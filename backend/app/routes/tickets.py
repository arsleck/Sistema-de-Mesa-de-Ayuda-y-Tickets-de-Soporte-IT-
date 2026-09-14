from flask import Blueprint, request, jsonify
from app import db
from app.models.ticket import Ticket
from flask_jwt_extended import jwt_required, get_jwt_identity

tickets_bp = Blueprint('tickets', __name__)

@tickets_bp.route('/', methods=['POST'], strict_slashes=False)
@jwt_required()
def create_ticket():
    current_user_id = get_jwt_identity() # Ahora esto será un string simple con el ID
    data = request.get_json()

    if not data or not data.get('title') or not data.get('description'):
        return jsonify({"error": "Faltan datos obligatorios (title, description)"}), 400

    new_ticket = Ticket(
        title=data['title'],
        description=data['description'],
        priority=data.get('priority', 'Media'),
        created_by_id=int(current_user_id) # Convertimos el string a entero para la base de datos
    )

    db.session.add(new_ticket)
    db.session.commit()

    return jsonify({"message": "Ticket creado exitosamente", "ticket": new_ticket.to_dict()}), 201

from app.models.user import User

@tickets_bp.route('/', methods=['GET'], strict_slashes=False)
@jwt_required()
def get_tickets():
    tickets = Ticket.query.all()
    return jsonify([ticket.to_dict() for ticket in tickets]), 200

# Actualizar el estado o la asignación de un ticket
@tickets_bp.route('/<int:id>', methods=['PUT'], strict_slashes=False)
@jwt_required()
def update_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    data = request.get_json()

    if 'status' in data:
        ticket.status = data['status']
        
    # NUEVO: Si llega un agente asignado, lo actualizamos
    if 'assigned_to_id' in data:
        # Si envían una cadena vacía o nula, lo dejamos sin asignar (None)
        ticket.assigned_to_id = data['assigned_to_id'] if data['assigned_to_id'] else None

    db.session.commit()
    
    return jsonify({
        "message": "Ticket actualizado exitosamente", 
        "ticket": ticket.to_dict()
    }), 200

# Eliminar un ticket de la base de datos
@tickets_bp.route('/<int:id>', methods=['DELETE'], strict_slashes=False)
@jwt_required()
def delete_ticket(id):
    # Busca el ticket por su ID; si no existe, devuelve un error 404
    ticket = Ticket.query.get_or_404(id)
    
    db.session.delete(ticket)
    db.session.commit()
    
    return jsonify({"message": "Ticket eliminado exitosamente"}), 200