"""
Fábrica de la aplicación Flask (patrón "Application Factory").

Aquí se arma todo el backend: se carga la configuración desde variables de
entorno, se conectan las extensiones (base de datos, JWT, CORS) y se registran
los grupos de rutas (blueprints). Usar una fábrica permite crear una app
"de pruebas" con SQLite en memoria sin tocar PostgreSQL.
"""
import os
from datetime import timedelta

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

load_dotenv()

# Objeto ORM compartido por todos los modelos (SQLAlchemy)
db = SQLAlchemy()
jwt = JWTManager()


def create_app(test_config=None):
    app = Flask(__name__)

    # --- Configuración leída desde el entorno (.env, Docker o Kubernetes) ---
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL', 'sqlite:///helpdesk_local.db'  # respaldo para desarrollo rápido
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'clave-de-desarrollo-cambiar-en-produccion-2026')
    app.config['JSON_SORT_KEYS'] = False

    # Tokens de vida corta + token de renovación (modelo OAuth 2.1: access + refresh)
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=int(os.getenv('JWT_ACCESS_MINUTES', 30)))
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=int(os.getenv('JWT_REFRESH_DAYS', 7)))
    app.config['RATELIMIT_ENABLED'] = os.getenv('RATELIMIT_ENABLED', '1') == '1'
    # Dónde se guardan los contadores del límite de intentos (memory:// o redis://...)
    app.config['RATELIMIT_STORAGE_URI'] = os.getenv('RATELIMIT_STORAGE_URI', 'memory://')

    # Permite que las pruebas automáticas sobrescriban la configuración
    if test_config:
        app.config.update(test_config)

    # Detrás de Nginx/Kubernetes: usar la IP real del cliente (cabecera X-Forwarded-For),
    # si no, el límite de intentos bloquearía a todos los usuarios a la vez
    if os.getenv('TRUST_PROXY', '0') == '1':
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    # --- Extensiones ---
    db.init_app(app)
    jwt.init_app(app)

    from app.security import limiter, add_security_headers, TokenBlocklist
    limiter.init_app(app)                       # límite de intentos (fuerza bruta)
    app.after_request(add_security_headers)     # cabeceras de seguridad en cada respuesta

    @jwt.token_in_blocklist_loader
    def is_token_revoked(jwt_header, jwt_payload):
        # Un token revocado en el logout deja de servir aunque no haya expirado
        return db.session.query(TokenBlocklist.id).filter_by(jti=jwt_payload['jti']).first() is not None

    # CORS: solo los orígenes del frontend definidos pueden consumir la API
    allowed_origins = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',')
    # expose_headers: permite que el Centro de verificación (frontend) lea las cabeceras de seguridad
    security_headers = ['Content-Security-Policy', 'X-Frame-Options', 'X-Content-Type-Options', 'Referrer-Policy']
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}, r"/health": {"origins": "*"}},
         expose_headers=security_headers)

    with app.app_context():
        # Se importan los modelos para que SQLAlchemy cree sus tablas
        from app.models.user import User  # noqa: F401
        from app.models.ticket import Ticket  # noqa: F401

        from app.routes.health import health_bp
        from app.routes.auth import auth_bp
        from app.routes.tickets import tickets_bp
        from app.routes.docs import docs_bp

        # Registro de los grupos de endpoints
        app.register_blueprint(health_bp)                       # /health
        app.register_blueprint(auth_bp, url_prefix='/api/auth')  # login, registro, usuarios
        app.register_blueprint(tickets_bp, url_prefix='/api/tickets')  # CRUD de tickets
        app.register_blueprint(docs_bp)                          # /api/docs (Swagger UI)

        db.create_all()

        # Crea el administrador inicial si viene definido en el entorno
        from app.seed import seed_admin
        seed_admin()

    # Observabilidad: /metrics para Prometheus + logs en formato JSON
    from app.metrics import init_metrics
    init_metrics(app)

    register_error_handlers(app)
    return app


def register_error_handlers(app):
    """Respuestas de error siempre en JSON (nunca páginas HTML de Flask)."""

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Solicitud inválida"}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Recurso no encontrado"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Método no permitido"}), 405

    @app.errorhandler(429)
    def too_many_requests(e):
        return jsonify({"error": "Demasiados intentos. Espera un momento e inténtalo de nuevo."}), 429

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Error interno del servidor"}), 500
