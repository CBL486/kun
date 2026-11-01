param(
    [string]$RootPath,
    [string]$PythonPath = "python",
    [string]$EnvironmentFile,
    [string]$ListenAddress = "127.0.0.1",
    [int]$Port = 8080
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "AIWorld.Common.ps1")
Import-AIWorldEnvironment -Path $EnvironmentFile
$root = Resolve-AIWorldRoot -RootPath $RootPath
$logDirectory = Join-Path $root "logs"
New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null
Set-Location $root

& $PythonPath -m uvicorn app.main:app `
    --host $ListenAddress `
    --port $Port `
    --log-level info `
    *>> (Join-Path $logDirectory "api.log")
exit $LASTEXITCODE
