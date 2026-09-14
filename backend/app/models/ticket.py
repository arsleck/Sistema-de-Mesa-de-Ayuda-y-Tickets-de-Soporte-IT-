from app import db
from datetime import datetime

class Ticket(db.Model):
    __tablename__ = 'tickets'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Abierto') 
    priority = db.Column(db.String(20), default='Media') 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Claves foráneas
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Relaciones para obtener los datos del usuario directamente desde la tabla 'users'
    creator = db.relationship('User', foreign_keys=[created_by_id])
    assignee = db.relationship('User', foreign_keys=[assigned_to_id])

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "created_by_id": self.created_by_id,
            "assigned_to_id": self.assigned_to_id,
            "created_at": self.created_at.isoformat(),
            # Esta línea extrae el nombre del creador gracias a la relación definida arriba
            "creator_username": self.creator.username if self.creator else None
        }