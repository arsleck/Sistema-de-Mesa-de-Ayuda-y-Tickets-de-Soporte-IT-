# =====================================================================
#  Despliegue de HelpDesk Pro en Minikube (Windows / PowerShell)
#
#  Uso (desde la raíz del repositorio):
#      .\k8s\deploy.ps1              # construye imágenes y despliega todo
#      .\k8s\deploy.ps1 -SkipBuild   # solo vuelve a aplicar los manifiestos
#
#  Requisitos: Docker Desktop abierto + minikube start + addon metrics-server
# =====================================================================
param([switch]$SkipBuild)
$ErrorActionPreference = "Stop"
$ns = "helpdesk"

function Paso($texto) { Write-Host "`n==> $texto" -ForegroundColor Cyan }

Paso "1/6 Verificando el clúster"
kubectl get nodes

if (-not $SkipBuild) {
    # Las imágenes se construyen DENTRO de Minikube: así el clúster las tiene sin un registro externo
    Paso "2/6 Construyendo imagen del backend dentro de Minikube"
    minikube image build -t helpdesk-backend:latest -f backend/Dockerfile .
    Paso "2/6 Construyendo imagen del frontend dentro de Minikube"
    minikube image build -t helpdesk-frontend:latest frontend
}

Paso "3/6 Namespace, ConfigMap y Secret"
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-config.yaml

Paso "4/6 Configuración de Prometheus y Grafana (ConfigMaps desde la carpeta monitoring/)"
# --dry-run + apply = crea o actualiza el ConfigMap sin error si ya existe
kubectl create configmap prometheus-config -n $ns --dry-run=client -o yaml `
    --from-file=prometheus.yml=k8s/monitoring/prometheus-k8s.yml `
    --from-file=alerts.yml=monitoring/prometheus/alerts.yml | kubectl apply -f -
kubectl create configmap grafana-datasources -n $ns --dry-run=client -o yaml `
    --from-file=monitoring/grafana/provisioning/datasources/prometheus.yml | kubectl apply -f -
kubectl create configmap grafana-providers -n $ns --dry-run=client -o yaml `
    --from-file=monitoring/grafana/provisioning/dashboards/dashboards.yml | kubectl apply -f -
kubectl create configmap grafana-dashboards -n $ns --dry-run=client -o yaml `
    --from-file=monitoring/grafana/dashboards/helpdesk.json | kubectl apply -f -

Paso "5/6 Desplegando base de datos, Redis, backend (+HPA), frontend y monitoreo"
kubectl apply -f k8s/
# Si las imágenes se reconstruyeron con la misma etiqueta, se reinician los pods para usarlas
if (-not $SkipBuild) { kubectl rollout restart deployment/backend deployment/frontend -n $ns }

Paso "6/6 Esperando a que todo esté listo"
foreach ($d in "postgres", "redis", "backend", "frontend", "prometheus", "grafana") {
    kubectl rollout status deployment/$d -n $ns --timeout=180s
}

kubectl get pods,svc,hpa -n $ns
Write-Host "`nListo. Para abrir la aplicación ejecuta:  .\k8s\port-forward.ps1" -ForegroundColor Green
