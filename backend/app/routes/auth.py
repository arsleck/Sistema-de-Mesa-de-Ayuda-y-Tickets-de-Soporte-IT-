"""
Endpoints de autenticación y usuarios  (prefijo /api/auth)

- POST /register        -> registro público (siempre crea 'employee')
- POST /admin/register  -> solo el admin crea técnicos ('agent')
- POST /login           -> valida credenciales y entrega el JWT
- GET  /me              -> datos del usuario dueño del token
- GET  /agents          -> técnicos disponibles para asignar (solo staff)
- GET  /users           -> listado de usuarios (solo admin)
"""
from flask import Blueprint, request, jsonify
from app import db
from app.models.user import User
import bcrypt
from flask_jwt_extended import create_access_token, jwt_required

from app.utils.auth_helpers import get_current_user, roles_required, STAFF_ROLES

auth_bp = Blueprint('auth', __name__)


def _hash_password(password):
    """Bcrypt agrega una 'sal' aleatoria: dos contraseñas iguales generan hashes distintos."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def _validate_user_payload(data):
    """Revisa que lleguen los campos obligatorios y con un formato razonable."""
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return "Faltan datos obligatorios"
    if len(data['username']) > 80 or len(data['email']) > 120:
        return "Usuario o correo demasiado largo"
    if '@' not in data['email']:
        return "Correo electrónico inválido"
    if len(data['password']) < 6:
        return "La contraseña debe tener al menos 6 caracteres"
    return None


def _user_exists(data):
    return (User.query.filter_by(username=data['username']).first()
            or User.query.filter_by(email=data['email']).first())


# 1. REGISTRO PÚBLICO (Solo crea empleados normales)
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True)
    error = _validate_user_payload(data)
    if error:
        return jsonify({"error": error}), 400

    if _user_exists(data):
        return jsonify({"error": "El usuario o correo ya existe"}), 409

    # Seguridad: Forzamos el rol a employee sin importar qué envíe el frontend
    new_user = User(
        username=data['username'],
        email=data['email'],
        password_hash=_hash_password(data['password']),
        role='employee'
    )

    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "Usuario registrado exitosamente"}), 201


# 2. REGISTRO PRIVADO (Solo el Admin puede crear Técnicos)
@auth_bp.route('/admin/register', methods=['POST'])
@roles_required('admin')
def register_agent():
    data = request.get_json(silent=True)
    error = _validate_user_payload(data)
    if error:
        return jsonify({"error": error}), 400

    if _user_exists(data):
        return jsonify({"error": "El usuario o correo ya existe"}), 409

    new_agent = User(
        username=data['username'],
        email=data['email'],
        password_hash=_hash_password(data['password']),
        role='agent'  # Se crea explícitamente como técnico
    )

    db.session.add(new_agent)
    db.session.commit()
    return jsonify({"message": "Técnico creado exitosamente", "user": new_agent.to_dict()}), 201


# 3. LOGIN (Devuelve el token y el rol)
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True)
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "Faltan credenciales"}), 400

    # El ORM arma la consulta con parámetros: un texto como "' OR 1=1 --" se trata como dato, no como SQL
    user = User.query.filter_by(username=data['username']).first()

    if not user or not bcrypt.checkpw(data['password'].encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({"error": "Credenciales inválidas"}), 401

    # El "identity" del token es el id del usuario; el rol viaja como dato adicional
    access_token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})

    return jsonify({
        "message": "Inicio de sesión exitoso",
        "access_token": access_token,
        "username": user.username,
        "role": user.role  # Enviamos el rol al frontend
    }), 200


# 4. PERFIL DEL USUARIO AUTENTICADO
@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(user.to_dict()), 200


# 5. LISTA DE AGENTES (Para asignación) — ahora protegida: solo staff
@auth_bp.route('/agents', methods=['GET'])
@roles_required(*STAFF_ROLES)
def get_agents():
    agents = User.query.filter(User.role.in_(STAFF_ROLES)).all()
    agent_list = [{"id": agent.id, "username": agent.username} for agent in agents]
    return jsonify(agent_list), 200


# 6. LISTA DE USUARIOS (Panel administrativo)
@auth_bp.route('/users', methods=['GET'])
@roles_required('admin')
def get_users():
    users = User.query.order_by(User.id).all()
    return jsonify([u.to_dict() for u in users]), 200
