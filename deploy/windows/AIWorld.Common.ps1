function Import-AIWorldEnvironment {
    param([string]$Path)
    if (-not $Path) {
        return
    }
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Environment file not found: $Path"
    }
    foreach ($line in Get-Content -LiteralPath $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#")) {
            continue
        }
        $parts = $trimmed.Split("=", 2)
        if ($parts.Count -ne 2) {
            throw "Invalid environment line"
        }
        [Environment]::SetEnvironmentVariable(
            $parts[0].Trim(),
            $parts[1],
            "Process"
        )
    }
}

function Resolve-AIWorldRoot {
    param([string]$RootPath)
    if (-not $RootPath) {
        return (Split-Path -Parent $PSScriptRoot)
    }
    return (Resolve-Path -LiteralPath $RootPath).Path
}
