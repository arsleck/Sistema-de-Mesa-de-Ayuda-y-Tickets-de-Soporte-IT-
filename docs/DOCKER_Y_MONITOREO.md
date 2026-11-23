# Contenerización y monitorización (Actividades 5 y 8)

## 1. Arquitectura con Docker Compose

```text
             Navegador
                 │  http://localhost:8080
        ┌────────▼────────┐
        │ frontend (Nginx)│  React compilado + proxy /api → backend
        └────────┬────────┘
                 │  http://backend:5000
        ┌────────▼────────┐  /metrics   ┌────────────┐      ┌─────────┐
        │ backend (Flask  │◄────────────│ Prometheus │◄─────│ Grafana │
        │ + Gunicorn)     │  cada 5 s   │   :9090    │      │  :3000  │
        └────────┬────────┘             └────────────┘      └─────────┘
                 │  SQLAlchemy
        ┌────────▼────────┐
        │ db (PostgreSQL) │  volumen pgdata (datos persistentes)
        └─────────────────┘
```

| Servicio | Imagen | Puerto | Para qué sirve |
|---|---|---|---|
| `db` | `postgres:16-alpine` | interno 5432 | Base de datos `mesa_ayuda_it` |
| `backend` | `backend/Dockerfile` | 5000 | API REST Flask servida con Gunicorn |
| `frontend` | `frontend/Dockerfile` | **8080** | React compilado + Nginx |
| `prometheus` | `prom/prometheus` | **9090** | Recolecta métricas cada 5 s y evalúa alertas |
| `grafana` | `grafana/grafana` | **3000** | Dashboard "HelpDesk Pro – Monitorización" |

## 2. Cómo levantarlo

```powershell
# Docker Desktop debe estar abierto
cd C:\proyectos\web2\Sistema-de-Mesa-de-Ayuda-y-Tickets-de-Soporte-IT
docker compose up -d --build
docker compose ps            # todos deben quedar "running" / "healthy"
```

| URL | Usuario |
|---|---|
| App: http://localhost:8080 | `admin_soporte` / `super_secreta_123` |
| Swagger: http://localhost:8080/api/docs | — |
| Prometheus: http://localhost:9090 (Status → Targets) | — |
| Grafana: http://localhost:3000 | `admin` / `admin` |

Para apagar: `docker compose down` (con `-v` también se borra la base de datos).

## 3. Los Dockerfile explicados

### `backend/Dockerfile`
| Instrucción | Por qué |
|---|---|
| `FROM python:3.12-slim` | Imagen base pequeña |
| `COPY requirements.txt` + `pip install` **antes** del código | Docker reutiliza la capa de dependencias si solo cambia el código: builds más rápidos |
| `COPY docs/openapi.yaml` | Swagger UI dentro del contenedor (por eso el *build context* es la raíz) |
| `USER appuser` | El proceso **no** corre como root (seguridad) |
| `HEALTHCHECK` → `/health` | Docker marca el contenedor como *unhealthy* si la API o la BD fallan |
| `CMD gunicorn ...` | Servidor de producción; se escala agregando réplicas |

### `frontend/Dockerfile` (multi-stage)
| Etapa | Qué hace |
|---|---|
| `node:22-alpine AS build` | `npm ci` + `npm run build` → carpeta `dist/` |
| `nginx:1.27-alpine` | Solo copia `dist/` y `nginx.conf`: imagen final sin Node (~50 MB) |

`nginx.conf` reenvía `/api` y `/health` al servicio `backend`, así navegador y API comparten dominio.

## 4. Variables de entorno

Se leen de un archivo `.env` en la raíz (ver `.env.example`). Si no existen, Compose usa los valores por defecto.

| Variable | Servicio | Descripción | Por defecto |
|---|---|---|---|
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | db, backend | Credenciales de PostgreSQL | `mesa_ayuda_it` / `helpdesk` / `helpdesk_pass` |
| `DATABASE_URL` | backend | Cadena de conexión SQLAlchemy (Compose la arma sola) | `postgresql://...@db:5432/...` |
| `JWT_SECRET_KEY` | backend | Clave para firmar los JWT (mínimo 32 caracteres) | **cambiar en producción** |
| `JWT_ACCESS_MINUTES` / `JWT_REFRESH_DAYS` | backend | Duración del access token y del refresh token | 30 / 7 |
| `CORS_ORIGINS` | backend | Orígenes permitidos (separados por coma) | `http://localhost:8080` |
| `TRUST_PROXY` | backend | `1` = leer la IP real desde Nginx (necesario para el límite de intentos) | `1` |
| `RATELIMIT_STORAGE_URI` | backend | Dónde guardar el conteo de intentos (`memory://` o `redis://...`) | `memory://` |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` / `ADMIN_EMAIL` | backend | Administrador creado al primer arranque | `admin_soporte` / ... |
| `VITE_API_URL` | frontend (build) | URL del API vista por el navegador; vacía = mismo dominio | `""` |
| `GRAFANA_USER` / `GRAFANA_PASSWORD` | grafana | Acceso a Grafana | `admin` / `admin` |

## 5. Monitorización y observabilidad

### Métricas que expone el backend en `/metrics`
| Métrica | Tipo | Significado |
|---|---|---|
| `flask_http_request_total` | Counter | Peticiones por método y código HTTP |
| `flask_http_request_duration_seconds` | Histogram | Latencia por endpoint (p50/p95/p99) |
| `helpdesk_tickets{status}` | Gauge | Tickets actuales por estado (consulta la BD) |
| `helpdesk_tickets_by_priority{priority}` | Gauge | Tickets por prioridad |
| `helpdesk_tickets_created_total{priority}` | Counter | Tickets creados |
| `helpdesk_login_attempts_total{result}` | Counter | Logins exitosos y fallidos |
| `up{job="helpdesk-backend"}` | — | 1 si Prometheus alcanza el backend (disponibilidad) |

Todas llevan la etiqueta `pod`, que identifica a cada réplica cuando se escala.

### Alertas (`monitoring/prometheus/alerts.yml`)
`BackendCaido`, `AltaTasaDeErrores` (>5 % de 5xx), `LatenciaAlta` (p95 > 500 ms), `MuchosTicketsAltaPrioridadAbiertos`.

### Logs estructurados
Cada petición genera una línea JSON: `docker compose logs -f backend`
```json
{"ts": "2026-11-23T13:55:22", "pod": "a1b2c3", "method": "POST", "path": "/api/tickets", "status": 201, "ms": 10.5, "ip": "172.18.0.1"}
```

### Dashboard de Grafana
Se carga solo al arrancar (*provisioning*). Tiene tres secciones:
1. **Disponibilidad:** backend arriba, réplicas activas, peticiones/s, latencia p95, % errores y tickets totales.
2. **Tráfico y rendimiento:** peticiones por endpoint, latencia p50/p95/p99, códigos HTTP (401/403/429 incluidos) y carga por réplica.
3. **Negocio:** tickets por estado y prioridad, logins exitosos vs. fallidos y tickets creados.

### Demostración en vivo
```powershell
python scripts\generar_carga.py --usuarios 15 --segundos 120
```
Con Grafana abierto se ve subir el tráfico, la latencia y los tickets en tiempo real.

Para demostrar **disponibilidad**: `docker compose stop backend` → la alerta `BackendCaido` se activa en Prometheus y el panel pasa a **CAÍDO**. Luego `docker compose start backend`.
