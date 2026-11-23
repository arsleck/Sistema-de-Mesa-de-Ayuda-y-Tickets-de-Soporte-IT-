# Guion de demostración – HelpDesk Pro

Recorrido sugerido para la sustentación (≈ 25 min). Cada bloque indica **qué mostrar**, **qué ejecutar** y **qué decir**.

## Preparación (antes de empezar)

```powershell
cd C:\proyectos\web2\Sistema-de-Mesa-de-Ayuda-y-Tickets-de-Soporte-IT
docker compose up -d --build            # opción A: Docker Compose (puertos 8080/9090/3000)
# o bien
minikube start; .\k8s\port-forward.ps1  # opción B: Kubernetes (puertos 8081/9091/3001)
```
Pestañas abiertas: GitHub (repo), la app, Swagger, Grafana y Prometheus.
Usuarios: `admin_soporte` / `super_secreta_123`. Crea antes un empleado desde **Registrarse**.

---

## 1. Contexto y arquitectura (2 min) – teoría
- **Mostrar:** README → diagrama de arquitectura y la carpeta `docs/adr/`.
- **Decir:** "Es una SPA en React que consume una API REST en Flask. Separamos frontend y backend para escalarlos por separado (ADR 0001). Cada herramienta la elegimos comparando alternativas; está documentado en 11 ADR."
- **Mostrar:** `docs/ANALISIS_REQUISITOS.md` → tabla de estado inicial (1 commit, fallas de RBAC, `/health` sin registrar) vs. resumen final.

## 2. API REST + OpenAPI (A1, A4) – 3 min
1. Abrir **`/api/docs`** (Swagger UI) → mostrar los grupos Monitoreo, Autenticación, Usuarios y Tickets.
2. `POST /api/auth/login` → copiar `access_token` → **Authorize** → `GET /api/tickets`.
3. Postman → importar `docs/postman/HelpDesk_Pro.postman_collection.json` → **Run collection** → 26 peticiones en verde.
- **Decir:** "Son más de 5 endpoints CRUD, documentados en OpenAPI 3.0 y con pruebas automáticas en Postman."

## 3. Integración full-stack (A2) – 3 min
1. Como **empleado**: crear un ticket de prioridad **Alta** → solo ve sus tickets.
2. Como **admin**: aparece el aviso rojo de **SLA** (Alta sin asignar) → asignar técnico → pasar a *En Progreso* → *Resuelto*.
3. Clic en el ícono 🕘 del ticket → **historial** (quién, qué, cuándo).
- **Decir:** "React maneja el estado con hooks; Axios adjunta el JWT con un interceptor; SQLAlchemy persiste en PostgreSQL. El historial es una tabla de auditoría (ADR 0011)."

## 4. Seguridad (A3) – 4 min
1. Mostrar `docs/seguridad/evidencia_ANTES.md` (**2/14**) y `evidencia_DESPUES.md` (**14/14**).
2. En vivo:
   ```powershell
   cd backend
   python security\demo_sqli.py          # SQL concatenado vs. parametrizado
   python security\evidencia_seguridad.py http://localhost:8080
   ```
3. App → **Verificación** → *Ejecutar* (11/11) → abrir la evidencia del paso **JWT** (payload del token) y del paso **XSS**.
4. Botón opcional **Fuerza bruta** → 429 al sexto intento.
- **Decir:** "JWT de 30 min + refresh + revocación en el logout (modelo OAuth 2.1). SQLi se evita con el ORM, XSS con saneamiento + CSP + React, y CSRF porque el token no viaja en cookies y CORS está restringido. Además encontramos y corregimos *Broken Access Control*."

## 5. Pruebas (A2, A4) – 2 min
```powershell
cd backend; pytest
start reports\reporte_pruebas.html
```
- **Decir:** "Son 31 pruebas de integración con una base de datos en memoria; el mismo comando corre en el pipeline."

## 6. Docker (A5) – 2 min
```powershell
docker compose ps
docker compose logs --tail 5 backend      # logs en JSON
```
- **Mostrar:** `backend/Dockerfile` (capas, usuario no root, healthcheck) y `frontend/Dockerfile` (multi-stage).
- **Mostrar:** tabla de variables de entorno en `docs/DOCKER_Y_MONITOREO.md`.

## 7. Kubernetes + escalabilidad (A6, A8) – 4 min
```powershell
kubectl get pods,svc,hpa -n helpdesk
1..6 | ForEach-Object { (Invoke-RestMethod http://localhost:8081/health).instance }   # balanceo
kubectl delete pod -n helpdesk -l app=backend --wait=false; kubectl get pods -n helpdesk -w   # autorreparación
```
En dos terminales:
```powershell
kubectl get hpa -n helpdesk -w
python scripts\generar_carga.py --url http://localhost:8081 --usuarios 40 --segundos 180
```
- **Mostrar:** Grafana → *Réplicas (pods) activas* sube de 2 a 6 y *Carga por réplica* se reparte.
- **Decir:** "En la primera prueba la observabilidad nos mostró que la liveness probe reiniciaba pods sanos bajo carga (14 errores). Ajustamos el timeout y la segunda prueba dio 6514 peticiones con 0 errores. Redis comparte el límite de intentos entre réplicas (ADR 0007)."

## 8. Monitorización (A8) – 2 min
- App → **Monitoreo** → Grafana: disponibilidad, latencia p95, códigos HTTP (401/403/429), negocio y fila **SLA**.
- Prometheus → *Status → Targets* (un target por pod) y *Alerts* (6 reglas).
- Disponibilidad en vivo (Compose): `docker compose stop backend` → panel **CAÍDO** / alerta `BackendCaido` → `docker compose start backend`.

## 9. GitFlow + CI/CD + Terraform (A6, A7) – 3 min
1. GitHub → **Insights → Network**: ramas `feature/*` → `develop` → `main`; **Pull requests → Closed**.
2. **Actions** → abrir una ejecución: `backend-tests` → `frontend-build` → `validate-iac` → `docker-images` → `deploy-kubernetes`; descargar el artifact `backend-reports`.
3. **Packages** del repositorio: imágenes en GHCR.
4. `terraform/` → `main.tf` (Container Apps, PostgreSQL Flexible, autoescalado HTTP) y `README.md` (en inglés).
- **Decir:** "El pipeline no deja integrar código que rompa pruebas o seguridad. El despliegue a Azure se activa en `main` con la variable `AZURE_DEPLOY` y las credenciales como *secrets*."

## Preguntas frecuentes

| Pregunta | Respuesta corta |
|---|---|
| ¿Por qué Flask y no Django? | API ligera; agregamos solo lo necesario como extensiones (ADR 0001). |
| ¿Dónde se guarda el token? | En `localStorage`; se mitiga XSS con saneamiento, CSP y React (ADR 0003). |
| ¿Por qué Redis? | Con varias réplicas el contador en memoria no se comparte (ADR 0007). |
| ¿Qué pasa si cae la BD? | `/health` responde 503, la readiness probe saca al pod del balanceo y Grafana lo muestra. |
| ¿Por qué Container Apps y no AKS? | Serverless, autoescalado HTTP y TLS incluidos, a menor costo (ADR 0010). |
| ¿Cómo se mide el SLA? | Histograma de tiempo de resolución + alerta de urgentes sin asignar (ADR 0011). |
