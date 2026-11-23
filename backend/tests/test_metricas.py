"""
Prueba de observabilidad (Actividad 8): el endpoint /metrics expone métricas
técnicas (peticiones, latencia) y de negocio (tickets, logins) para Prometheus.
"""
from app import create_app


def test_endpoint_metrics_para_prometheus():
    app = create_app({'TESTING': True, 'METRICS_DISABLED': False, 'RATELIMIT_ENABLED': False,
                      'SQLALCHEMY_DATABASE_URI': 'sqlite://',
                      'JWT_SECRET_KEY': 'clave-solo-para-pruebas-automaticas-0123456789'})
    client = app.test_client()
    client.post('/api/auth/register', json={'username': 'm', 'email': 'm@test.com', 'password': 'Clave_123'})
    token = client.post('/api/auth/login', json={'username': 'm', 'password': 'Clave_123'}).get_json()['access_token']
    client.post('/api/tickets', json={'title': 'a', 'description': 'b', 'priority': 'Alta'},
                headers={'Authorization': f'Bearer {token}'})
    # El usuario es employee y no puede resolver: se promueve a admin para la prueba de SLA
    from app import db
    from app.models.user import User
    with app.app_context():
        db.session.query(User).filter_by(username='m').update({'role': 'admin'})
        db.session.commit()
    client.put('/api/tickets/1', json={'status': 'Resuelto'}, headers={'Authorization': f'Bearer {token}'})

    body = client.get('/metrics').get_data(as_text=True)
    assert 'flask_http_request_duration_seconds' in body          # latencia por endpoint
    assert 'helpdesk_login_attempts_total{result="success"}' in body
    assert 'helpdesk_tickets_created_total{priority="Alta"}' in body
    assert 'helpdesk_tickets{status="Resuelto"} 1.0' in body      # leído de la base de datos
    assert 'helpdesk_ticket_resolution_seconds_count{priority="Alta"}' in body   # SLA (histograma)
    assert 'helpdesk_high_priority_unassigned 0.0' in body
