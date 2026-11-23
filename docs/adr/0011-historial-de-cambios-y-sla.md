# ADR 0011: Historial de cambios (auditoría) y métricas de SLA

**Estado:** Aceptada · **Actividad del curso:** A2, A8

## Contexto
Una mesa de ayuda se evalúa por su **acuerdo de nivel de servicio (SLA)**: cuánto tarda en resolver y si atiende a tiempo lo urgente. Además, para auditoría se necesita saber quién cambió el estado o la asignación de cada ticket. El README original listaba "Historial de cambios" y "Tiempo promedio de resolución" como funcionalidades pendientes.

## Opciones evaluadas
| Opción | Evaluación |
|---|---|
| Agregar columnas `resolved_at`, `updated_by` a `tickets` | Solo guarda el último cambio y obliga a migrar la tabla existente. |
| Tabla `ticket_history` (un registro por cambio) | Auditoría completa; la tabla nueva se crea sola sin tocar las existentes. |
| Calcular el SLA solo en SQL | Útil para el dashboard de la app, pero sin tendencias ni alertas. |
| Histograma en Prometheus + alertas | Tendencias en Grafana, percentiles y alertas automáticas. |

## Decisión
- Tabla `ticket_history` (ORM) que registra creación, estado, prioridad, técnico asignado y ediciones, con usuario y fecha. Endpoint `GET /api/tickets/<id>/history`.
- Métrica `helpdesk_ticket_resolution_seconds` (histograma con cortes de 15 min a 3 días) y `helpdesk_high_priority_unassigned`.
- Alertas `SLAAltaPrioridadSinAsignar` y `SLAResolucionLenta`; fila "SLA" en Grafana; aviso en el frontend para el staff.

## Consecuencias
- Cada decisión sobre un ticket es trazable (útil ante reclamos de usuarios).
- El SLA se observa en dos niveles: en la app (`/stats`) y en Grafana (tendencias y alertas).
- El historial se elimina junto con el ticket (cascada del ORM).
