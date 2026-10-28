function Resolve-B1Python {
    $candidates = New-Object System.Collections.Generic.List[string]
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        $candidates.Add($pythonCommand.Source)
    }

    $bundledPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    if (Test-Path -LiteralPath $bundledPython) {
        $candidates.Add($bundledPython)
    }

    foreach ($candidate in ($candidates | Select-Object -Unique)) {
        try {
            $version = (& $candidate --version 2>&1 | Out-String).Trim()
            if ($LASTEXITCODE -eq 0 -and $version -match "^Python 3\.") {
                return $candidate
            }
        }
        catch {
            continue
        }
    }

    throw "找不到可用的 Python 3.11 或更高版本。"
}
