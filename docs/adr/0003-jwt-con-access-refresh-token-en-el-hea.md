# ADR 0003: JWT con access + refresh token en el header Authorization

**Estado:** Aceptada · **Actividad del curso:** A3

## Contexto
La API es stateless y debe poder escalar a varias réplicas sin compartir sesiones en memoria. Además se debe mitigar CSRF.

## Opciones evaluadas
| Opción | Evaluación |
|---|---|
| Sesiones con cookie en el servidor | Requiere almacén compartido de sesiones y es vulnerable a CSRF si no se agregan tokens anti-CSRF. |
| JWT único de larga duración | Simple, pero un token robado sirve por mucho tiempo y no se puede invalidar. |
| JWT corto + refresh token + lista negra (modelo OAuth 2.1) | Sesiones renovables, revocables y sin estado en cada réplica. |

## Decisión
Access token de 30 min y refresh token de 7 días, enviados en el header Authorization; logout revoca el jti en la tabla token_blocklist.

## Consecuencias
- Cualquier réplica valida el token sin consultar a las demás (escalabilidad horizontal).
- El navegador no adjunta el token automáticamente: CSRF no es explotable.
- El token se guarda en localStorage: el riesgo XSS se mitiga con saneamiento (nh3) + CSP + escape de React.
