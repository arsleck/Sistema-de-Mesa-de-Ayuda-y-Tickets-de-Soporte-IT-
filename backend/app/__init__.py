"""
Fábrica de la aplicación Flask (patrón "Application Factory").

Aquí se arma todo el backend: se carga la configuración desde variables de
entorno, se conectan las extensiones (base de datos, JWT, CORS) y se registran
los grupos de rutas (blueprints). Usar una fábrica permite crear una app
"de pruebas" con SQLite en memoria sin tocar PostgreSQL.
"""
import os

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

    # Permite que las pruebas automáticas sobrescriban la configuración
    if test_config:
        app.config.update(test_config)

    # --- Extensiones ---
    db.init_app(app)
    jwt.init_app(app)

    # CORS: solo los orígenes del frontend definidos pueden consumir la API
    allowed_origins = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',')
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}, r"/health": {"origins": "*"}})

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

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Error interno del servidor"}), 500
