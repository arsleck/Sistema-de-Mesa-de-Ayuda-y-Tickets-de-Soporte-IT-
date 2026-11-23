"""
Pruebas de INTEGRACIÓN de la API (Actividad 2 y 4).

Cada prueba recorre el flujo completo: petición HTTP -> Flask -> JWT/RBAC ->
SQLAlchemy -> base de datos -> respuesta JSON, igual que lo haría el frontend.
"""
from tests.conftest import login


# ------------------------------------------------------------------ Monitoreo
def test_health_reporta_api_y_base_de_datos(client):
    r = client.get('/health')
    assert r.status_code == 200
    assert r.get_json()['status'] == 'ok'
    assert r.get_json()['database'] == 'ok'


def test_documentacion_swagger_disponible(client):
    assert client.get('/api/docs').status_code == 200
    spec = client.get('/api/openapi.yaml')
    assert spec.status_code == 200
    assert b'openapi: 3.0' in spec.data


# ------------------------------------------------------------------ Autenticación
def test_registro_publico_siempre_crea_employee(client):
    # Aunque el cliente intente registrarse como admin, el backend lo fuerza a employee
    r = client.post('/api/auth/register', json={
        'username': 'nuevo', 'email': 'nuevo@test.com', 'password': 'Clave_123', 'role': 'admin'})
    assert r.status_code == 201
    assert login_role(client, 'nuevo', 'Clave_123') == 'employee'


def login_role(client, user, pwd):
    return client.post('/api/auth/login', json={'username': user, 'password': pwd}).get_json()['role']


def test_login_devuelve_access_y_refresh_token(client):
    body = login(client, 'admin')
    assert body['access_token'] and body['refresh_token']
    assert body['role'] == 'admin'


def test_login_con_contrasena_incorrecta_responde_401(client):
    r = client.post('/api/auth/login', json={'username': 'admin', 'password': 'incorrecta'})
    assert r.status_code == 401


def test_endpoint_protegido_sin_token_responde_401(client):
    assert client.get('/api/tickets').status_code == 401


# ------------------------------------------------------------------ Flujo completo de un ticket
def test_flujo_completo_ticket_crear_asignar_resolver_eliminar(client, headers):
    """Simula el ciclo de vida real de una incidencia de punta a punta."""
    emp, adm = headers('empleado'), headers('admin')

    # 1. El empleado reporta la incidencia
    r = client.post('/api/tickets', json={'title': 'VPN no conecta', 'description': 'Error 809',
                                          'priority': 'Alta'}, headers=emp)
    assert r.status_code == 201
    ticket = r.get_json()['ticket']
    assert ticket['status'] == 'Abierto' and ticket['creator_username'] == 'empleado'

    # 2. El admin lo asigna al técnico y lo pasa a "En Progreso"
    tecnico_id = next(a['id'] for a in client.get('/api/auth/agents', headers=adm).get_json()
                      if a['username'] == 'tecnico')
    r = client.put(f"/api/tickets/{ticket['id']}", json={'assigned_to_id': tecnico_id,
                                                         'status': 'En Progreso'}, headers=adm)
    assert r.status_code == 200
    assert r.get_json()['ticket']['assignee_username'] == 'tecnico'

    # 3. El técnico lo resuelve
    r = client.put(f"/api/tickets/{ticket['id']}", json={'status': 'Resuelto'}, headers=headers('tecnico'))
    assert r.get_json()['ticket']['status'] == 'Resuelto'

    # 4. El empleado consulta y ve el estado actualizado (persistido en la BD)
    assert client.get(f"/api/tickets/{ticket['id']}", headers=emp).get_json()['status'] == 'Resuelto'

    # 5. El admin lo elimina y ya no existe
    assert client.delete(f"/api/tickets/{ticket['id']}", headers=adm).status_code == 200
    assert client.get(f"/api/tickets/{ticket['id']}", headers=adm).status_code == 404


def test_filtros_y_busqueda_de_tickets(client, headers):
    adm = headers('admin')
    client.post('/api/tickets', json={'title': 'Impresora atascada', 'description': 'Piso 3',
                                      'priority': 'Baja'}, headers=adm)
    client.post('/api/tickets', json={'title': 'Correo caído', 'description': 'Outlook',
                                      'priority': 'Alta'}, headers=adm)

    assert len(client.get('/api/tickets?priority=Alta', headers=adm).get_json()) == 1
    resultado = client.get('/api/tickets?q=impresora', headers=adm).get_json()
    assert [t['title'] for t in resultado] == ['Impresora atascada']


def test_metricas_del_dashboard(client, headers):
    adm = headers('admin')
    for prioridad in ('Alta', 'Alta', 'Media'):
        client.post('/api/tickets', json={'title': 't', 'description': 'd', 'priority': prioridad}, headers=adm)
    stats = client.get('/api/tickets/stats', headers=adm).get_json()
    assert stats['total'] == 3
    assert stats['by_priority'] == {'Baja': 0, 'Media': 1, 'Alta': 2}
    assert stats['by_status']['Abierto'] == 3
    assert stats['unassigned'] == 3


def test_validaciones_de_datos(client, headers):
    emp = headers('empleado')
    assert client.post('/api/tickets', json={'title': 'x'}, headers=emp).status_code == 400
    assert client.post('/api/tickets', json={'title': 'x', 'description': 'y', 'priority': 'Urgente'},
                       headers=emp).status_code == 400
    assert client.post('/api/tickets', json={'title': 'x' * 150, 'description': 'y'},
                       headers=emp).status_code == 400
