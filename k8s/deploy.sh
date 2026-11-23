#!/usr/bin/env bash
# =====================================================================
#  Despliegue en un clúster Kubernetes local (Linux/macOS o GitHub Actions con kind).
#  Equivalente a deploy.ps1. Uso:  CLUSTER=kind bash k8s/deploy.sh
#  CLUSTER=minikube (por defecto) construye las imágenes dentro de Minikube;
#  CLUSTER=kind carga en kind imágenes ya construidas con "docker build".
# =====================================================================
set -euo pipefail
NS=helpdesk
CLUSTER=${CLUSTER:-minikube}

echo "==> Imágenes ($CLUSTER)"
if [ "$CLUSTER" = "minikube" ]; then
  minikube image build -t helpdesk-backend:latest -f backend/Dockerfile .
  minikube image build -t helpdesk-frontend:latest frontend
else
  kind load docker-image helpdesk-backend:latest helpdesk-frontend:latest --name "${KIND_CLUSTER:-kind}"
fi

echo "==> Namespace y configuración"
kubectl apply -f k8s/00-namespace.yaml -f k8s/01-config.yaml
kubectl create configmap prometheus-config -n $NS --dry-run=client -o yaml \
  --from-file=prometheus.yml=k8s/monitoring/prometheus-k8s.yml \
  --from-file=alerts.yml=monitoring/prometheus/alerts.yml | kubectl apply -f -
kubectl create configmap grafana-datasources -n $NS --dry-run=client -o yaml \
  --from-file=monitoring/grafana/provisioning/datasources/prometheus.yml | kubectl apply -f -
kubectl create configmap grafana-providers -n $NS --dry-run=client -o yaml \
  --from-file=monitoring/grafana/provisioning/dashboards/dashboards.yml | kubectl apply -f -
kubectl create configmap grafana-dashboards -n $NS --dry-run=client -o yaml \
  --from-file=monitoring/grafana/dashboards/helpdesk.json | kubectl apply -f -

echo "==> Manifiestos"
kubectl apply -f k8s/

echo "==> Esperando despliegues"
for d in postgres redis backend frontend; do
  kubectl rollout status deployment/$d -n $NS --timeout=240s
done
kubectl get pods,svc,hpa -n $NS
