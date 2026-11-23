# =====================================================================
#  HelpDesk Pro - Guided demo / Demostración guiada (sustentación)
#
#  Ejecuta EN ORDEN cada verificación del proyecto y hace una pausa entre
#  pasos para explicar en el video. Funciona con Docker Compose (8080) o
#  con Kubernetes + port-forward (8081): se detecta automáticamente.
#
#  Uso (desde la raíz del repositorio, en PowerShell):
#      powershell -ExecutionPolicy Bypass -File scripts\demo_sustentacion.ps1
#      powershell -ExecutionPolicy Bypass -File scripts\demo_sustentacion.ps1 -SinPausas
#      powershell -ExecutionPolicy Bypass -File scripts\demo_sustentacion.ps1 -Desde 6
#
#  Requisitos: sistema en ejecución, Python con backend\requirements-dev.txt.
# =====================================================================
param(
    [switch]$SinPausas,       # corre todo seguido (sin esperar Enter)
    [int]$Desde = 1,          # empezar desde un paso concreto
    [switch]$ConCarga         # incluir la prueba de carga (paso 11)
)
$ErrorActionPreference = "Continue"
$OutputEncoding = [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false
$Repo = "https://github.com/arsleck/Sistema-de-Mesa-de-Ayuda-y-Tickets-de-Soporte-IT-"

# ---------------------------------------------------------------- utilidades
function Paso($n, $en, $es) {
    if ($n -lt $Desde) { return $false }
    Write-Host ""
    Write-Host ("=" * 78) -ForegroundColor DarkCyan
    Write-Host (" STEP {0} | {1}" -f $n, $en) -ForegroundColor Cyan
    Write-Host ("        | {0}" -f $es) -ForegroundColor DarkGray
    Write-Host ("=" * 78) -ForegroundColor DarkCyan
    return $true
}
function Pausa { if (-not $SinPausas) { Read-Host "`n   [Enter] next step / siguiente paso" | Out-Null } }
function Ok($msg)   { Write-Host "   [OK]  $msg" -ForegroundColor Green }
function Info($msg) { Write-Host "   ...   $msg" -ForegroundColor Gray }
function Mal($msg)  { Write-Host "   [X]   $msg" -ForegroundColor Red }

# Llamada HTTP que devuelve código y cuerpo aunque la respuesta sea 4xx/5xx
function Api($method, $path, $body = $null, $token = $null) {
    $headers = @{}
    if ($token) { $headers["Authorization"] = "Bearer $token" }
    $params = @{ Method = $method; Uri = "$Base$path"; Headers = $headers; ContentType = "application/json"; UseBasicParsing = $true }
    if ($body) { $params["Body"] = ($body | ConvertTo-Json -Compress) }
    try {
        $r = Invoke-WebRequest @params
        return @{ code = [int]$r.StatusCode; data = ($r.Content | ConvertFrom-Json); headers = $r.Headers }
    } catch {
        $code = [int]$_.Exception.Response.StatusCode
        $text = ""
        try { $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream()); $text = $reader.ReadToEnd() } catch {}
        if (-not $text -and $_.ErrorDetails) { $text = $_.ErrorDetails.Message }   # PowerShell 7
        $data = $null; try { $data = $text | ConvertFrom-Json } catch {}
        return @{ code = $code; data = $data }
    }
}
function Esperado($r, $codigo, $texto) {
    if ($r.code -eq $codigo) { Ok "$texto -> HTTP $($r.code)" } else { Mal "$texto -> HTTP $($r.code) (expected $codigo)" }
}
function DecodeJwt($t) {
    $p = $t.Split(".")[1].Replace("-", "+").Replace("_", "/")
    switch ($p.Length % 4) { 2 { $p += "==" } 3 { $p += "=" } }
    return [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($p)) | ConvertFrom-Json
}

