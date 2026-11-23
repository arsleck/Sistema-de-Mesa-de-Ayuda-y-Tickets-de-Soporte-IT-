"""
Configuración compartida de las pruebas (fixtures de pytest).

Cada prueba recibe una aplicación NUEVA con una base de datos SQLite en memoria:
así las pruebas no dependen de PostgreSQL y no ensucian datos reales.
Se crean tres usuarios de ejemplo, uno por cada rol del sistema.
"""
import os
import sys

import bcrypt
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db  # noqa: E402
from app.models.user import User  # noqa: E402

PASSWORD = 'Clave_Prueba_123'


@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite://',   # base de datos en memoria
        'JWT_SECRET_KEY': 'clave-solo-para-pruebas-automaticas-0123456789',
        'RATELIMIT_ENABLED': False,               # se activa solo en la prueba de fuerza bruta
    })
    with app.app_context():
        hashed = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt(rounds=4)).decode()
        db.session.add_all([
            User(username='admin', email='admin@test.com', password_hash=hashed, role='admin'),
            User(username='tecnico', email='tecnico@test.com', password_hash=hashed, role='agent'),
            User(username='empleado', email='empleado@test.com', password_hash=hashed, role='employee'),
            User(username='otro', email='otro@test.com', password_hash=hashed, role='employee'),
        ])
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, username):
    """Inicia sesión y devuelve el cuerpo completo de la respuesta (tokens y rol)."""
    return client.post('/api/auth/login', json={'username': username, 'password': PASSWORD}).get_json()


@pytest.fixture
def headers(client):
    """Devuelve una función: headers('admin') -> {'Authorization': 'Bearer ...'}"""
    def _headers(username):
        return {'Authorization': f"Bearer {login(client, username)['access_token']}"}
    return _headers
