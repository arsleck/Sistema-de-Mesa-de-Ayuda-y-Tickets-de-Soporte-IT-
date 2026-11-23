# ADR 0002: PostgreSQL con SQLAlchemy ORM

**Estado:** Aceptada · **Actividad del curso:** A2, A3

## Contexto
Los tickets tienen relaciones (creador, técnico asignado) y requieren integridad referencial y consultas por estado/prioridad.

## Opciones evaluadas
| Opción | Evaluación |
|---|---|
| SQLite | Sin servidor, pero no soporta bien concurrencia de varias réplicas. |
| MongoDB | Flexible, pero las relaciones usuario–ticket son naturalmente relacionales. |
| PostgreSQL + ORM | Relacional, robusto, disponible como servicio gestionado en Azure. |

## Decisión
PostgreSQL como motor y SQLAlchemy como ORM. Las pruebas usan SQLite en memoria a través del mismo ORM.

## Consecuencias
- Las consultas se parametrizan siempre: mitiga SQL Injection (OWASP A03) sin esfuerzo extra.
- El mismo código funciona con SQLite (pruebas), PostgreSQL local, Docker y Azure.
- Cambios de esquema requieren migraciones (pendiente: Flask-Migrate/Alembic).
