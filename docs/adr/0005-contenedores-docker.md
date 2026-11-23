# ADR 0005: Contenedores Docker: Gunicorn para la API y Nginx para el frontend

**Estado:** Aceptada · **Actividad del curso:** A5

## Contexto
Se necesita que el sistema completo (BD, API, web, monitoreo) arranque igual en cualquier PC, en CI y en la nube.

## Opciones evaluadas
| Opción | Evaluación |
|---|---|
| Instalación manual (venv + npm + PostgreSQL local) | Cada máquina queda distinta: «en mi PC sí funciona». |
| Máquinas virtuales | Aisladas pero pesadas y lentas de crear. |
| Contenedores Docker + Compose | Ligeros, reproducibles y la misma imagen llega a Kubernetes y Azure. |

## Decisión
Dockerfile por servicio (frontend multi-stage con Nginx; backend con Gunicorn, usuario no root y healthcheck) y docker-compose para el entorno local.

## Consecuencias
- La imagen del frontend no incluye Node (≈50 MB).
- Nginx actúa como reverse proxy: un único dominio, sin problemas de CORS.
- La URL del backend es configurable (BACKEND_URL) para Docker, Kubernetes o Azure.