# ---------------------------------------------------------------- entorno
$Base = $null; $Modo = $null
foreach ($c in @(@{u = "http://localhost:8081"; m = "kubernetes"}, @{u = "http://localhost:8080"; m = "docker"}, @{u = "http://127.0.0.1:5000"; m = "local"})) {
    try { Invoke-RestMethod "$($c.u)/health" -TimeoutSec 3 | Out-Null; $Base = $c.u; $Modo = $c.m; break } catch {}
}
if (-not $Base) { Mal "No se encontró la aplicación. Ejecuta 'docker compose up -d' o '.\k8s\port-forward.ps1'."; exit 1 }
$Grafana = if ($Modo -eq "kubernetes") { "http://localhost:3001" } else { "http://localhost:3000" }
$Prom    = if ($Modo -eq "kubernetes") { "http://localhost:9091" } else { "http://localhost:9090" }
Write-Host "`n HelpDesk Pro - Guided demo | Entorno detectado: $Modo ($Base)" -ForegroundColor Yellow

# Tokens que se reutilizan en varios pasos (el login tiene límite de 5 intentos/min)
$adminLogin = Api POST "/api/auth/login" @{ username = "admin_soporte"; password = "super_secreta_123" }
$AdminToken = $adminLogin.data.access_token
$empName = "empleado_demo_" + (Get-Random -Maximum 9999)
Api POST "/api/auth/register" @{ username = $empName; email = "$empName@empresa.com"; password = "Clave_Demo_123" } | Out-Null
$empLogin = Api POST "/api/auth/login" @{ username = $empName; password = "Clave_Demo_123" }
$EmpToken = $empLogin.data.access_token

# ================================================================ 1. ARQUITECTURA
if (Paso 1 "Architecture: running services" "Arquitectura: servicios en ejecución") {
    if ($Modo -eq "kubernetes") { kubectl get pods,svc,hpa -n helpdesk }
    elseif ($Modo -eq "docker") { docker compose ps }
    else { Info "Modo local: backend Flask + frontend Vite" }
    Pausa
}

# ================================================================ 2. HEALTH + OPENAPI
if (Paso 2 "Health check and OpenAPI documentation (A1, A4)" "Monitoreo de salud y documentación OpenAPI") {
    $h = Api GET "/health"
    $h.data | Format-List status, database, rate_limit_storage, instance
    Esperado $h 200 "API and database are healthy"
    $spec = (Invoke-WebRequest "$Base/api/openapi.yaml" -UseBasicParsing).Content
    if ($spec -is [byte[]]) { $spec = [Text.Encoding]::UTF8.GetString($spec) }   # PowerShell 7 devuelve bytes
    $rutas = ([regex]::Matches($spec, "(?m)^  /\S+:")).Count
    Ok "OpenAPI 3.0 spec published with $rutas documented paths"
    Info "Opening Swagger UI..."; Start-Process "$Base/api/docs"
    Pausa
}

# ================================================================ 3. JWT / OAUTH 2.1
if (Paso 3 "Authentication: JWT access + refresh token (OAuth 2.1 model)" "Autenticación: JWT con token de acceso y de renovación") {
    Esperado $adminLogin 200 "Admin login"
    $payload = DecodeJwt $AdminToken
    Info ("Token payload -> sub: {0} | role: {1} | type: {2} | expires: {3}" -f $payload.sub, $payload.role, $payload.type, ([DateTimeOffset]::FromUnixTimeSeconds($payload.exp).LocalDateTime))
    $ref = Api POST "/api/auth/refresh" $null $adminLogin.data.refresh_token
    Esperado $ref 200 "New access token obtained with the refresh token"
    Esperado (Api GET "/api/tickets") 401 "Request WITHOUT token is rejected"
    Pausa
}

