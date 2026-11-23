# ADR 0001: Arquitectura desacoplada: SPA en React + API REST en Flask

**Estado:** Aceptada · **Actividad del curso:** A1, A2

## Contexto
El sistema debe atender a empleados, técnicos y administradores desde el navegador, y la misma lógica debe poder consumirse desde otras herramientas (Postman, scripts, futuras apps móviles).

## Opciones evaluadas
| Opción | Evaluación |
|---|---|
| Aplicación monolítica con plantillas del servidor (Jinja/Django templates) | Más simple, pero acopla interfaz y lógica; no expone una API reutilizable. |
| SPA React + API REST JSON | Separa responsabilidades; la API se documenta con OpenAPI y se prueba de forma independiente. |

## Decisión
Frontend React + Vite (SPA) y backend Flask exponiendo una API REST documentada con OpenAPI 3.0.

## Consecuencias
- El frontend y el backend se despliegan y escalan por separado (2 Deployments en Kubernetes).
- Se necesita CORS o un proxy (Nginx) para servir ambos bajo el mismo dominio.
- Flask es ligero y permite agregar solo lo necesario (JWT, limiter, métricas) como extensiones.
