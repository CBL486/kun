param([switch]$ConfirmRemoval)

$ErrorActionPreference = "Stop"
if (-not $ConfirmRemoval) {
    throw "Set -ConfirmRemoval to unregister AI World tasks"
}
foreach ($name in "AIWorld-API", "AIWorld-Scheduler", "AIWorld-Backup", "AIWorld-LogRotation") {
    $task = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    if ($task) {
        Stop-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
        Unregister-ScheduledTask -TaskName $name -Confirm:$false
    }
}
