# ADR 0004: Autorización RBAC aplicada en el backend

**Estado:** Aceptada · **Actividad del curso:** A3

## Contexto
El código original solo ocultaba botones en el frontend; un empleado podía eliminar o cerrar tickets llamando a la API directamente (OWASP A01 – Broken Access Control).

## Opciones evaluadas
| Opción | Evaluación |
|---|---|
| Validar permisos solo en el frontend | Inseguro: cualquier cliente HTTP salta la interfaz. |
| Decorador @roles_required + verificación de propietario | Centralizado, declarativo y fácil de auditar. |

## Decisión
Decorador `@roles_required(...)` y reglas de propietario en cada endpoint; el frontend solo adapta la interfaz.

## Consecuencias
- La regla de seguridad vive en un solo lugar (backend/app/utils/auth_helpers.py).
- Probado automáticamente: test_rbac_seguridad.py y evidencia antes/después (2/14 → 14/14).
