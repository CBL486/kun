param(
    [string]$Database = "out/b4/world.db",
    [ValidateSet("migrate", "rollback", "version")]
    [string]$Command = "migrate",
    [int]$TargetVersion = 0
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot "resolve-b1-python.ps1")
$pythonPath = Resolve-B1Python

Push-Location $repoRoot
try {
    & $pythonPath -m rpg_storage $Command `
        --database $Database `
        --target-version $TargetVersion
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
