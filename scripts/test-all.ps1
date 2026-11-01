$ErrorActionPreference = "Stop"
& (Join-Path $PSScriptRoot "test-b13.ps1")
exit $LASTEXITCODE
