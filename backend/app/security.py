"""
Controles de seguridad transversales (OWASP Top 10).

Resumen de lo que hay en este archivo:
- limiter            -> limita intentos de login (fuerza bruta, OWASP A07)
- sanitize_text()    -> quita etiquetas HTML/JS de lo que escribe el usuario (XSS, OWASP A03)
- add_security_headers() -> cabeceras HTTP que le dicen al navegador cómo protegerse
- token_blocklist    -> tokens revocados al cerrar sesión (OAuth 2.1: revocación)

SQL Injection (A03) se previene usando SIEMPRE el ORM SQLAlchemy: los valores
viajan como parámetros y nunca se concatenan dentro del texto SQL.
CSRF se previene porque el JWT viaja en el header Authorization (no en cookies):
el navegador no lo envía solo, así que otra página no puede "usar" la sesión.
"""
import html
from datetime import datetime

import nh3
from flask import request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app import db

# Límite de peticiones por IP (se aplica con @limiter.limit en los endpoints sensibles)
limiter = Limiter(key_func=get_remote_address, storage_uri="memory://", default_limits=[])


def sanitize_text(value):
    """Elimina cualquier etiqueta HTML (<script>, <img onerror=...>, etc.) y deja solo el texto."""
    if value is None:
        return value
    text = str(value)
    # Se limpia dos veces: la segunda atrapa trucos como "&lt;script&gt;" codificado
    for _ in range(2):
        text = html.unescape(nh3.clean(text, tags=set()))
    return text.strip()


class TokenBlocklist(db.Model):
    """Tabla con los identificadores (jti) de tokens revocados en el logout."""
    __tablename__ = 'token_blocklist'

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def add_security_headers(response):
    """Cabeceras que endurecen el navegador frente a XSS, clickjacking y sniffing."""
    response.headers['X-Content-Type-Options'] = 'nosniff'       # no "adivinar" tipos de archivo
    response.headers['X-Frame-Options'] = 'DENY'                 # evita clickjacking (iframes)
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Cache-Control'] = 'no-store'               # no guardar datos sensibles en caché
    # Content-Security-Policy: la API solo devuelve JSON, así que no se permite ejecutar nada.
    # Swagger UI (/api/docs) necesita cargar sus scripts desde el CDN, por eso tiene su propia política.
    if request.path == '/api/docs':
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline' https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://unpkg.com; img-src 'self' data: https:")
    else:
        response.headers['Content-Security-Policy'] = "default-src 'none'; frame-ancestors 'none'"
    return response
