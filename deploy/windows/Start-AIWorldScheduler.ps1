param(
    [string]$RootPath,
    [string]$PythonPath = "python",
    [string]$EnvironmentFile,
    [string]$WorkerId = "scheduler-1",
    [string]$LogDirectory
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "AIWorld.Common.ps1")
Import-AIWorldEnvironment -Path $EnvironmentFile
$root = Resolve-AIWorldRoot -RootPath $RootPath
$databaseUrl = $env:AIWORLD_SCHEDULER_DATABASE_URL
if (-not $databaseUrl) {
    throw "AIWORLD_SCHEDULER_DATABASE_URL is required"
}
if (-not $LogDirectory) {
    $LogDirectory = Join-Path $root "logs"
}
$logDirectory = $LogDirectory
New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null
Set-Location $root
$env:AIWORLD_ROOT = $root

if ($databaseUrl -match "@([^:/]+):([0-9]+)/") {
    Wait-AIWorldTcpPort -HostName $matches[1] -Port ([int]$matches[2])
}

$serviceErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $PythonPath (Join-Path $PSScriptRoot "run_module.py") rpg_scheduler run `
    --url $databaseUrl `
    --worker-id $WorkerId `
    --poll-interval 1 `
    *>> (Join-Path $logDirectory "scheduler.log")
$serviceExitCode = $LASTEXITCODE
$ErrorActionPreference = $serviceErrorActionPreference
exit $serviceExitCode
