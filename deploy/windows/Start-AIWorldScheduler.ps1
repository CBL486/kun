param(
    [string]$RootPath,
    [string]$PythonPath = "python",
    [string]$EnvironmentFile,
    [string]$WorkerId = "scheduler-1"
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "AIWorld.Common.ps1")
Import-AIWorldEnvironment -Path $EnvironmentFile
$root = Resolve-AIWorldRoot -RootPath $RootPath
$databaseUrl = $env:AIWORLD_SCHEDULER_DATABASE_URL
if (-not $databaseUrl) {
    throw "AIWORLD_SCHEDULER_DATABASE_URL is required"
}
$logDirectory = Join-Path $root "logs"
New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null
Set-Location $root

& $PythonPath -m rpg_scheduler run `
    --url $databaseUrl `
    --worker-id $WorkerId `
    --poll-interval 1 `
    *>> (Join-Path $logDirectory "scheduler.log")
exit $LASTEXITCODE
