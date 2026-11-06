param(
    [string]$BaseUrl = "http://127.0.0.1:8080",
    [string]$EnvironmentFile,
    [string]$PythonPath = "python",
    [string]$ReleaseRoot,
    [string]$BackupDirectory,
    [string]$LogDirectory,
    [int]$MaxBackupAgeHours = 36,
    [int]$MaxPending = 500,
    [int]$MaxExpiredLeases = 0,
    [int]$MinDiskFreeGb = 5
)

$ErrorActionPreference = "Stop"
$failures = @()
$checkedAt = [DateTimeOffset]::UtcNow.ToString("o")

if ($EnvironmentFile) {
    if (-not (Test-Path -LiteralPath $EnvironmentFile)) {
        $failures += "environment_file_missing"
    } else {
        foreach ($line in Get-Content -LiteralPath $EnvironmentFile) {
            $trimmed = $line.Trim()
            if (-not $trimmed -or $trimmed.StartsWith("#")) {
                continue
            }
            $parts = $trimmed.Split("=", 2)
            if ($parts.Count -eq 2) {
                [Environment]::SetEnvironmentVariable(
                    $parts[0].Trim(),
                    $parts[1],
                    "Process"
                )
            }
        }
    }
}

if (-not $ReleaseRoot) {
    $ReleaseRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path
}
if (-not $BackupDirectory) {
    $BackupDirectory = Join-Path $ReleaseRoot "backups"
}
if (-not $LogDirectory) {
    $LogDirectory = Join-Path $ReleaseRoot "logs"
}
New-Item -ItemType Directory -Force -Path $LogDirectory | Out-Null
$env:AIWORLD_ROOT = $ReleaseRoot

$base = $BaseUrl.TrimEnd("/")
$health = $false
$ready = $false
$databaseReady = $false
$schedulerChecked = $false
$pendingDue = $null
$delayed = $null
$leased = $null
$expiredLeases = $null
$backupAgeHours = $null
$diskFreeGb = $null
$taskStates = [ordered]@{}

try {
    $healthResponse = Invoke-RestMethod -Uri "$base/health" -TimeoutSec 10
    $health = $healthResponse.status -eq "ok"
    if (-not $health) {
        $failures += "health_not_ok"
    }
} catch {
    $failures += "health_request_failed"
}

try {
    $readyResponse = Invoke-RestMethod -Uri "$base/ready" -TimeoutSec 10
    $ready = $readyResponse.status -eq "ready"
    if (-not $ready) {
        $failures += "ready_not_ready"
    }
} catch {
    $failures += "ready_request_failed"
}

