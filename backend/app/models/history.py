from datetime import datetime

from app import db


class TicketHistory(db.Model):
    """
    Tabla 'ticket_history': AUDITORÍA de cada cambio de un ticket.
    Guarda quién cambió qué campo, el valor anterior, el nuevo y cuándo.
    Con estos registros se calcula además el tiempo de resolución (SLA).
    """
    __tablename__ = 'ticket_history'

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    field = db.Column(db.String(30), nullable=False)      # creado, status, priority, assigned_to, title, description
    old_value = db.Column(db.String(120), nullable=True)
    new_value = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship('User')

    def to_dict(self):
        return {
            "id": self.id,
            "field": self.field,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "user": self.user.username if self.user else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
