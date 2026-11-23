"""
Demostración didáctica de SQL Injection (OWASP A03) — se ejecuta en una base
de datos SQLite EN MEMORIA, no toca la base real del proyecto.

Compara dos formas de buscar un usuario en el login:
  ANTES (vulnerable): el texto del usuario se pega dentro del SQL con un f-string.
  DESPUÉS (seguro):   consulta parametrizada, como hace SQLAlchemy en HelpDesk Pro.

Uso:  python security/demo_sqli.py
"""
import sqlite3

db = sqlite3.connect(':memory:')
db.execute("CREATE TABLE users (id INTEGER, username TEXT, password_hash TEXT, role TEXT)")
db.executemany("INSERT INTO users VALUES (?,?,?,?)", [
    (1, 'admin_soporte', '$2b$12$hash_secreto_admin', 'admin'),
    (2, 'ana', '$2b$12$hash_secreto_ana', 'employee'),
])

payload = "' OR '1'='1"
print(f"Usuario escrito por el atacante: {payload!r}\n")

# ---------------- ANTES: concatenación (NUNCA hacer esto)
sql = f"SELECT id, username, role FROM users WHERE username = '{payload}'"
print("🔴 VULNERABLE — SQL que llega a la base de datos:")
print("   " + sql)
print("   Filas devueltas:", db.execute(sql).fetchall(), "→ ¡devuelve TODOS los usuarios, incluido el admin!\n")

# ---------------- DESPUÉS: consulta parametrizada (lo que hace el ORM)
sql = "SELECT id, username, role FROM users WHERE username = ?"
print("🟢 SEGURO — SQL con parámetro (el payload viaja aparte, como dato):")
print("   " + sql + f"   parámetros = ({payload!r},)")
print("   Filas devueltas:", db.execute(sql, (payload,)).fetchall(), "→ ningún usuario se llama así\n")

print("En HelpDesk Pro todas las consultas usan SQLAlchemy, por ejemplo:")
print("   User.query.filter_by(username=data['username']).first()")
