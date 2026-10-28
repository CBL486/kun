param(
    [Parameter(Mandatory = $true)]
    [string]$Url,
    [ValidateSet("migrate", "rollback", "version")]
    [string]$Command = "version",
    [switch]$ConfirmRollback
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot "resolve-b1-python.ps1")
$pythonPath = Resolve-B1Python

$dependencyPath = Join-Path $repoRoot ".b5-deps"
if (Test-Path -LiteralPath $dependencyPath) {
    $separator = [System.IO.Path]::PathSeparator
    $env:PYTHONPATH = $dependencyPath + $separator + $env:PYTHONPATH
}

Push-Location $repoRoot
try {
    $arguments = @(
        "-m", "rpg_orm",
        $Command,
        "--url", $Url
    )
    if ($ConfirmRollback) {
        $arguments += "--confirm-rollback"
    }
    & $pythonPath @arguments
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
