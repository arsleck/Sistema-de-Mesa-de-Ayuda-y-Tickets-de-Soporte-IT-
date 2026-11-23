# ADR 0006: Observabilidad con Prometheus + Grafana y métricas de negocio

**Estado:** Aceptada · **Actividad del curso:** A8

## Contexto
Una mesa de ayuda no se evalúa solo por CPU: importa cuántos tickets hay abiertos, cuántos son de prioridad Alta y si el servicio responde rápido.

## Opciones evaluadas
| Opción | Evaluación |
|---|---|
| Revisar logs manualmente | No da tendencias ni alertas. |
| Servicio SaaS (Datadog, New Relic) | Potente pero de pago y externo. |
| Prometheus (modelo pull) + Grafana | Estándar abierto, nativo en Kubernetes, descubre réplicas automáticamente. |

## Decisión
Endpoint /metrics con métricas técnicas (peticiones, latencia, códigos HTTP) y de negocio (tickets por estado/prioridad, logins); 4 reglas de alerta; dashboard aprovisionado como código; logs en JSON.

## Consecuencias
- Cada réplica se mide por separado (etiqueta pod), lo que hace visible el autoescalado.
- El dashboard y las alertas se versionan en Git (monitoring/).
- Los logs JSON se integran con Log Analytics en Azure.
