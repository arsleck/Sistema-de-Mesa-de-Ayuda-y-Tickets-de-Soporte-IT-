"""
Monitoreo del servicio (health check).

Lo usan Docker, Kubernetes (liveness/readiness) y el pipeline CI/CD para saber
si la API está viva y si puede hablar con la base de datos.
"""
from datetime import datetime

from flask import Blueprint, jsonify
from sqlalchemy import text

from app import db

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    # Se hace una consulta mínima para comprobar la conexión con la base de datos
    try:
        db.session.execute(text('SELECT 1'))
        database = "ok"
    except Exception:
        database = "error"

    status_code = 200 if database == "ok" else 503
    return jsonify({
        "status": "ok" if database == "ok" else "degraded",
        "message": "API de la Mesa de Ayuda funcionando correctamente",
        "database": database,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }), status_code
