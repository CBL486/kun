$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot "resolve-b1-python.ps1")
$pythonPath = Resolve-B1Python

Push-Location $repoRoot
try {
    & $pythonPath -m unittest tests.test_b1_simulator tests.test_b2_agent_core -v
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
    git diff --check
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
