$ErrorActionPreference = "Stop"
& (Join-Path $PSScriptRoot "test-b10.ps1")
exit $LASTEXITCODE
