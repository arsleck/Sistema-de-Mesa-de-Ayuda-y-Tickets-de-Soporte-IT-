# Kubernetes, CI/CD e Infraestructura como Código (Actividades 6, 7 y 8)

## 1. Arquitectura en Kubernetes (namespace `helpdesk`)

```text
 kubectl port-forward ─► Service frontend (NodePort 30080)
                              │
                    ┌─────────▼─────────┐
                    │ Deployment        │  2 réplicas Nginx + React
                    │ frontend          │
                    └─────────┬─────────┘
                              │ http://backend:5000
                    ┌─────────▼─────────┐      HPA: 2 → 6 réplicas
                    │ Deployment backend│◄──── (CPU > 50 %)
                    │ pod │ pod │ ...   │
                    └──┬──────────┬─────┘
                       │          │
          ┌────────────▼──┐   ┌───▼───────────┐     ┌────────────┐   ┌─────────┐
          │ postgres + PVC│   │ redis         │     │ prometheus │──►│ grafana │
          └───────────────┘   └───────────────┘     └─────┬──────┘   └─────────┘
                                                          │ descubre cada pod del backend
```

| Archivo | Recursos |
|---|---|
| `k8s/00-namespace.yaml` | Namespace `helpdesk` |
| `k8s/01-config.yaml` | ConfigMap (configuración) + Secret (contraseñas, JWT) |
| `k8s/10-postgres.yaml` | PVC 1 Gi + Deployment + Service de PostgreSQL |
| `k8s/11-redis.yaml` | Deployment + Service de Redis (límite de intentos compartido) |
| `k8s/20-backend.yaml` | Deployment (2 réplicas, probes, RollingUpdate, requests/limits) + Service |
| `k8s/21-backend-hpa.yaml` | HorizontalPodAutoscaler 2–6 réplicas al 50 % de CPU |
| `k8s/30-frontend.yaml` | Deployment (2 réplicas) + Service NodePort |
| `k8s/40-monitoring.yaml` | Prometheus (con RBAC para descubrir pods) + Grafana |

### Conceptos clave para la sustentación
| Concepto | Dónde se ve |
|---|---|
| **Pod** | `kubectl get pods -n helpdesk`: cada contenedor en ejecución |
| **Deployment** | Mantiene N réplicas; si un pod muere, crea otro |
| **Service** | DNS interno estable (`backend`, `postgres`, `redis`) y balanceo entre pods |
| **readinessProbe** | Un pod del backend solo recibe tráfico si `/health` (API + BD) responde |
| **livenessProbe** | Si el backend se cuelga, Kubernetes reinicia el contenedor |
| **RollingUpdate** | Actualización sin caída (`maxUnavailable: 0`) |
| **HPA** | Escala el backend según la CPU |
| **PVC** | Los datos de PostgreSQL sobreviven al reinicio del pod |
| **ConfigMap / Secret** | Configuración separada del código |

## 2. Despliegue en Minikube (Windows)

```powershell
# Una sola vez
minikube start --driver=docker --cpus=4 --memory=6144
minikube addons enable metrics-server

# Desde la raíz del repositorio
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\k8s\deploy.ps1          # construye imágenes dentro de Minikube y aplica todo
.\k8s\port-forward.ps1    # abre App :8081, Prometheus :9091, Grafana :3001
```

### Demostración paso a paso
```powershell
kubectl get pods,svc,hpa -n helpdesk          # 1. Ver los recursos

# 2. Balanceo: cada /health indica el pod que respondió ("instance")
1..6 | ForEach-Object { (Invoke-RestMethod http://localhost:8081/health).instance }

# 3. Autorreparación: borrar un pod y ver cómo Kubernetes lo recrea
kubectl delete pod -n helpdesk -l app=backend --wait=false
kubectl get pods -n helpdesk -w               # Ctrl+C para salir

# 4. Escalabilidad: generar carga y observar el HPA
python scripts\generar_carga.py --url http://localhost:8081 --usuarios 40 --segundos 180
kubectl get hpa -n helpdesk -w                # REPLICAS sube de 2 hacia 6
```
En Grafana (http://localhost:3001) los paneles **Réplicas (pods) activas** y **Carga por réplica** muestran el escalado en vivo.

```powershell
# 5. Actualización sin caída (rolling update)
kubectl rollout restart deployment/backend -n helpdesk
kubectl rollout status deployment/backend -n helpdesk

# Limpiar
kubectl delete namespace helpdesk
minikube stop
```

## 3. GitFlow

```text
main ────────────────────────────────────────●  release 2.0.0
          \                                 /
develop ───●───────●───────●───────●───────●
            \     / \     / \     / \     /
 feature/api-rest-rbac  seguridad-owasp  pruebas  docker-monitoreo  k8s-cicd-terraform
```
- `feature/*` → PR hacia `develop` (cada fase es un PR revisado).
- `develop` → PR hacia `main` al cerrar una versión (`release`).
- Mensajes con *Conventional Commits*: `feat:`, `fix:`, `docs:`, `test:`, `chore:`.

## 4. Pipeline CI/CD (`.github/workflows/ci-cd.yml`)

| # | Job | Qué hace | Falla si… |
|---|---|---|---|
| 1 | `backend-tests` | pytest (reporte HTML) + script OWASP contra el servidor | alguna prueba falla o un control no está protegido |
| 2 | `frontend-build` | ESLint + build de producción | hay errores de lint o de compilación |
| 3 | `validate-iac` | kubeconform sobre `k8s/` + `terraform fmt` y `validate` | un manifiesto o el Terraform es inválido |
| 4 | `docker-images` | construye ambas imágenes y las publica en GHCR (`ghcr.io/arsleck/helpdesk-*`) | falla el build |
| 5 | `deploy-kubernetes` | crea un clúster **kind**, despliega `k8s/` y hace smoke test a `/health` | el despliegue no queda sano |
| 6 | `deploy-azure` | `terraform plan` + `apply` en Azure (solo `main` con `AZURE_DEPLOY=true`) | — |

Los reportes de pruebas y la evidencia de seguridad quedan como **artifacts** descargables en cada ejecución (pestaña *Actions*).

## 5. Infraestructura como código (Terraform → Azure)

Ver [`terraform/README.md`](../terraform/README.md), escrito en inglés como pide la Actividad 7.
Crea con un solo `terraform apply`: Resource Group, Log Analytics, PostgreSQL Flexible Server, Redis (opcional), Container Apps Environment, backend con autoescalado HTTP (1–5) y frontend con HTTPS público.

## 6. Decisiones de arquitectura

Las razones de cada herramienta están en [`docs/adr/`](adr/README.md).
