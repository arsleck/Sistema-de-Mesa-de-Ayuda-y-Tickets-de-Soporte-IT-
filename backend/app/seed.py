"""
Creación del administrador inicial.

El README indica que el admin "se configura mediante un proceso no visual".
Este módulo formaliza ese proceso: si existen ADMIN_USERNAME y ADMIN_PASSWORD
en el entorno, se crea el usuario admin la primera vez que arranca el backend.
"""
import os

import bcrypt

from app import db
from app.models.user import User


def seed_admin():
    username = os.getenv('ADMIN_USERNAME')
    password = os.getenv('ADMIN_PASSWORD')
    email = os.getenv('ADMIN_EMAIL', f'{username}@helpdesk.local' if username else None)

    if not username or not password:
        return  # No hay admin configurado: no se hace nada

    if User.query.filter_by(username=username).first():
        return  # Ya existe, no se duplica

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    db.session.add(User(username=username, email=email, password_hash=hashed, role='admin'))
    db.session.commit()
    print(f"[seed] Administrador '{username}' creado")
