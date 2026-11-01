param(
    [Parameter(Mandatory = $true)]
    [string]$Backup,
    [Parameter(Mandatory = $true)]
    [string]$Url,
    [string]$PgBin,
    [switch]$ConfirmRestore
)

$ErrorActionPreference = "Stop"
if (-not $ConfirmRestore) {
    throw "Set -ConfirmRestore after verifying the backup and recovery window"
}
$repoRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot "resolve-b1-python.ps1")
$pythonPath = Resolve-B1Python
$dependencyPath = Join-Path $repoRoot ".b6-deps"
if (Test-Path -LiteralPath $dependencyPath) {
    $separator = [System.IO.Path]::PathSeparator
    $env:PYTHONPATH = $dependencyPath + $separator + $env:PYTHONPATH
}
$arguments = @(
    "-m", "rpg_release", "restore",
    "--backup", $Backup,
    "--url", $Url,
    "--confirm-restore"
)
if ($PgBin) {
    $arguments += @("--pg-bin", $PgBin)
}
Push-Location $repoRoot
try {
    & $pythonPath @arguments
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
