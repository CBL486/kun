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
    & $pythonPath -m pytest -q `
        tests/test_b4_persistence.py `
        tests/test_b5_postgres_contract.py `
        tests/test_b6_api.py `
        tests/test_b8_scheduler.py
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
