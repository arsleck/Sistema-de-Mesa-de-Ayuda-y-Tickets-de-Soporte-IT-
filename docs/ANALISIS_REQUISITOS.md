# Análisis de requisitos del curso vs. estado del proyecto

**Proyecto:** HelpDesk Pro – Sistema de Mesa de Ayuda y Tickets de Soporte IT
**Asignatura:** Ingeniería Web II
**Fecha del análisis:** 23/11/2026
**Punto de partida:** commit `db8f541` — *feat: initial HelpDesk Pro implementation* (único commit, solo rama `main`)

Leyenda: ✅ implementado · 🟡 parcial · ❌ no implementado

---

## 1. Estado inicial (antes de las mejoras)

### M1 · Programación Full-Stack del lado del servidor y seguridad web

| Actividad | Requisito | Estado inicial | Observación |
|---|---|:---:|---|
| A1 – Backend | API REST con 5 endpoints CRUD | 🟡 | Había POST, GET (lista), PUT y DELETE. Faltaba GET por id. |
| A1 | Documentación OpenAPI 3.0 | 🟡 | `docs/openapi.yaml` solo documentaba `/health` y `GET /api/tickets`. |
| A1 | Colección Postman | ❌ | Solo existía `test_api.py` (script manual). |
| A1 | Pull Request en GitHub | ❌ | Un único commit directo a `main`. |
| A2 – Integración | Frontend React consumiendo la API | ✅ | React + Vite + Axios con interceptor JWT. |
| A2 | Manejo de estados | ✅ | `useState` / `useEffect` en las páginas. |
| A2 | Persistencia con ORM | ✅ | SQLAlchemy + PostgreSQL. |
| A2 | Mínimo 3 pruebas de integración + reporte | ❌ | No había pruebas automatizadas. |
| A3 – Seguridad | Autenticación JWT | ✅ | Flask-JWT-Extended + Bcrypt. |
| A3 | OAuth 2.1 (refresh / expiración) | ❌ | Token único sin renovación. |
| A3 | Mitigación SQLi | 🟡 | El ORM la previene, pero sin evidencia antes/después. |
| A3 | Mitigación XSS | 🟡 | React escapa HTML, pero el backend guardaba cualquier contenido y no enviaba cabeceras de seguridad. |
| A3 | Mitigación CSRF | 🟡 | El JWT viaja en el header (no en cookie), pero no estaba documentado ni probado. |
| A3 | Evidencia de pruebas antes/después | ❌ | — |
| A4 – Pruebas y docs | Swagger UI / Postman | ❌ | — |

### M2 · Servicios en la nube, DevOps y despliegue

| Actividad | Requisito | Estado inicial |
|---|---|:---:|
| A5 | Dockerfile backend/frontend + Docker Compose (con BD) | ❌ |
| A6 | Kubernetes local (Minikube): pods, servicios, deployments | ❌ |
| A6 | GitFlow con mínimo 10 commits documentados | ❌ |
| A7 | CI/CD con GitHub Actions (build + test + deploy) | ❌ |
| A7 | Terraform (IaC) — en inglés | ❌ |
| A8 | Prometheus + Grafana (monitorización y escalabilidad) | ❌ |
| A8 | Despliegue en la nube (AWS/GCP/Azure) | ❌ |

### Fallas detectadas en el código original

| # | Falla | Riesgo |
|---|---|---|
| 1 | `/health` no estaba registrado (vivía en `routes/__init__.py`, que nunca se ejecuta) → respondía 404. | Monitoreo y probes de K8s imposibles. |
| 2 | `PUT /api/tickets/<id>` no validaba rol: un empleado podía cambiar estados o asignarse técnicos por API. | **OWASP A01 – Broken Access Control** |
| 3 | `DELETE /api/tickets/<id>` permitía borrar a cualquier usuario autenticado. | **OWASP A01** |
| 4 | `GET /api/tickets` devolvía los tickets de todos los usuarios a cualquier empleado. | Exposición de información |
| 5 | `GET /api/auth/agents` era público (sin token). | Enumeración de usuarios |
| 6 | No se validaban `status`, `priority` ni `assigned_to_id` (se podía asignar a un empleado). | Integridad de datos |
| 7 | `requirements.txt` y `.gitignore` estaban en UTF-16. | Rompe Docker / CI en Linux |
| 8 | `JWT_SECRET_KEY` sin valor por defecto; `debug=True` fijo en `run.py`. | Configuración insegura |

---

## 2. Plan de implementación (GitFlow)

| Fase | Rama `feature/*` | Cubre |
|---|---|---|
| 1 | `feature/api-rest-rbac` | A1, A4 — CRUD completo, RBAC, OpenAPI 3.0, Swagger UI, Postman |
| 2 | `feature/seguridad-owasp` | A3 — refresh tokens, rate limit, cabeceras, SQLi/XSS/CSRF con evidencia |
| 3 | `feature/pruebas-verificacion` | A2, A4 — pruebas de integración, reporte HTML, Centro de verificación visual |
| 4 | `feature/docker-monitoreo` | A5, A8 — Docker Compose, Prometheus, Grafana |
| 5 | `feature/k8s-cicd-terraform` | A6, A7, A8 — Minikube, HPA, GitHub Actions, Terraform (Azure) |
| 6 | `release/2.0.0` | Documentación final y guion de demostración |

El estado final de cada requisito se actualiza en la sección 3 al cierre de cada fase.

---

## 3. Estado actual

| Requisito | Estado | Evidencia |
|---|:---:|---|
| CRUD completo (6 endpoints de tickets + 6 de auth/usuarios) | ✅ | `backend/app/routes/tickets.py`, `auth.py` |
| RBAC en el backend | ✅ | `backend/app/utils/auth_helpers.py` (`@roles_required`) |
| OpenAPI 3.0 completo | ✅ | `docs/openapi.yaml` |
| Swagger UI | ✅ | `http://127.0.0.1:5000/api/docs` |
| Colección Postman con tests | ✅ | `docs/postman/HelpDesk_Pro.postman_collection.json` (22 peticiones, 27 aserciones) |
| `/health` con chequeo de BD | ✅ | `http://127.0.0.1:5000/health` |
| JWT con modelo OAuth 2.1 (refresh + revocación) | ✅ | `/api/auth/refresh`, `/api/auth/logout`, tabla `token_blocklist` |
| SQLi, XSS y CSRF mitigados con evidencia antes/después | ✅ | `docs/seguridad/` — 2/14 → 14/14 controles |
| Límite de intentos y cabeceras de seguridad | ✅ | `backend/app/security.py` |
| Mínimo 3 pruebas de integración + reporte | ✅ | `backend/tests/` (25 pruebas) → `backend/reports/reporte_pruebas.html` |
| Verificación visual de requisitos | ✅ | Frontend `/verificacion` — `docs/PRUEBAS.md` |
| Dockerfile backend/frontend + Docker Compose con BD | ✅ | `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml` |
| Documentación de Dockerfile y variables de entorno | ✅ | `docs/DOCKER_Y_MONITOREO.md` |
| Prometheus + Grafana (métricas, alertas, dashboard) | ✅ | `monitoring/`, endpoint `/metrics`, logs JSON |
