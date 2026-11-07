param(
    [string]$RootPath,
    [string]$PythonPath = "python",
    [string]$EnvironmentFile,
    [string]$LogDirectory
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "AIWorld.Common.ps1")
Import-AIWorldEnvironment -Path $EnvironmentFile
$root = Resolve-AIWorldRoot -RootPath $RootPath
if (-not $LogDirectory) {
    $LogDirectory = Join-Path $root "logs"
}
New-Item -ItemType Directory -Force -Path $LogDirectory | Out-Null
Set-Location $root
$env:AIWORLD_ROOT = $root

$serviceErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $PythonPath (Join-Path $PSScriptRoot "run_module.py") app.world_tick `
    *>> (Join-Path $LogDirectory "world-tick.log")
$serviceExitCode = $LASTEXITCODE
$ErrorActionPreference = $serviceErrorActionPreference
exit $serviceExitCode
