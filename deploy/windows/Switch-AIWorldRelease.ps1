param(
    [Parameter(Mandatory = $true)]
    [string]$ReleasePath,
    [Parameter(Mandatory = $true)]
    [string]$CurrentLink,
    [string]$PythonPath = "python",
    [switch]$ManageTasks,
    [switch]$ConfirmSwitch
)

$ErrorActionPreference = "Stop"
if (-not $ConfirmSwitch) {
    throw "Set -ConfirmSwitch after reading rollback-runbook.md"
}
$release = (Resolve-Path -LiteralPath $ReleasePath).Path
$current = [IO.Path]::GetFullPath($CurrentLink)
$parent = Split-Path -Parent $current
if (-not (Test-Path -LiteralPath $parent)) {
    throw "Current link parent directory is missing"
}

$verifyBootstrap = "import sys; sys.path.insert(0, r'$release'); from rpg_deploy.__main__ import main; raise SystemExit(main())"
$verifyOutput = & $PythonPath -c $verifyBootstrap verify --release $release
if ($LASTEXITCODE -ne 0) {
    throw "Release verification failed: $verifyOutput"
}

$next = "$current.next"
$previous = "$current.previous"
if (Test-Path -LiteralPath $next) {
    throw "Staging junction already exists: $next"
}
if ($ManageTasks) {
    Stop-ScheduledTask -TaskName "AIWorld-API" -ErrorAction SilentlyContinue
    Stop-ScheduledTask -TaskName "AIWorld-Scheduler" -ErrorAction SilentlyContinue
}

try {
    New-Item -ItemType Junction -Path $next -Target $release | Out-Null
    if (Test-Path -LiteralPath $current) {
        if (Test-Path -LiteralPath $previous) {
            throw "Previous junction already exists: $previous"
        }
        Rename-Item -LiteralPath $current -NewName (Split-Path -Leaf $previous)
    }
    Rename-Item -LiteralPath $next -NewName (Split-Path -Leaf $current)
    if ($ManageTasks) {
        Start-ScheduledTask -TaskName "AIWorld-API"
        Start-ScheduledTask -TaskName "AIWorld-Scheduler"
    }
    Write-Output "Activated release $release at $current"
}
catch {
    if (
        -not (Test-Path -LiteralPath $current) -and
        (Test-Path -LiteralPath $previous)
    ) {
        Rename-Item -LiteralPath $previous `
            -NewName (Split-Path -Leaf $current)
    }
    if ($ManageTasks) {
        Start-ScheduledTask -TaskName "AIWorld-API" -ErrorAction SilentlyContinue
        Start-ScheduledTask -TaskName "AIWorld-Scheduler" -ErrorAction SilentlyContinue
    }
    throw
}
