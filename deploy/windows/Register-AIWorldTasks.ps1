param(
    [Parameter(Mandatory = $true)]
    [string]$RootPath,
    [Parameter(Mandatory = $true)]
    [string]$PythonPath,
    [string]$EnvironmentFile,
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
$envArguments = if ($EnvironmentFile) {
    "-EnvironmentFile `"$EnvironmentFile`""
} else {
    ""
}

$apiAction = New-ScheduledTaskAction -Execute "pwsh.exe" `
    -Argument (@(
        $common
        "`"$apiScript`""
        "-RootPath"
        "`"$root`""
        "-PythonPath"
        "`"$PythonPath`""
        $envArguments
    ) -join " ")
$schedulerAction = New-ScheduledTaskAction -Execute "pwsh.exe" `
    -Argument (@(
        $common
        "`"$schedulerScript`""
        "-RootPath"
        "`"$root`""
        "-PythonPath"
        "`"$PythonPath`""
        $envArguments
    ) -join " ")
$rotationAction = New-ScheduledTaskAction -Execute "pwsh.exe" `
    -Argument (@(
        $common
        "`"$rotationScript`""
        "-LogDirectory"
        "`"$(Join-Path $root 'logs')`""
    ) -join " ")
$backupAction = New-ScheduledTaskAction -Execute "pwsh.exe" `
    -Argument (@(
        $common
        "`"$backupScript`""
        "-RootPath"
        "`"$root`""
        "-PythonPath"
        "`"$PythonPath`""
        $envArguments
    ) -join " ")

$startup = New-ScheduledTaskTrigger -AtStartup
$daily = New-ScheduledTaskTrigger -Daily -At "03:30"
$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType S4U `
    -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet `
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

Write-Output "Registered AIWorld-API, AIWorld-Scheduler, AIWorld-Backup and AIWorld-LogRotation"