try {
    $metrics = (Invoke-WebRequest -UseBasicParsing -Uri "$base/metrics" -TimeoutSec 10).Content
    $databaseReady = $metrics -match "(?m)^aiworld_database_ready 1$"
    if (-not $databaseReady) {
        $failures += "database_not_ready_metric"
    }
    foreach ($metric in @(
        "scheduler_pending_due",
        "scheduler_delayed",
        "scheduler_leased",
        "scheduler_expired_leases"
    )) {
        $match = [regex]::Match($metrics, "(?m)^aiworld_$metric ([0-9.]+)$")
        if ($match.Success) {
            $value = [double]$match.Groups[1].Value
            switch ($metric) {
                "scheduler_pending_due" { $pendingDue = $value }
                "scheduler_delayed" { $delayed = $value }
                "scheduler_leased" { $leased = $value }
                "scheduler_expired_leases" { $expiredLeases = $value }
            }
        }
    }
    if ($pendingDue -ne $null -and $pendingDue -gt $MaxPending) {
        $failures += "scheduler_backlog"
    }
    if ($expiredLeases -ne $null -and $expiredLeases -gt $MaxExpiredLeases) {
        $failures += "scheduler_expired_leases"
    }
} catch {
    $failures += "metrics_request_failed"
}
if ($env:AIWORLD_SCHEDULER_DATABASE_URL -and (Test-Path -LiteralPath $ReleaseRoot)) {
    $runner = Join-Path $ReleaseRoot "deploy\windows\run_module.py"
    if (-not (Test-Path -LiteralPath $runner)) {
        $failures += "module_runner_missing"
    } else {
        $previousErrorAction = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            $statusText = & $PythonPath $runner rpg_scheduler status `
                --url $env:AIWORLD_SCHEDULER_DATABASE_URL 2>$null
            $statusExitCode = $LASTEXITCODE
        } finally {
            $ErrorActionPreference = $previousErrorAction
        }
        if ($statusExitCode -ne 0) {
            $failures += "scheduler_status_failed"
        } else {
            try {
                $status = $statusText | ConvertFrom-Json
                $schedulerChecked = $true
                if ($null -eq $pendingDue) {
                    $pendingDue = [double]$status.backlog.pending_due
                }
                if ($null -eq $delayed) {
                    $delayed = [double]$status.backlog.delayed
                }
                if ($null -eq $leased) {
                    $leased = [double]$status.backlog.leased
                }
                if ($null -eq $expiredLeases) {
                    $expiredLeases = [double]$status.backlog.expired_leases
                }
            } catch {
                $failures += "scheduler_status_invalid"
            }
        }
    }
}

try {
    $newestBackup = Get-ChildItem -LiteralPath $BackupDirectory -File |
        Where-Object { $_.Name -like "aiworld-*" -and $_.Name -notlike "*.json" } |
        Sort-Object LastWriteTimeUtc -Descending |
        Select-Object -First 1
    if (-not $newestBackup) {
        $failures += "backup_missing"
    } else {
        $backupAgeHours = [Math]::Round(
            ([DateTime]::UtcNow - $newestBackup.LastWriteTimeUtc).TotalHours,
            2
        )
        if ($backupAgeHours -gt $MaxBackupAgeHours) {
            $failures += "backup_stale"
        }
    }
} catch {
    $failures += "backup_check_failed"
}

try {
    $diskFreeGb = [Math]::Round((Get-PSDrive -Name C).Free / 1GB, 2)
    if ($diskFreeGb -lt $MinDiskFreeGb) {
        $failures += "disk_space_low"
    }
} catch {
    $failures += "disk_check_failed"
}

foreach ($name in @(
    "AIWorld-API",
    "AIWorld-Scheduler",
    "AIWorld-Backup",
    "AIWorld-LogRotation"
)) {
    $task = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    if (-not $task) {
        $taskStates[$name] = "Missing"
        $failures += "task_missing:$name"
        continue
    }
    $taskStates[$name] = [string]$task.State
    if ($name -in @("AIWorld-API", "AIWorld-Scheduler") -and $task.State -ne "Running") {
        $failures += "task_not_running:$name"
    }
}
$healthy = $failures.Count -eq 0
$result = [ordered]@{
    schema_version = "aiworld-monitor-v1"
    checked_at = $checkedAt
    healthy = $healthy
    failures = @($failures)
    health = $health
    ready = $ready
    database_ready = $databaseReady
    scheduler_checked = $schedulerChecked
    scheduler_pending_due = $pendingDue
    scheduler_delayed = $delayed
    scheduler_leased = $leased
    scheduler_expired_leases = $expiredLeases
    backup_age_hours = $backupAgeHours
    disk_free_gb = $diskFreeGb
    task_states = [ordered]@{
        api = $taskStates["AIWorld-API"]
        scheduler = $taskStates["AIWorld-Scheduler"]
        backup = $taskStates["AIWorld-Backup"]
        log_rotation = $taskStates["AIWorld-LogRotation"]
    }
}
$json = $result | ConvertTo-Json -Depth 8

$latestPath = Join-Path $LogDirectory "monitor-latest.json"
$historyPath = Join-Path $LogDirectory "monitor-history.ndjson"
$alertPath = Join-Path $LogDirectory "monitor-alert.txt"
[IO.File]::WriteAllText($latestPath, $json + "`n", (New-Object Text.UTF8Encoding($false)))
[IO.File]::AppendAllText($historyPath, ($json -replace "\r?\n", " ") + "`n", (New-Object Text.UTF8Encoding($false)))

if ($healthy) {
    if (Test-Path -LiteralPath $alertPath) {
        Remove-Item -LiteralPath $alertPath -Force
    }
} else {
    $alertText = "$checkedAt`n" + ($failures -join "`n") + "`n"
    [IO.File]::WriteAllText($alertPath, $alertText, (New-Object Text.UTF8Encoding($false)))
}

Write-Output $json
if (-not $healthy) {
    exit 1
}
