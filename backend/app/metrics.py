"""
Observabilidad: métricas para Prometheus y logs estructurados (Actividad 8).

- GET /metrics expone métricas en el formato que Prometheus "raspa" (scrape) cada 5-15 s.
- Métricas automáticas (prometheus-flask-exporter): peticiones por endpoint, código
  HTTP y tiempo de respuesta (latencia).
- Métricas de negocio propias: tickets por estado/prioridad, tickets creados, logins.
- Cada petición deja una línea de log en JSON (fácil de buscar y analizar).
"""
import json
import logging
import os
import socket
import time

from flask import g, request
from prometheus_client import Counter, Histogram
from prometheus_client.core import GaugeMetricFamily, REGISTRY
from prometheus_flask_exporter import PrometheusMetrics

# ---------------------------------------------------------------- Contadores de negocio
TICKETS_CREATED = Counter('helpdesk_tickets_created_total', 'Tickets creados', ['priority'])
LOGIN_ATTEMPTS = Counter('helpdesk_login_attempts_total', 'Intentos de inicio de sesión', ['result'])

# SLA: cuánto tarda un ticket desde que se crea hasta que se marca "Resuelto".
# Los "buckets" son los cortes del SLA: 15 min, 1 h, 4 h, 8 h, 1 día, 3 días.
RESOLUTION_TIME = Histogram(
    'helpdesk_ticket_resolution_seconds', 'Tiempo de resolución de tickets (SLA)', ['priority'],
    buckets=(60, 900, 3600, 4 * 3600, 8 * 3600, 24 * 3600, 72 * 3600))

POD_NAME = os.getenv('HOSTNAME', socket.gethostname())  # en Kubernetes = nombre del pod


class TicketStatsCollector:
    """Cada vez que Prometheus consulta /metrics, cuenta los tickets actuales en la BD."""

    def __init__(self, app):
        self.app = app

    def collect(self):
        from app import db
        from app.models.ticket import Ticket, VALID_PRIORITIES, VALID_STATUSES
        from sqlalchemy import func

        by_status = GaugeMetricFamily('helpdesk_tickets', 'Tickets actuales por estado', labels=['status'])
        by_priority = GaugeMetricFamily('helpdesk_tickets_by_priority', 'Tickets por prioridad', labels=['priority'])
        # SLA: incidencias urgentes que nadie ha tomado todavía (dispara una alerta en Prometheus)
        urgent_unassigned = GaugeMetricFamily('helpdesk_high_priority_unassigned',
                                              'Tickets de prioridad Alta, sin resolver y sin técnico asignado')
        urgent = 0
        try:
            with self.app.app_context():
                # Se parte de 0 para cada estado/prioridad: así Grafana muestra 0 y no "No data"
                status_counts = {s: 0 for s in VALID_STATUSES}
                status_counts.update(dict(db.session.query(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status).all()))
                priority_counts = {p: 0 for p in VALID_PRIORITIES}
                priority_counts.update(dict(db.session.query(Ticket.priority, func.count(Ticket.id)).group_by(Ticket.priority).all()))
                urgent = Ticket.query.filter(Ticket.priority == 'Alta', Ticket.status != 'Resuelto',
                                             Ticket.assigned_to_id.is_(None)).count()
                db.session.remove()
            for status, n in status_counts.items():
                by_status.add_metric([status], n)
            for prio, n in priority_counts.items():
                by_priority.add_metric([prio], n)
        except Exception:
            pass  # si la BD no responde, /metrics sigue funcionando
        urgent_unassigned.add_metric([], urgent)
        yield by_status
        yield by_priority
        yield urgent_unassigned


_collector_registered = False


def init_metrics(app):
    """Activa /metrics y el log estructurado. Se llama desde create_app()."""
    global _collector_registered
    if app.config.get('TESTING') and app.config.get('METRICS_DISABLED', True):
        return  # en las pruebas automáticas no se registran métricas globales

    metrics = PrometheusMetrics(app, group_by='url_rule', default_labels={'pod': POD_NAME})
    metrics.info('helpdesk_app_info', 'Información de la aplicación', version='2.0.0')

    if not _collector_registered:
        REGISTRY.register(TicketStatsCollector(app))
        _collector_registered = True

    _init_structured_logging(app)


def _init_structured_logging(app):
    logger = logging.getLogger('helpdesk')
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    @app.before_request
    def _start_timer():
        g._t0 = time.perf_counter()

    @app.after_request
    def _log_request(response):
        if request.path != '/metrics':  # no llenar el log con los scrapes de Prometheus
            logger.info(json.dumps({
                'ts': time.strftime('%Y-%m-%dT%H:%M:%S'),
                'pod': POD_NAME,
                'method': request.method,
                'path': request.path,
                'status': response.status_code,
                'ms': round((time.perf_counter() - g.get('_t0', time.perf_counter())) * 1000, 1),
                'ip': request.headers.get('X-Forwarded-For', request.remote_addr),
            }, ensure_ascii=False))
        return response
