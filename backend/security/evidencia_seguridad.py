"""
Evidencia de seguridad ANTES / DESPUÉS (OWASP Top 10 2023).

Ejecuta ataques controlados contra la API que esté corriendo y muestra una tabla
con el resultado de cada prueba:  🟢 PROTEGIDO  /  🔴 VULNERABLE

Uso (con el backend encendido):
    python security/evidencia_seguridad.py                      # contra http://127.0.0.1:5000
    python security/evidencia_seguridad.py http://localhost:8080
    python security/evidencia_seguridad.py http://127.0.0.1:5000 --md resultado.md

Para la evidencia "antes": hacer checkout del commit original (db8f541), levantar
el backend y correr este mismo script. Luego repetir sobre la versión nueva.
No necesita usuario administrador: crea sus propios usuarios de prueba.
"""
import sys
import time
import uuid

import requests

BASE = next((a for a in sys.argv[1:] if a.startswith('http')), 'http://127.0.0.1:5000').rstrip('/')
MD_OUT = sys.argv[sys.argv.index('--md') + 1] if '--md' in sys.argv else None
API = f'{BASE}/api'
S = requests.Session()
S.trust_env = False  # no usar proxies del sistema para localhost

results = []  # (categoria OWASP, prueba, protegido: bool, detalle)


def check(owasp, name, protected, detail):
    results.append((owasp, name, protected, detail))
    icon = '🟢 PROTEGIDO ' if protected else '🔴 VULNERABLE'
    print(f'{icon} | {owasp:<22} | {name:<52} | {detail}')


def new_user(prefix):
    """Registra un empleado nuevo y devuelve su token."""
    name = f'{prefix}_{uuid.uuid4().hex[:6]}'
    pwd = 'Clave_Prueba_123'
    S.post(f'{API}/auth/register', json={'username': name, 'email': f'{name}@demo.com', 'password': pwd})
    r = S.post(f'{API}/auth/login', json={'username': name, 'password': pwd})
    return name, r.json().get('access_token'), r.json()


def auth(token):
    return {'Authorization': f'Bearer {token}'}


print(f'\nObjetivo: {BASE}\n' + '-' * 120)

# Dos empleados: la "víctima" crea un ticket y el "atacante" intenta abusar de él
victim, t_victim, _ = new_user('victima')
attacker, t_attacker, login_body = new_user('atacante')
r = S.post(f'{API}/tickets', json={'title': 'Ticket privado de la víctima', 'description': 'Datos internos'},
           headers=auth(t_victim))
victim_ticket = r.json()['ticket']['id']

# ---------------------------------------------------------------- A03 Injection: SQL
r = S.post(f'{API}/auth/login', json={'username': "' OR '1'='1' --", 'password': "' OR '1'='1' --"})
check('A03 SQL Injection', "Login con payload ' OR '1'='1' --", r.status_code != 200,
      f'HTTP {r.status_code} (200 = entró sin contraseña)')

r = S.get(f'{API}/tickets', params={'q': "' OR 1=1 --"}, headers=auth(t_attacker))
leaked = [t for t in r.json() if t.get('id') == victim_ticket] if r.ok else []
check('A03 SQLi + A01', "Búsqueda ?q=' OR 1=1 -- no expone tickets ajenos", not leaked,
      f'{len(leaked)} ticket(s) de la víctima expuestos')

# ---------------------------------------------------------------- A03 Injection: XSS
payload = '<script>alert("XSS")</script><img src=x onerror=alert(1)>Impresora dañada'
r = S.post(f'{API}/tickets', json={'title': payload, 'description': payload}, headers=auth(t_attacker))
stored = r.json().get('ticket', {}).get('title', '')
check('A03 XSS almacenado', 'El HTML/JS malicioso se elimina antes de guardar',
      '<script' not in stored and 'onerror' not in stored, f'Guardado: {stored[:45]!r}')

r = S.get(f'{BASE}/health')
csp = r.headers.get('Content-Security-Policy')
check('A03 XSS (navegador)', 'Cabecera Content-Security-Policy presente', bool(csp), csp or 'sin CSP')

