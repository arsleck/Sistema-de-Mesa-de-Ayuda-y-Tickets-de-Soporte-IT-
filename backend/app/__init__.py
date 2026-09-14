import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')

    db.init_app(app)
    CORS(app)
    JWTManager(app)

    with app.app_context():
        from app.models.user import User
        from app.models.ticket import Ticket

        from app.routes.auth import auth_bp
        from app.routes.tickets import tickets_bp

        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        app.register_blueprint(tickets_bp, url_prefix='/api/tickets')

        db.create_all()

    return app