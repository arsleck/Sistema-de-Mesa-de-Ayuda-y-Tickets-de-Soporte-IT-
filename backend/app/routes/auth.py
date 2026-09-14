from flask import Blueprint, request, jsonify
from app import db
from app.models.user import User
import bcrypt
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

auth_bp = Blueprint('auth', __name__)

# 1. REGISTRO PÚBLICO (Solo crea empleados normales)
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Faltan datos obligatorios"}), 400

    if User.query.filter_by(username=data['username']).first() or User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "El usuario o correo ya existe"}), 409

    hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Seguridad: Forzamos el rol a employee sin importar qué envíe el frontend
    new_user = User(
        username=data['username'],
        email=data['email'],
        password_hash=hashed_password,
        role='employee' 
    )

    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "Usuario registrado exitosamente"}), 201

# 2. REGISTRO PRIVADO (Solo el Admin puede crear Técnicos)
@auth_bp.route('/admin/register', methods=['POST'])
@jwt_required()
def register_agent():
    current_user_id = get_jwt_identity()
    admin_user = User.query.get(current_user_id)
    
    if not admin_user or admin_user.role != 'admin':
        return jsonify({"error": "Acceso denegado. Solo los administradores pueden crear técnicos."}), 403

    data = request.get_json()
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Faltan datos obligatorios"}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "El usuario ya existe"}), 409

    hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    new_agent = User(
        username=data['username'],
        email=data['email'],
        password_hash=hashed_password,
        role='agent' # Se crea explícitamente como técnico
    )

    db.session.add(new_agent)
    db.session.commit()
    return jsonify({"message": "Técnico creado exitosamente"}), 201

# 3. LOGIN (Devuelve el rol)
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "Faltan credenciales"}), 400

    user = User.query.filter_by(username=data['username']).first()

    if not user or not bcrypt.checkpw(data['password'].encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({"error": "Credenciales inválidas"}), 401

    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        "message": "Inicio de sesión exitoso",
        "access_token": access_token,
        "username": user.username,
        "role": user.role # Enviamos el rol al frontend
    }), 200

# 4. LISTA DE AGENTES (Para asignación)
@auth_bp.route('/agents', methods=['GET'])
def get_agents():
    agents = User.query.filter(User.role.in_(['admin', 'agent'])).all()
    agent_list = [{"id": agent.id, "username": agent.username} for agent in agents]
    return jsonify(agent_list), 200