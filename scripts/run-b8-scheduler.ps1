param(
    [ValidateSet("status", "recover", "enqueue-reconcile")]
    [string]$Command = "status",
    [string]$DatabaseUrl = "sqlite:///./data/b8.sqlite3",
    [string]$OperationId
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

$arguments = @("-m", "rpg_scheduler", $Command, "--url", $DatabaseUrl)
if ($OperationId) {
    $arguments += @("--operation-id", $OperationId)
}

Push-Location $repoRoot
try {
    & $pythonPath @arguments
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
