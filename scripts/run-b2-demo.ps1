param(
    [string]$Date = "2026-11-02",
    [string]$Time = "08:00",
    [string]$Slot = "morning_1",
    [string]$OperationId = "op_b2_demo_001"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot "resolve-b1-python.ps1")
$pythonPath = Resolve-B1Python

Push-Location $repoRoot
try {
    & $pythonPath -m rpg_agent `
        --date $Date `
        --time $Time `
        --slot $Slot `
        --operation-id $OperationId
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
