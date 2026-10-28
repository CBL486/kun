param(
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 8080
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
    & $pythonPath -m uvicorn app.main:app --host $HostAddress --port $Port
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
