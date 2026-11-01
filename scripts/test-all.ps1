$ErrorActionPreference = "Stop"
& (Join-Path $PSScriptRoot "test-b12.ps1")
exit $LASTEXITCODE
