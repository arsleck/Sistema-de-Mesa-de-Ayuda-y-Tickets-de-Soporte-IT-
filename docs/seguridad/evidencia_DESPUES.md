# Evidencia DESPUÉS — rama `feature/seguridad-owasp`

Objetivo: `http://127.0.0.1:5000` — 2026-11-23 12:56

| OWASP | Prueba | Resultado | Detalle |
|---|---|:---:|---|
| A03 SQL Injection | Login con payload ' OR '1'='1' -- | 🟢 Protegido | HTTP 401 (200 = entró sin contraseña) |
| A03 SQLi + A01 | Búsqueda ?q=' OR 1=1 -- no expone tickets ajenos | 🟢 Protegido | 0 ticket(s) de la víctima expuestos |
| A03 XSS almacenado | El HTML/JS malicioso se elimina antes de guardar | 🟢 Protegido | Guardado: 'Impresora dañada' |
| A03 XSS (navegador) | Cabecera Content-Security-Policy presente | 🟢 Protegido | default-src 'none'; frame-ancestors 'none' |
| CSRF / CORS | Un sitio externo NO es autorizado por CORS | 🟢 Protegido | Access-Control-Allow-Origin: None |
| CSRF | Sin header Authorization la sesión no se usa (cookie ignorada) | 🟢 Protegido | HTTP 401 |
| A01 Control de acceso | Empleado NO ve tickets de otros empleados | 🟢 Protegido | 1 tickets visibles, 0 ajenos |
| A01 Control de acceso | Empleado NO cambia el estado de un ticket ajeno | 🟢 Protegido | HTTP 403 |
| A01 Control de acceso | Empleado NO elimina un ticket ajeno | 🟢 Protegido | HTTP 403 |
| A01 Control de acceso | Lista de técnicos requiere autenticación | 🟢 Protegido | HTTP 401 |
| A07 Autenticación | Fuerza bruta bloqueada (HTTP 429 tras 5 intentos) | 🟢 Protegido | Códigos: [401, 401, 429, 429, 429, 429, 429] |
| A07 Autenticación | Login entrega refresh token (sesión renovable) | 🟢 Protegido | refresh_token presente |
| A07 Autenticación | Logout revoca el token en el servidor | 🟢 Protegido | logout HTTP 200; reuso del token HTTP 401 |
| A05 Configuración | Cabeceras de seguridad HTTP | 🟢 Protegido | todas presentes |

**14/14 controles protegidos**
