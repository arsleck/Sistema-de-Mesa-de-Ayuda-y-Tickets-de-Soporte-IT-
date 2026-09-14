from flask import Flask

def create_app():
    app = Flask(__name__)

    # Importar los Blueprints
    from app.routes.health import health_bp
    from app.routes.auth import auth_bp
    from app.routes.tickets import tickets_bp

    # Registrar los Blueprints en la aplicación
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(tickets_bp, url_prefix='/api/tickets')

    return app