param(
    [string]$Date = "2026-11-04"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot "resolve-b1-python.ps1")
$pythonPath = Resolve-B1Python

Push-Location $repoRoot
try {
    & $pythonPath -m rpg_npc --date $Date
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
