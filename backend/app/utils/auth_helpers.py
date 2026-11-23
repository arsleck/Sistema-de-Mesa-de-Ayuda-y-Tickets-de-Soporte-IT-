"""
Utilidades de autorización (RBAC: control de acceso basado en roles).

El decorador @roles_required se coloca encima de un endpoint para que solo
ciertos roles puedan usarlo. Así la seguridad no depende de que el frontend
"esconda" botones: el backend es quien decide.
"""
from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app import db
from app.models.user import User

STAFF_ROLES = ('admin', 'agent')  # Técnicos y administradores


def get_current_user():
    """Devuelve el usuario dueño del token JWT de la petición actual."""
    user_id = get_jwt_identity()
    return db.session.get(User, int(user_id)) if user_id else None


def roles_required(*roles):
    """Permite el acceso solo a los roles indicados; si no, responde 403."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()  # 1) Debe venir un JWT válido
            user = get_current_user()
            if not user or user.role not in roles:  # 2) Y el rol debe estar permitido
                return jsonify({"error": "No tienes permisos para realizar esta acción"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
