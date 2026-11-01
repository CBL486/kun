param(
    [Parameter(Mandatory = $true)]
    [string]$TargetRelease,
    [Parameter(Mandatory = $true)]
    [string]$CurrentLink,
    [string]$PythonPath = "python",
    [switch]$ManageTasks,
    [switch]$ConfirmRollback
)

$ErrorActionPreference = "Stop"
if (-not $ConfirmRollback) {
    throw "Set -ConfirmRollback after reading rollback-runbook.md"
}
$repoRoot = Split-Path -Parent $PSScriptRoot
$switchScript = Join-Path $repoRoot "deploy\windows\Switch-AIWorldRelease.ps1"
& $switchScript `
    -ReleasePath $TargetRelease `
    -CurrentLink $CurrentLink `
    -PythonPath $PythonPath `
    -ManageTasks:$ManageTasks `
    -ConfirmSwitch
exit $LASTEXITCODE
