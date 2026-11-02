param(
    [string]$RootPath,
    [string]$PythonPath = "python",
    [string]$EnvironmentFile,
    [string]$BackupDirectory,
    [string]$PgBin
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "AIWorld.Common.ps1")
Import-AIWorldEnvironment -Path $EnvironmentFile
$root = Resolve-AIWorldRoot -RootPath $RootPath
$databaseUrl = $env:AIWORLD_BACKUP_DATABASE_URL
if (-not $databaseUrl) {
    throw "AIWORLD_BACKUP_DATABASE_URL is required"
}
if (-not $BackupDirectory) {
    $BackupDirectory = Join-Path $root "backups"
}
New-Item -ItemType Directory -Force -Path $BackupDirectory | Out-Null
$stamp = [DateTimeOffset]::UtcNow.ToString("yyyyMMddTHHmmssZ")
$extension = if ($databaseUrl.StartsWith("sqlite")) { ".sqlite3" } else { ".dump" }
$output = Join-Path $BackupDirectory "aiworld-$stamp$extension"
if (-not $PgBin) {
    $PgBin = Join-Path (Split-Path -Parent $PythonPath) "Lib\site-packages\embedded_postgres\pginstall\bin"
}
$logDirectory = Join-Path $root "logs"
New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null
Set-Location $root
$env:AIWORLD_ROOT = $root

& $PythonPath (Join-Path $PSScriptRoot "run_module.py") rpg_release backup `
    --url $databaseUrl `
    --output $output `
    --pg-bin $PgBin `
    *>> (Join-Path $logDirectory "backup.log")
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
& $PythonPath (Join-Path $PSScriptRoot "run_module.py") rpg_release verify-backup `
    --backup $output `
    *>> (Join-Path $logDirectory "backup.log")
exit $LASTEXITCODE
