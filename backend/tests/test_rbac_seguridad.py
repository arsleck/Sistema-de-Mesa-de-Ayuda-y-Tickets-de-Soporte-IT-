"""
Pruebas de AUTORIZACIÓN (RBAC) y SEGURIDAD (Actividad 3 – OWASP Top 10 2023).
"""
from app import db
from tests.conftest import login


def _crear_ticket(client, headers_dict, title='Ticket privado'):
    r = client.post('/api/tickets', json={'title': title, 'description': 'detalle'}, headers=headers_dict)
    return r.get_json()['ticket']['id']


# ------------------------------------------------------------------ A01 Control de acceso (RBAC)
def test_empleado_solo_ve_sus_propios_tickets(client, headers):
    _crear_ticket(client, headers('otro'))
    mio = _crear_ticket(client, headers('empleado'), 'Mío')
    visibles = client.get('/api/tickets', headers=headers('empleado')).get_json()
    assert [t['id'] for t in visibles] == [mio]


def test_empleado_no_puede_ver_detalle_de_ticket_ajeno(client, headers):
    ajeno = _crear_ticket(client, headers('otro'))
    assert client.get(f'/api/tickets/{ajeno}', headers=headers('empleado')).status_code == 403


def test_empleado_no_puede_cambiar_estado_ni_eliminar(client, headers):
    emp = headers('empleado')
    propio = _crear_ticket(client, emp)
    assert client.put(f'/api/tickets/{propio}', json={'status': 'Resuelto'}, headers=emp).status_code == 403
    assert client.delete(f'/api/tickets/{propio}', headers=emp).status_code == 403


def test_empleado_puede_editar_su_ticket_solo_si_esta_abierto(client, headers):
    emp = headers('empleado')
    propio = _crear_ticket(client, emp)
    assert client.put(f'/api/tickets/{propio}', json={'title': 'Corregido'}, headers=emp).status_code == 200
    client.put(f'/api/tickets/{propio}', json={'status': 'En Progreso'}, headers=headers('tecnico'))
    assert client.put(f'/api/tickets/{propio}', json={'title': 'Otra vez'}, headers=emp).status_code == 409


def test_solo_admin_crea_tecnicos(client, headers):
    datos = {'username': 'tec2', 'email': 'tec2@test.com', 'password': 'Clave_123'}
    assert client.post('/api/auth/admin/register', json=datos, headers=headers('tecnico')).status_code == 403
    assert client.post('/api/auth/admin/register', json=datos, headers=headers('admin')).status_code == 201


def test_no_se_puede_asignar_un_ticket_a_un_empleado(client, headers):
    adm = headers('admin')
    tid = _crear_ticket(client, adm)
    empleado_id = next(u['id'] for u in client.get('/api/auth/users', headers=adm).get_json()
                       if u['username'] == 'empleado')
    r = client.put(f'/api/tickets/{tid}', json={'assigned_to_id': empleado_id}, headers=adm)
    assert r.status_code == 400


# ------------------------------------------------------------------ A03 Inyección
def test_sql_injection_en_login_no_permite_entrar(client):
    r = client.post('/api/auth/login', json={'username': "' OR '1'='1' --", 'password': "' OR '1'='1"})
    assert r.status_code == 401


def test_sql_injection_en_busqueda_no_altera_la_consulta(client, headers):
    _crear_ticket(client, headers('otro'))
    r = client.get("/api/tickets?q=' OR 1=1 --", headers=headers('empleado'))
    assert r.status_code == 200 and r.get_json() == []


def test_xss_se_elimina_antes_de_guardar(client, headers):
    payload = '<script>alert("XSS")</script><img src=x onerror=alert(1)>Monitor sin señal'
    r = client.post('/api/tickets', json={'title': payload, 'description': payload}, headers=headers('empleado'))
    ticket = r.get_json()['ticket']
    assert ticket['title'] == 'Monitor sin señal'
    assert '<' not in ticket['description']


# ------------------------------------------------------------------ CSRF / CORS y cabeceras
def test_cors_no_autoriza_origenes_externos(client):
    r = client.options('/api/tickets', headers={'Origin': 'http://sitio-malicioso.com',
                                                'Access-Control-Request-Method': 'POST'})
    assert r.headers.get('Access-Control-Allow-Origin') is None


def test_cabeceras_de_seguridad_presentes(client):
    r = client.get('/health')
    for cabecera in ('X-Content-Type-Options', 'X-Frame-Options', 'Content-Security-Policy', 'Referrer-Policy'):
        assert cabecera in r.headers


# ------------------------------------------------------------------ A07 Autenticación
def test_refresh_token_entrega_nuevo_access_token(client):
    refresh = login(client, 'empleado')['refresh_token']
    r = client.post('/api/auth/refresh', headers={'Authorization': f'Bearer {refresh}'})
    assert r.status_code == 200
    assert client.get('/api/auth/me', headers={'Authorization': f"Bearer {r.get_json()['access_token']}"}).status_code == 200


def test_logout_revoca_el_token(client, headers):
    h = headers('empleado')
    assert client.post('/api/auth/logout', headers=h).status_code == 200
    assert client.get('/api/auth/me', headers=h).status_code == 401


def test_fuerza_bruta_bloqueada_con_429():
    # Se crea una app aparte con el limitador ENCENDIDO (en las demás pruebas está apagado)
    from app import create_app
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite://', 'RATELIMIT_ENABLED': True,
                      'JWT_SECRET_KEY': 'clave-solo-para-pruebas-automaticas-0123456789'})
    client = app.test_client()
    codigos = [client.post('/api/auth/login', json={'username': 'admin', 'password': f'mala{i}'}).status_code
               for i in range(7)]
    assert codigos[:5] == [401] * 5   # los 5 primeros intentos se evalúan normalmente
    assert codigos[5:] == [429, 429]  # a partir del sexto, bloqueado


def test_contrasenas_guardadas_con_bcrypt(app):
    from app.models.user import User
    usuario = db.session.query(User).filter_by(username='admin').first()
    assert usuario.password_hash.startswith('$2b$')  # nunca texto plano
