param(
    [Parameter(Mandatory = $true)]
    [string]$Output,
    [string]$Version,
    [string]$BuiltAt
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
$arguments = @("-m", "rpg_deploy", "build", "--output", $Output)
if ($Version) {
    $arguments += @("--version", $Version)
}
if ($BuiltAt) {
    $arguments += @("--built-at", $BuiltAt)
}
Push-Location $repoRoot
try {
    & $pythonPath @arguments
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
