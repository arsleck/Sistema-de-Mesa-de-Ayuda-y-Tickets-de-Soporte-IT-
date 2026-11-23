# =====================================================================
#  Abre túneles desde tu PC hacia los Services del clúster (Minikube + Docker
#  en Windows no expone los NodePort directamente).
#
#   App        -> http://localhost:8081
#   Prometheus -> http://localhost:9091
#   Grafana    -> http://localhost:3001   (admin / admin)
#
#  Se abren 3 ventanas minimizadas; ciérralas para detener los túneles.
# =====================================================================
$ns = "helpdesk"
$tuneles = @(
    @{ svc = "frontend";   local = 8081; remoto = 80 },
    @{ svc = "prometheus"; local = 9091; remoto = 9090 },
    @{ svc = "grafana";    local = 3001; remoto = 3000 }
)
foreach ($t in $tuneles) {
    Start-Process -WindowStyle Minimized kubectl -ArgumentList "port-forward -n $ns svc/$($t.svc) $($t.local):$($t.remoto)"
    Write-Host ("{0,-11} -> http://localhost:{1}" -f $t.svc, $t.local) -ForegroundColor Green
}
