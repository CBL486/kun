param(
    [string]$BaseUrl = "http://127.0.0.1:8080",
    [string]$SchedulerDatabaseUrl,
    [string]$PythonPath = "python",
    [int]$MaxPending = 500,
    [int]$MaxExpiredLeases = 0
)

$ErrorActionPreference = "Stop"
$healthy = $true
$result = [ordered]@{
    checked_at = [DateTimeOffset]::UtcNow.ToString("o")
    health = $false
    ready = $false
    metrics_database_ready = $false
    scheduler_checked = $false
    scheduler_backlog = $null
}

try {
    $health = Invoke-RestMethod -Uri "$BaseUrl/health" -TimeoutSec 10
    $result.health = $health.status -eq "ok"
} catch {
    $result.health = $false
}

try {
    $ready = Invoke-RestMethod -Uri "$BaseUrl/ready" -TimeoutSec 10
    $result.ready = $ready.status -eq "ready"
} catch {
    $result.ready = $false
}

try {
    $metrics = (Invoke-WebRequest -Uri "$BaseUrl/metrics" -TimeoutSec 10).Content
    $result.metrics_database_ready = $metrics -match "aiworld_database_ready 1"
} catch {
    $result.metrics_database_ready = $false
}

if ($SchedulerDatabaseUrl) {
    try {
        $schedulerJson = & $PythonPath -m rpg_scheduler status `
            --url $SchedulerDatabaseUrl
        if ($LASTEXITCODE -ne 0) {
            throw "scheduler status command failed"
        }
        $result.scheduler_checked = $true
        $result.scheduler_backlog = $schedulerJson | ConvertFrom-Json
        if (
            $result.scheduler_backlog.backlog.pending_due -gt $MaxPending -or
            $result.scheduler_backlog.backlog.expired_leases -gt $MaxExpiredLeases
        ) {
            $healthy = $false
        }
    } catch {
        $result.scheduler_checked = $false
        $healthy = $false
    }
}

$healthy = $healthy -and
    $result.health -and
    $result.ready -and
    $result.metrics_database_ready
$result.healthy = $healthy
$result | ConvertTo-Json -Depth 5
if (-not $healthy) {
    exit 1
}
