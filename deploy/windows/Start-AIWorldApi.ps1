param(
    [string]$RootPath,
    [string]$PythonPath = "python",
    [string]$EnvironmentFile,
    [string]$ListenAddress = "127.0.0.1",
    [int]$Port = 8080,
    [string]$LogDirectory
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "AIWorld.Common.ps1")
Import-AIWorldEnvironment -Path $EnvironmentFile
$root = Resolve-AIWorldRoot -RootPath $RootPath
if (-not $LogDirectory) {
    $LogDirectory = Join-Path $root "logs"
}
$logDirectory = $LogDirectory
New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null
Set-Location $root
$env:AIWORLD_ROOT = $root

& $PythonPath (Join-Path $PSScriptRoot "run_module.py") uvicorn app.main:app `
    --host $ListenAddress `
    --port $Port `
    --log-level info `
    *>> (Join-Path $logDirectory "api.log")
exit $LASTEXITCODE
