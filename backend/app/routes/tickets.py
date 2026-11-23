"""
Endpoints CRUD de tickets  (prefijo /api/tickets)

| Método | Ruta          | Quién puede                                  |
|--------|---------------|----------------------------------------------|
| POST   | /             | Cualquier usuario autenticado                |
| GET    | /             | Employee: solo los suyos · Staff: todos      |
| GET    | /<id>         | El creador del ticket o el staff             |
| PUT    | /<id>         | Staff: estado/asignación/prioridad           |
|        |               | Creador: asunto/detalle mientras esté Abierto|
| DELETE | /<id>         | Solo staff (admin y agent)                   |
| GET    | /stats        | Métricas para el dashboard                   |
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func, or_

from app import db
from app.models.ticket import Ticket, VALID_PRIORITIES, VALID_STATUSES
from app.models.user import User
from app.utils.auth_helpers import get_current_user, roles_required, STAFF_ROLES

tickets_bp = Blueprint('tickets', __name__)


def _is_staff(user):
    return user is not None and user.role in STAFF_ROLES


def _can_view(user, ticket):
    """Un empleado solo puede ver los tickets que él mismo creó."""
    return _is_staff(user) or ticket.created_by_id == user.id


# ---------------------------------------------------------------- CREATE
@tickets_bp.route('/', methods=['POST'], strict_slashes=False)
@jwt_required()
def create_ticket():
    user = get_current_user()
    data = request.get_json(silent=True)

    if not data or not data.get('title') or not data.get('description'):
        return jsonify({"error": "Faltan datos obligatorios (title, description)"}), 400

    priority = data.get('priority', 'Media')
    if priority not in VALID_PRIORITIES:
        return jsonify({"error": f"Prioridad inválida. Usa: {', '.join(VALID_PRIORITIES)}"}), 400
    if len(data['title']) > 100:
        return jsonify({"error": "El asunto no puede superar 100 caracteres"}), 400

    new_ticket = Ticket(
        title=data['title'].strip(),
        description=data['description'].strip(),
        priority=priority,
        created_by_id=user.id  # El creador siempre es el dueño del token, nunca lo envía el cliente
    )

    db.session.add(new_ticket)
    db.session.commit()

    return jsonify({"message": "Ticket creado exitosamente", "ticket": new_ticket.to_dict()}), 201


# ---------------------------------------------------------------- READ (lista)
@tickets_bp.route('/', methods=['GET'], strict_slashes=False)
@jwt_required()
def get_tickets():
    user = get_current_user()
    query = Ticket.query

    # RBAC: el empleado solo ve sus propios tickets
    if not _is_staff(user):
        query = query.filter(Ticket.created_by_id == user.id)

    # Filtros opcionales por query string: ?status=Abierto&priority=Alta&q=impresora
    status = request.args.get('status')
    priority = request.args.get('priority')
    search = request.args.get('q')
    if status:
        query = query.filter(Ticket.status == status)
    if priority:
        query = query.filter(Ticket.priority == priority)
    if search:
        like = f"%{search}%"  # SQLAlchemy lo envía como parámetro, no lo concatena al SQL
        query = query.filter(or_(Ticket.title.ilike(like), Ticket.description.ilike(like)))

    tickets = query.order_by(Ticket.created_at.desc()).all()
    return jsonify([ticket.to_dict() for ticket in tickets]), 200


# ---------------------------------------------------------------- MÉTRICAS DASHBOARD
@tickets_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    user = get_current_user()
    base = Ticket.query if _is_staff(user) else Ticket.query.filter(Ticket.created_by_id == user.id)

    by_status = {s: 0 for s in VALID_STATUSES}
    for status, count in base.with_entities(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status):
        by_status[status] = count

    by_priority = {p: 0 for p in VALID_PRIORITIES}
    for priority, count in base.with_entities(Ticket.priority, func.count(Ticket.id)).group_by(Ticket.priority):
        by_priority[priority] = count

    # Carga de trabajo por técnico (solo tiene sentido para el staff)
    by_agent = []
    if _is_staff(user):
        rows = (db.session.query(User.username, func.count(Ticket.id))
                .join(Ticket, Ticket.assigned_to_id == User.id)
                .group_by(User.username).all())
        by_agent = [{"agent": name, "count": count} for name, count in rows]

    return jsonify({
        "total": sum(by_status.values()),
        "by_status": by_status,
        "by_priority": by_priority,
        "by_agent": by_agent,
        "unassigned": base.filter(Ticket.assigned_to_id.is_(None)).count(),
    }), 200


# ---------------------------------------------------------------- READ (detalle)
@tickets_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_ticket(id):
    user = get_current_user()
    ticket = db.get_or_404(Ticket, id)
    if not _can_view(user, ticket):
        return jsonify({"error": "No tienes permisos para ver este ticket"}), 403
    return jsonify(ticket.to_dict()), 200


# ---------------------------------------------------------------- UPDATE
@tickets_bp.route('/<int:id>', methods=['PUT'], strict_slashes=False)
@jwt_required()
def update_ticket(id):
    user = get_current_user()
    ticket = db.get_or_404(Ticket, id)
    data = request.get_json(silent=True) or {}

    staff_fields = {'status', 'assigned_to_id'}
    owner_fields = {'title', 'description'}

    # Un empleado NO puede cambiar estado ni asignar técnicos (antes sí podía vía API)
    if not _is_staff(user):
        if ticket.created_by_id != user.id:
            return jsonify({"error": "No tienes permisos sobre este ticket"}), 403
        if staff_fields & data.keys():
            return jsonify({"error": "Solo técnicos o administradores pueden cambiar estado o asignación"}), 403
        if ticket.status != 'Abierto':
            return jsonify({"error": "Solo se pueden editar tickets en estado Abierto"}), 409

    if 'status' in data:
        if data['status'] not in VALID_STATUSES:
            return jsonify({"error": f"Estado inválido. Usa: {', '.join(VALID_STATUSES)}"}), 400
        ticket.status = data['status']

    if 'priority' in data:
        if data['priority'] not in VALID_PRIORITIES:
            return jsonify({"error": f"Prioridad inválida. Usa: {', '.join(VALID_PRIORITIES)}"}), 400
        ticket.priority = data['priority']

    # Asignación de técnico: debe existir y tener rol de staff
    if 'assigned_to_id' in data:
        agent_id = data['assigned_to_id']
        if agent_id in (None, '', 0):
            ticket.assigned_to_id = None
        else:
            agent = db.session.get(User, int(agent_id))
            if not agent or agent.role not in STAFF_ROLES:
                return jsonify({"error": "El usuario asignado no es un técnico válido"}), 400
            ticket.assigned_to_id = agent.id

    for field in owner_fields:
        if field in data and data[field]:
            if field == 'title' and len(data[field]) > 100:
                return jsonify({"error": "El asunto no puede superar 100 caracteres"}), 400
            setattr(ticket, field, data[field].strip())

    db.session.commit()

    return jsonify({
        "message": "Ticket actualizado exitosamente",
        "ticket": ticket.to_dict()
    }), 200


# ---------------------------------------------------------------- DELETE
@tickets_bp.route('/<int:id>', methods=['DELETE'], strict_slashes=False)
@roles_required(*STAFF_ROLES)  # Antes cualquier usuario autenticado podía borrar
def delete_ticket(id):
    # Busca el ticket por su ID; si no existe, devuelve un error 404
    ticket = db.get_or_404(Ticket, id)

    db.session.delete(ticket)
    db.session.commit()

    return jsonify({"message": "Ticket eliminado exitosamente"}), 200
