"""
Pruebas del HISTORIAL de cambios (auditoría) y de las métricas de SLA.
"""


def _crear(client, h, prioridad='Alta'):
    return client.post('/api/tickets', json={'title': 'Servidor caído', 'description': 'No responde',
                                             'priority': prioridad}, headers=h).get_json()['ticket']['id']


def test_historial_registra_quien_cambio_que_y_cuando(client, headers):
    adm = headers('admin')
    tid = _crear(client, headers('empleado'))
    tecnico = next(a['id'] for a in client.get('/api/auth/agents', headers=adm).get_json() if a['username'] == 'tecnico')
    client.put(f'/api/tickets/{tid}', json={'assigned_to_id': tecnico, 'status': 'En Progreso'}, headers=adm)
    client.put(f'/api/tickets/{tid}', json={'status': 'Resuelto'}, headers=headers('tecnico'))

    historial = client.get(f'/api/tickets/{tid}/history', headers=headers('empleado')).get_json()
    cambios = [(h['field'], h['old_value'], h['new_value'], h['user']) for h in historial]
    assert cambios == [
        ('creado', None, 'Alta · Abierto', 'empleado'),
        ('status', 'Abierto', 'En Progreso', 'admin'),
        ('assigned_to', None, 'tecnico', 'admin'),
        ('status', 'En Progreso', 'Resuelto', 'tecnico'),
    ]


def test_historial_no_registra_cambios_sin_efecto(client, headers):
    adm = headers('admin')
    tid = _crear(client, adm)
    client.put(f'/api/tickets/{tid}', json={'status': 'Abierto'}, headers=adm)   # mismo estado
    assert len(client.get(f'/api/tickets/{tid}/history', headers=adm).get_json()) == 1


def test_historial_de_ticket_ajeno_es_privado(client, headers):
    tid = _crear(client, headers('otro'))
    assert client.get(f'/api/tickets/{tid}/history', headers=headers('empleado')).status_code == 403


def test_historial_se_elimina_con_el_ticket(app, client, headers):
    from app import db
    from app.models.history import TicketHistory
    adm = headers('admin')
    tid = _crear(client, adm)
    client.delete(f'/api/tickets/{tid}', headers=adm)
    assert db.session.query(TicketHistory).filter_by(ticket_id=tid).count() == 0


def test_stats_incluye_indicadores_de_sla(client, headers):
    adm = headers('admin')
    urgente = _crear(client, adm, 'Alta')
    _crear(client, adm, 'Baja')
    stats = client.get('/api/tickets/stats', headers=adm).get_json()
    assert stats['high_priority_unassigned'] == 1
    assert stats['avg_resolution_minutes'] is None          # aún no hay tickets resueltos

    client.put(f'/api/tickets/{urgente}', json={'status': 'Resuelto'}, headers=adm)
    stats = client.get('/api/tickets/stats', headers=adm).get_json()
    assert stats['high_priority_unassigned'] == 0
    assert stats['avg_resolution_minutes'] is not None and stats['avg_resolution_minutes'] >= 0
