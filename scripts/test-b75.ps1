param(
    [switch]$Rebuild
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

$nodeCommand = Get-Command node -ErrorAction SilentlyContinue
if ($nodeCommand) {
    $nodePath = $nodeCommand.Source
}
else {
    $bundledNode = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
    if (Test-Path -LiteralPath $bundledNode) {
        $nodePath = $bundledNode
    }
}

Push-Location $repoRoot
try {
    if ($Rebuild) {
        & (Join-Path $PSScriptRoot "build-b75-assets.ps1")
        if ($LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }
    }
    & $pythonPath -m pytest -q
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
    if ($nodePath) {
        & $nodePath --check web/app.js
        if ($LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }
        & $nodePath --check web/spine-player.js
        if ($LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }
    }
    & $pythonPath scripts/check_b75_visual.py
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
    exit 0
}
finally {
    Pop-Location
}
