# ADR 0007: Redis para compartir el límite de intentos entre réplicas

**Estado:** Aceptada · **Actividad del curso:** A3, A6, A8

## Contexto
El límite de 5 logins por minuto se guardaba en la memoria de cada proceso. Con 2–6 réplicas, un atacante podría hacer 5 intentos por réplica, multiplicando el límite.

## Opciones evaluadas
| Opción | Evaluación |
|---|---|
| Mantener memory:// | Correcto con una réplica, inseguro al escalar. |
| Guardar contadores en PostgreSQL | Funciona, pero agrega escrituras a la BD principal en cada intento. |
| Redis | Almacén en memoria, rápido, con expiración automática (TTL) y soportado nativamente por Flask-Limiter. |

## Decisión
Redis como almacén del rate limit (`RATELIMIT_STORAGE_URI=redis://redis:6379/0`) en Docker Compose y Kubernetes; opcional (Azure Cache for Redis) en la nube.

## Consecuencias
- El límite es global aunque haya N réplicas: la seguridad no se degrada al escalar.
- /health informa el almacén en uso (rate_limit_storage) para verificarlo en la demo.
- Un servicio más que operar (mitigado: imagen oficial, sin estado crítico).
