param(
    [string]$SourceRoot = $env:B75_SOURCE_ROOT
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not $SourceRoot) {
    throw "重建资源需要设置 B75_SOURCE_ROOT，并指向本地私密素材解压目录。"
}
$resolvedSourceRoot = (Resolve-Path -LiteralPath $SourceRoot).Path
$env:B75_SOURCE_ROOT = $resolvedSourceRoot

. (Join-Path $PSScriptRoot "resolve-b1-python.ps1")
$pythonPath = Resolve-B1Python

$dependencyPath = Join-Path $repoRoot ".b6-deps"
if (Test-Path -LiteralPath $dependencyPath) {
    $separator = [System.IO.Path]::PathSeparator
    $env:PYTHONPATH = $dependencyPath + $separator + $env:PYTHONPATH
}

Push-Location $repoRoot
try {
    & $pythonPath scripts/build_b75_assets.py
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
    & $pythonPath scripts/build_spine_assets.py
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
