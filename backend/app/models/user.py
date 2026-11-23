from app import db

VALID_ROLES = ('admin', 'agent', 'employee')


class User(db.Model):
    """Tabla 'users': empleados, técnicos (agent) y administradores."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)  # nunca se guarda la contraseña en texto plano
    role = db.Column(db.String(20), nullable=False, default='employee')  # roles: admin, agent, employee

    def to_dict(self):
        """Datos públicos del usuario (sin el hash de la contraseña)."""
        return {"id": self.id, "username": self.username, "email": self.email, "role": self.role}

    def __repr__(self):
        return f'<User {self.username}>'