# ---------------------------------------------------------------- CSRF
r = S.options(f'{API}/tickets', headers={'Origin': 'http://sitio-malicioso.com',
                                         'Access-Control-Request-Method': 'POST'})
acao = r.headers.get('Access-Control-Allow-Origin')
check('CSRF / CORS', 'Un sitio externo NO es autorizado por CORS', acao not in ('*', 'http://sitio-malicioso.com'),
      f'Access-Control-Allow-Origin: {acao}')

r = S.post(f'{API}/tickets', json={'title': 'csrf', 'description': 'csrf'},
           headers={'Cookie': f'access_token={t_attacker}', 'Origin': 'http://sitio-malicioso.com'})
check('CSRF', 'Sin header Authorization la sesión no se usa (cookie ignorada)', r.status_code == 401,
      f'HTTP {r.status_code}')

# ---------------------------------------------------------------- A01 Broken Access Control
r = S.get(f'{API}/tickets', headers=auth(t_attacker))
leaked = [t for t in r.json() if t['id'] == victim_ticket] if r.ok else []
check('A01 Control de acceso', 'Empleado NO ve tickets de otros empleados', not leaked,
      f'{len(r.json()) if r.ok else 0} tickets visibles, {len(leaked)} ajenos')

r = S.put(f'{API}/tickets/{victim_ticket}', json={'status': 'Resuelto'}, headers=auth(t_attacker))
check('A01 Control de acceso', 'Empleado NO cambia el estado de un ticket ajeno', r.status_code == 403,
      f'HTTP {r.status_code}')

r = S.delete(f'{API}/tickets/{victim_ticket}', headers=auth(t_attacker))
check('A01 Control de acceso', 'Empleado NO elimina un ticket ajeno', r.status_code == 403,
      f'HTTP {r.status_code}')

r = S.get(f'{API}/auth/agents')
check('A01 Control de acceso', 'Lista de técnicos requiere autenticación', r.status_code == 401,
      f'HTTP {r.status_code}')

# ---------------------------------------------------------------- A07 Fallas de autenticación
codes = [S.post(f'{API}/auth/login', json={'username': victim, 'password': f'mala{i}'}).status_code
         for i in range(7)]
check('A07 Autenticación', 'Fuerza bruta bloqueada (HTTP 429 tras 5 intentos)', 429 in codes,
      f'Códigos: {codes}')

check('A07 Autenticación', 'Login entrega refresh token (sesión renovable)', 'refresh_token' in login_body,
      'refresh_token presente' if 'refresh_token' in login_body else 'solo access_token')

r = S.post(f'{API}/auth/logout', headers=auth(t_attacker))
after = S.get(f'{API}/tickets', headers=auth(t_attacker))
check('A07 Autenticación', 'Logout revoca el token en el servidor', after.status_code == 401,
      f'logout HTTP {r.status_code}; reuso del token HTTP {after.status_code}')

# ---------------------------------------------------------------- A05 Configuración insegura
r = S.get(f'{BASE}/health')
needed = ['X-Content-Type-Options', 'X-Frame-Options', 'Referrer-Policy']
missing = [h for h in needed if h not in r.headers]
check('A05 Configuración', 'Cabeceras de seguridad HTTP', not missing,
      'todas presentes' if not missing else f'faltan: {", ".join(missing)}')

# ---------------------------------------------------------------- Resumen
ok = sum(1 for *_, p, _ in results if p)
print('-' * 120 + f'\nResultado: {ok}/{len(results)} controles protegidos\n')

if MD_OUT:
    with open(MD_OUT, 'w', encoding='utf-8') as f:
        f.write(f'Objetivo: `{BASE}` — {time.strftime("%Y-%m-%d %H:%M")}\n\n')
        f.write('| OWASP | Prueba | Resultado | Detalle |\n|---|---|:---:|---|\n')
        for owasp, name, p, detail in results:
            f.write(f'| {owasp} | {name} | {"🟢 Protegido" if p else "🔴 Vulnerable"} | {detail} |\n')
        f.write(f'\n**{ok}/{len(results)} controles protegidos**\n')
