$ErrorActionPreference = "Stop"
& (Join-Path $PSScriptRoot "test-b11.ps1")
exit $LASTEXITCODE
