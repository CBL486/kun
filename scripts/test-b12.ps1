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
    & $pythonPath -m rpg_quality --output out/b12/e2e-report.json
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
    & $pythonPath -m rpg_stress --output out/b12/cost-report.json
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
    & $pythonPath -m rpg_deploy config-check
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
    $releasePath = Join-Path $repoRoot (
        "out/b12/release-" + [guid]::NewGuid().ToString("N")
    )
    & $pythonPath -m rpg_deploy build `
        --output $releasePath `
        --built-at "2026-11-01T00:00:00Z"
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
    & $pythonPath -m rpg_deploy verify --release $releasePath
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
