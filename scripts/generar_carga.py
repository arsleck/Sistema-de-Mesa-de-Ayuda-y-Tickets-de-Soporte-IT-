"""
Generador de carga para la DEMOSTRACIÓN de monitorización y escalabilidad.

Simula muchos usuarios usando la mesa de ayuda al mismo tiempo (login, listar,
crear y consultar tickets, métricas) para que las gráficas de Grafana se muevan
y, en Kubernetes, el autoescalado (HPA) cree más réplicas del backend.

Uso:
    python scripts/generar_carga.py                                  # Docker Compose (localhost:8080)
    python scripts/generar_carga.py --url http://localhost:5000 --usuarios 20 --segundos 120

Solo usa la librería "requests" (ya incluida en backend/requirements.txt).
"""
import argparse
import random
import threading
import time
import uuid

import requests

parser = argparse.ArgumentParser(description='Generador de carga HelpDesk Pro')
parser.add_argument('--url', default='http://localhost:8080', help='URL base de la aplicación')
parser.add_argument('--usuarios', type=int, default=10, help='Usuarios simultáneos (hilos)')
parser.add_argument('--segundos', type=int, default=60, help='Duración de la prueba')
args = parser.parse_args()

BASE = args.url.rstrip('/')
stats = {'ok': 0, 'error': 0}
lock = threading.Lock()
TITULOS = ['Impresora sin papel', 'VPN no conecta', 'Correo no sincroniza', 'Pantalla azul',
           'Sin acceso a carpeta compartida', 'Teclado no responde', 'Licencia de Office vencida']


def registrar(resultado):
    with lock:
        stats['ok' if resultado < 400 or resultado == 429 else 'error'] += 1


def obtener_token():
    """Un solo login para toda la prueba (el backend limita a 5 logins por minuto por IP)."""
    s = requests.Session()
    s.trust_env = False
    nombre = f'carga_{uuid.uuid4().hex[:8]}'
    s.post(f'{BASE}/api/auth/register', json={'username': nombre, 'email': f'{nombre}@demo.com',
                                             'password': 'Clave_Carga_1'})
    r = s.post(f'{BASE}/api/auth/login', json={'username': nombre, 'password': 'Clave_Carga_1'})
    r.raise_for_status()
    return r.json()['access_token']


def usuario_virtual(fin, token):
    s = requests.Session()
    s.trust_env = False
    s.headers['Authorization'] = f'Bearer {token}'

    while time.time() < fin:
        accion = random.random()
        if accion < 0.45:
            r = s.get(f'{BASE}/api/tickets')                              # listar
        elif accion < 0.65:
            r = s.post(f'{BASE}/api/tickets', json={                       # crear
                'title': random.choice(TITULOS), 'description': 'Generado por la prueba de carga',
                'priority': random.choice(['Baja', 'Media', 'Alta'])})
        elif accion < 0.85:
            r = s.get(f'{BASE}/api/tickets/stats')                         # dashboard
        else:
            r = s.get(f'{BASE}/health')                                    # monitoreo
        registrar(r.status_code)
        time.sleep(random.uniform(0.05, 0.3))


if __name__ == '__main__':
    print(f'Generando carga contra {BASE} con {args.usuarios} usuarios durante {args.segundos} s...')
    token = obtener_token()
    fin = time.time() + args.segundos
    hilos = [threading.Thread(target=usuario_virtual, args=(fin, token), daemon=True) for _ in range(args.usuarios)]
    for h in hilos:
        h.start()
    while any(h.is_alive() for h in hilos):
        time.sleep(5)
        print(f"  peticiones OK: {stats['ok']:>6} | errores: {stats['error']:>4}")
    print('Listo. Revisa Grafana: http://localhost:3000')
