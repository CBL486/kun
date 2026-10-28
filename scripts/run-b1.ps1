param(
    [string]$Output = "out/b1",
    [int]$Seed = 20261028,
    [int]$PauseAfter = 0,
    [switch]$Resume
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot "resolve-b1-python.ps1")
$pythonPath = Resolve-B1Python

Push-Location $repoRoot
try {
    $arguments = @(
        "-m", "rpg_sim", "seven-day",
        "--scenario", "slice-seven-day-v1",
        "--seed", "$Seed",
        "--mode", "rule_only",
        "--frozen-clock",
        "--output", $Output
    )
    if ($PauseAfter -gt 0) {
        $arguments += @("--pause-after", "$PauseAfter")
    }
    if ($Resume) {
        $arguments += "--resume"
    }
    & $pythonPath @arguments
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
