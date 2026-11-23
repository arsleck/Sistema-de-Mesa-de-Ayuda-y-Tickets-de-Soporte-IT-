# Evidencia ANTES — código original (commit `db8f541`)

Objetivo: `http://127.0.0.1:5000` — 2026-11-23 12:56

| OWASP | Prueba | Resultado | Detalle |
|---|---|:---:|---|
| A03 SQL Injection | Login con payload ' OR '1'='1' -- | 🟢 Protegido | HTTP 401 (200 = entró sin contraseña) |
| A03 SQLi + A01 | Búsqueda ?q=' OR 1=1 -- no expone tickets ajenos | 🔴 Vulnerable | 1 ticket(s) de la víctima expuestos |
| A03 XSS almacenado | El HTML/JS malicioso se elimina antes de guardar | 🔴 Vulnerable | Guardado: '<script>alert("XSS")</script><img src=x onerr' |
| A03 XSS (navegador) | Cabecera Content-Security-Policy presente | 🔴 Vulnerable | sin CSP |
| CSRF / CORS | Un sitio externo NO es autorizado por CORS | 🔴 Vulnerable | Access-Control-Allow-Origin: http://sitio-malicioso.com |
| CSRF | Sin header Authorization la sesión no se usa (cookie ignorada) | 🟢 Protegido | HTTP 401 |
| A01 Control de acceso | Empleado NO ve tickets de otros empleados | 🔴 Vulnerable | 2 tickets visibles, 1 ajenos |
| A01 Control de acceso | Empleado NO cambia el estado de un ticket ajeno | 🔴 Vulnerable | HTTP 200 |
| A01 Control de acceso | Empleado NO elimina un ticket ajeno | 🔴 Vulnerable | HTTP 200 |
| A01 Control de acceso | Lista de técnicos requiere autenticación | 🔴 Vulnerable | HTTP 200 |
| A07 Autenticación | Fuerza bruta bloqueada (HTTP 429 tras 5 intentos) | 🔴 Vulnerable | Códigos: [401, 401, 401, 401, 401, 401, 401] |
| A07 Autenticación | Login entrega refresh token (sesión renovable) | 🔴 Vulnerable | solo access_token |
| A07 Autenticación | Logout revoca el token en el servidor | 🔴 Vulnerable | logout HTTP 404; reuso del token HTTP 200 |
| A05 Configuración | Cabeceras de seguridad HTTP | 🔴 Vulnerable | faltan: X-Content-Type-Options, X-Frame-Options, Referrer-Policy |

**2/14 controles protegidos**