# ================================================================ 4. RBAC
if (Paso 4 "Role-based access control enforced in the backend" "Control de acceso por roles aplicado en el backend") {
    Esperado (Api GET "/api/auth/users" $null $AdminToken) 200 "Admin lists users"
    Esperado (Api GET "/api/auth/users" $null $EmpToken) 403 "Employee CANNOT list users"
    Esperado (Api POST "/api/auth/admin/register" @{ username = "hacker"; email = "h@x.com"; password = "123456" } $EmpToken) 403 "Employee CANNOT create technicians"
    $t = Api POST "/api/tickets" @{ title = "Ticket del empleado"; description = "Prueba RBAC"; priority = "Media" } $EmpToken
    Esperado (Api PUT "/api/tickets/$($t.data.ticket.id)" @{ status = "Resuelto" } $EmpToken) 403 "Employee CANNOT change the status"
    Esperado (Api DELETE "/api/tickets/$($t.data.ticket.id)" $null $EmpToken) 403 "Employee CANNOT delete tickets"
    Api DELETE "/api/tickets/$($t.data.ticket.id)" $null $AdminToken | Out-Null
    Pausa
}

# ================================================================ 5. CRUD + HISTORIAL + SLA
if (Paso 5 "Full ticket lifecycle, audit history and SLA (A1, A2)" "Ciclo de vida del ticket, historial de auditoría y SLA") {
    $c = Api POST "/api/tickets" @{ title = "Servidor de correo caido"; description = "Outlook no conecta"; priority = "Alta" } $EmpToken
    Esperado $c 201 "CREATE: employee reports a HIGH priority ticket #$($c.data.ticket.id)"
    $id = $c.data.ticket.id
    $s = Api GET "/api/tickets/stats" $null $AdminToken
    Info "SLA indicator -> high priority tickets without technician: $($s.data.high_priority_unassigned)"
    $agent = (Api GET "/api/auth/agents" $null $AdminToken).data | Select-Object -First 1
    Esperado (Api PUT "/api/tickets/$id" @{ assigned_to_id = $agent.id; status = "En Progreso" } $AdminToken) 200 "UPDATE: assigned to '$($agent.username)' and moved to In Progress"
    Esperado (Api PUT "/api/tickets/$id" @{ status = "Resuelto" } $AdminToken) 200 "UPDATE: ticket resolved"
    Esperado (Api GET "/api/tickets/$id" $null $EmpToken) 200 "READ: the employee sees the updated ticket"
    Info "Audit history / Historial de auditoría:"
    (Api GET "/api/tickets/$id/history" $null $AdminToken).data | ForEach-Object { "      {0,-12} {1,-14} -> {2,-14} by {3}" -f $_.field, $_.old_value, $_.new_value, $_.user } | Write-Host
    $s = Api GET "/api/tickets/stats" $null $AdminToken
    Ok "SLA: average resolution time = $($s.data.avg_resolution_minutes) min"
    Pausa
}

# ================================================================ 6. XSS / SQLi / CSRF
if (Paso 6 "OWASP: SQL injection, XSS and CSRF (A3)" "OWASP: inyección SQL, XSS y CSRF") {
    $sqli = Api POST "/api/auth/login" @{ username = "' OR '1'='1' --"; password = "' OR '1'='1" }
    Esperado $sqli 401 "SQL injection in login is neutralized"
    $xss = Api POST "/api/tickets" @{ title = '<script>alert("XSS")</script>Monitor sin senal'; description = '<img src=x onerror=alert(1)>Detalle' } $EmpToken
    Ok ("XSS payload stored as plain text: '{0}'" -f $xss.data.ticket.title)
    Api DELETE "/api/tickets/$($xss.data.ticket.id)" $null $AdminToken | Out-Null
    $h = Invoke-WebRequest "$Base/health" -UseBasicParsing
    Ok "Security headers: CSP='$($h.Headers['Content-Security-Policy'])' | X-Frame-Options=$($h.Headers['X-Frame-Options'])"
    Info "Didactic SQL injection demo (vulnerable vs parameterized):"
    python backend/security/demo_sqli.py
    Pausa
}

