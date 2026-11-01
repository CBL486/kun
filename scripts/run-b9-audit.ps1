param(
    [string]$DatabaseUrl = "sqlite:///./data/b9.sqlite3",
    [string]$BudgetDate = "2026-11-01"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot "resolve-b1-python.ps1")
$pythonPath = Resolve-B1Python

$dependencyPath = Join-Path $repoRoot ".b6-deps"
if (Test-Path -LiteralPath $dependencyPath) {
    $separator = [System.IO.Path]::PathSeparator
    $env:PYTHONPATH = $dependencyPath + $separator + $env:PYTHONPATH
}

Push-Location $repoRoot
try {
    & $pythonPath -m rpg_llm `
        --url $DatabaseUrl `
        --budget-date $BudgetDate
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
