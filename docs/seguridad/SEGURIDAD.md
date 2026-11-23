# Seguridad web – HelpDesk Pro (Actividad 3)

Autenticación con **JWT bajo el modelo OAuth 2.1** (access token + refresh token + revocación) y mitigación de vulnerabilidades del **OWASP Top 10 2023**, con evidencia de pruebas **antes / después**.

## 1. Resultado antes / después

| | Código original (`db8f541`) | Versión segura |
|---|:---:|:---:|
| Controles protegidos | **2 / 14** 🔴 | **14 / 14** 🟢 |
| Detalle | [evidencia_ANTES.md](evidencia_ANTES.md) | [evidencia_DESPUES.md](evidencia_DESPUES.md) |

Ambos reportes se generaron con el mismo script automático: `backend/security/evidencia_seguridad.py`.

## 2. Autenticación (JWT y modelo OAuth 2.1)

```text
 Login ──► access_token (30 min)  ──► Authorization: Bearer <token> en cada petición
       └─► refresh_token (7 días) ──► POST /api/auth/refresh  → nuevo access_token
 Logout ─► POST /api/auth/logout  → el "jti" del token se guarda en token_blocklist
                                    y el servidor lo rechaza aunque no haya vencido
```

| Práctica OAuth 2.1 | Cómo se aplica |
|---|---|
| Tokens de acceso de vida corta | `JWT_ACCESS_TOKEN_EXPIRES` = 30 min (configurable). |
| Refresh token separado | `create_refresh_token`; solo sirve en `/api/auth/refresh`. |
| Revocación de tokens | Tabla `token_blocklist` + `token_in_blocklist_loader`. |
| Bearer token solo en el header | Nunca en la URL ni en cookies. |
| Renovación transparente en el cliente | Interceptor de Axios (`frontend/src/api/axiosConfig.js`). |

## 3. Vulnerabilidades mitigadas

### A03 – SQL Injection
- **Riesgo:** si el texto del usuario se pega dentro del SQL, `' OR '1'='1` convierte la condición en siempre verdadera.
- **Mitigación:** todas las consultas usan el ORM SQLAlchemy, que envía los valores como **parámetros**.
- **Demostración didáctica:** `python backend/security/demo_sqli.py` compara la consulta vulnerable (f-string) con la parametrizada, en una base SQLite en memoria.

### A03 – Cross-Site Scripting (XSS)
- **Riesgo:** un ticket con `<script>` o `<img onerror=...>` ejecuta código en el navegador del técnico que lo abre.
- **Mitigación en tres capas:**
  1. **Backend:** `sanitize_text()` (librería `nh3`) elimina toda etiqueta HTML antes de guardar.
  2. **Frontend:** React escapa automáticamente el contenido (no se usa `dangerouslySetInnerHTML`).
  3. **Navegador:** cabecera `Content-Security-Policy`.

### CSRF – Cross-Site Request Forgery
- **Riesgo:** una página maliciosa envía peticiones usando la sesión que el navegador guarda en cookies.
- **Mitigación:**
  - El JWT viaja en el header `Authorization`, que el navegador **no** envía solo (no hay cookies de sesión).
  - CORS restringido a los orígenes del frontend (`CORS_ORIGINS`). Un sitio externo no recibe `Access-Control-Allow-Origin`.

### A01 – Control de acceso roto (hallazgo extra)
- **Antes:** un empleado podía cambiar el estado de cualquier ticket, eliminarlo, ver los de otros y listar técnicos sin token.
- **Después:** RBAC en el backend con `@roles_required` y verificación de dueño del ticket.

### A07 – Fallas de autenticación
- Límite de **5 intentos de login por minuto por IP** (`Flask-Limiter`) → HTTP 429.
- Contraseñas con **bcrypt** (sal aleatoria) y longitud mínima.

### A05 – Configuración de seguridad incorrecta
- Cabeceras: `X-Content-Type-Options`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Cache-Control: no-store`.
- `debug` desactivado por defecto; secretos solo desde variables de entorno.

## 4. Cómo reproducir la evidencia (demo)

```powershell
cd backend
venv\Scripts\activate
pip install -r requirements.txt

# 1) DESPUÉS: con la versión actual del backend encendida (python run.py) en otra terminal
python security\evidencia_seguridad.py

# 2) ANTES: copiar el script fuera del repo y volver temporalmente al commit original
copy security\evidencia_seguridad.py $env:TEMP\
git checkout db8f541
python run.py                                    # en otra terminal
python $env:TEMP\evidencia_seguridad.py
git checkout -                                   # regresar a la rama actual

# 3) Demo teórica de SQL Injection
python security\demo_sqli.py
```

> El login admite 5 intentos por minuto. Si repites el script seguido, espera un minuto.