# ================================================================ 7. PRUEBAS
if (Paso 7 "Automated integration tests with HTML report (A2, A4)" "Pruebas de integración automatizadas con reporte HTML") {
    Push-Location backend
    python -m pytest -q
    Pop-Location
    if (Test-Path backend/reports/reporte_pruebas.html) { Start-Process (Resolve-Path backend/reports/reporte_pruebas.html) }
    Pausa
}

# ================================================================ 8. EVIDENCIA OWASP
if (Paso 8 "OWASP evidence: 14 controlled attacks (before 2/14 -> after 14/14)" "Evidencia OWASP: 14 ataques controlados") {
    Info "Note: this step tests brute force, so login is blocked for ~1 minute afterwards."
    # El login admite 5 intentos por minuto: se espera a que el contador se reinicie
    if ($Desde -lt 8) {
        for ($s = 60; $s -gt 0; $s -= 5) { Write-Host "`r   ...   waiting for the rate limit window / esperando el límite de intentos: $s s " -NoNewline -ForegroundColor Gray; Start-Sleep 5 }
        Write-Host ""
    }
    python backend/security/evidencia_seguridad.py $Base
    Pausa
}

# ================================================================ 9. DOCKER / KUBERNETES
if (Paso 9 "Containers and orchestration (A5, A6)" "Contenedores y orquestación") {
    if ($Modo -eq "kubernetes") {
        Info "Load balancing: each request may be answered by a different pod"
        1..6 | ForEach-Object { "      -> " + (Invoke-RestMethod "$Base/health").instance } | Write-Host
        kubectl get hpa -n helpdesk
        Info "Self-healing: deleting one backend pod..."
        $pod = (kubectl get pods -n helpdesk -l app=backend -o jsonpath="{.items[0].metadata.name}")
        kubectl delete pod $pod -n helpdesk --wait=false
        Start-Sleep 5; kubectl get pods -n helpdesk -l app=backend
    } elseif ($Modo -eq "docker") {
        docker compose ps
        Info "Structured JSON logs:"; docker compose logs --tail 5 backend
    }
    Pausa
}

# ================================================================ 10. MONITOREO
if (Paso 10 "Monitoring: Prometheus metrics, alerts and Grafana (A8)" "Monitorización: métricas, alertas y Grafana") {
    try {
        $up = Invoke-RestMethod "$Prom/api/v1/query?query=up{job=`"helpdesk-backend`"}"
        Ok "Prometheus targets (backend pods UP): $($up.data.result.Count)"
        $rules = Invoke-RestMethod "$Prom/api/v1/rules"
        Ok ("Alert rules loaded: " + (($rules.data.groups | ForEach-Object { $_.rules }) | Measure-Object).Count)
    } catch { Mal "Prometheus no disponible en $Prom" }
    Start-Process $Grafana
    Pausa
}

# ================================================================ 11. CARGA / ESCALABILIDAD
if ($ConCarga -and (Paso 11 "Load test: horizontal autoscaling (A8)" "Prueba de carga: autoescalado horizontal")) {
    Info "Watch Grafana 'Replicas' panel or run 'kubectl get hpa -n helpdesk -w' in another window"
    python scripts/generar_carga.py --url $Base --usuarios 40 --segundos 180
    if ($Modo -eq "kubernetes") { kubectl get hpa -n helpdesk }
    Pausa
}

# ================================================================ 12. GITFLOW + CI/CD
if (Paso 12 "GitFlow, CI/CD pipeline and Terraform (A6, A7)" "GitFlow, pipeline CI/CD y Terraform") {
    git log --oneline --graph -15
    Ok ("Commits in the repository: " + (git rev-list --count HEAD))
    Info "Opening GitHub Actions..."; Start-Process "$Repo/actions"
    Info "Terraform resources (Azure):"
    Select-String -Path terraform/main.tf -Pattern '^resource "' | ForEach-Object { "      " + $_.Line } | Write-Host
}

Write-Host "`n Demo finished / Demostración finalizada" -ForegroundColor Yellow
