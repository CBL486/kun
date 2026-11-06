param(
    [Parameter(Mandatory = $true)]
    [string]$RootPath,
    [Parameter(Mandatory = $true)]
    [string]$PythonPath,
    [string]$EnvironmentFile,
    [string]$LogDirectory,
    [string]$BackupDirectory,
    [string]$PgBin,
    [switch]$ConfirmRegistration
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath $RootPath).Path
if (-not $ConfirmRegistration) {
    throw "Set -ConfirmRegistration after reviewing deployment-checklist.md"
}

$common = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File"
)
$apiScript = Join-Path $PSScriptRoot "Start-AIWorldApi.ps1"
$schedulerScript = Join-Path $PSScriptRoot "Start-AIWorldScheduler.ps1"
$backupScript = Join-Path $PSScriptRoot "Invoke-AIWorldBackup.ps1"
$rotationScript = Join-Path $PSScriptRoot "Rotate-AIWorldLogs.ps1"
$monitorScript = Join-Path $PSScriptRoot "AIWorld-Monitor.ps1"
$envArguments = if ($EnvironmentFile) {
    "-EnvironmentFile `"$EnvironmentFile`""
} else {
    ""
}
$logDirectory = if ($LogDirectory) { $LogDirectory } else { Join-Path $root "logs" }
$backupDirectory = if ($BackupDirectory) { $BackupDirectory } else { Join-Path $root "backups" }
$logArguments = "-LogDirectory `"$logDirectory`""
$backupArguments = @(
    "-BackupDirectory"
    "`"$backupDirectory`""
)
if ($PgBin) {
    $backupArguments += @("-PgBin", "`"$PgBin`"")
}

$apiAction = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument (@(
        $common
        "`"$apiScript`""
        "-RootPath"
        "`"$root`""
        "-PythonPath"
        "`"$PythonPath`""
        $envArguments
        $logArguments
    ) -join " ")
$schedulerAction = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument (@(
        $common
        "`"$schedulerScript`""
        "-RootPath"
        "`"$root`""
        "-PythonPath"
        "`"$PythonPath`""
        $envArguments
        $logArguments
    ) -join " ")
$rotationAction = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument (@(
        $common
        "`"$rotationScript`""
        $logArguments
    ) -join " ")
$backupAction = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument (@(
        $common
        "`"$backupScript`""
        "-RootPath"
        "`"$root`""
        "-PythonPath"
        "`"$PythonPath`""
        $envArguments
        $backupArguments
    ) -join " ")

$monitorAction = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument (@(
        $common
        "`"$monitorScript`""
        "-BaseUrl"
        "`"http://127.0.0.1:8080`""
        "-ReleaseRoot"
        "`"$root`""
        $envArguments
        "-PythonPath"
        "`"$PythonPath`""
        "-BackupDirectory"
        "`"$backupDirectory`""
        $logArguments
    ) -join " ")

$startup = New-ScheduledTaskTrigger -AtStartup
$monitorTrigger = New-ScheduledTaskTrigger -Once `
    -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Minutes 5) `
    -RepetitionDuration (New-TimeSpan -Days 3650)
$daily = New-ScheduledTaskTrigger -Daily -At "03:30"
$principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest
$monitorPrincipal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -RestartCount 5 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Days 3650)

Register-ScheduledTask -TaskName "AIWorld-API" `
    -Action $apiAction `
    -Trigger $startup `
    -Principal $principal `
    -Settings $settings `
    -Force | Out-Null
Register-ScheduledTask -TaskName "AIWorld-Scheduler" `
    -Action $schedulerAction `
    -Trigger $startup `
    -Principal $principal `
    -Settings $settings `
    -Force | Out-Null
Register-ScheduledTask -TaskName "AIWorld-LogRotation" `
    -Action $rotationAction `
    -Trigger $daily `
    -Principal $principal `
    -Settings $settings `
    -Force | Out-Null
Register-ScheduledTask -TaskName "AIWorld-Backup" `
    -Action $backupAction `
    -Trigger (New-ScheduledTaskTrigger -Daily -At "03:00") `
    -Principal $principal `
    -Settings $settings `
    -Force | Out-Null
Register-ScheduledTask -TaskName "AIWorld-Monitor" `
    -Action $monitorAction `
    -Trigger $monitorTrigger `
    -Principal $monitorPrincipal `
    -Settings $settings `
    -Force | Out-Null

Write-Output "Registered AIWorld-API, AIWorld-Scheduler, AIWorld-Backup, AIWorld-LogRotation and AIWorld-Monitor"
