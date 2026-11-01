param(
    [string]$LogDirectory,
    [int]$MaxSizeMB = 20,
    [int]$RetentionDays = 14
)

$ErrorActionPreference = "Stop"
if (-not $LogDirectory -or -not (Test-Path -LiteralPath $LogDirectory)) {
    throw "Log directory not found"
}
$cutoff = (Get-Date).AddDays(-$RetentionDays)
Get-ChildItem -LiteralPath $LogDirectory -File -Filter "*.log.*" |
    Where-Object { $_.LastWriteTime -lt $cutoff } |
    Remove-Item -Force

$maximumBytes = $MaxSizeMB * 1MB
Get-ChildItem -LiteralPath $LogDirectory -File -Filter "*.log" |
    Where-Object { $_.Length -ge $maximumBytes } |
    ForEach-Object {
        $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $destination = Join-Path $LogDirectory (
            "{0}.{1}.log" -f $_.BaseName, $timestamp
        )
        Move-Item -LiteralPath $_.FullName -Destination $destination
    }
