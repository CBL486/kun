param(
    [string]$RootPath,
    [string]$PythonPath = "python",
    [string]$EnvironmentFile,
    [string]$BackupDirectory
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
$logDirectory = Join-Path $root "logs"
New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null
Set-Location $root

& $PythonPath -m rpg_release backup `
    --url $databaseUrl `
    --output $output `
    *>> (Join-Path $logDirectory "backup.log")
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
& $PythonPath -m rpg_release verify-backup `
    --backup $output `
    *>> (Join-Path $logDirectory "backup.log")
exit $LASTEXITCODE
