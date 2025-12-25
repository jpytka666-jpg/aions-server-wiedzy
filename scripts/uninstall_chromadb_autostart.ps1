<#
.SYNOPSIS
    Uninstall ChromaDB HTTP Server autostart

.PARAMETER TaskName
    Scheduled task name (default: ChromaDB_HTTP_Server)
#>

param(
    [string]$TaskName = 'ChromaDB_HTTP_Server'
)

$root = Split-Path -Parent $PSScriptRoot

# Remove scheduled task
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "[AUTOSTART] Removed scheduled task: $TaskName" -ForegroundColor Green
} else {
    Write-Host "[AUTOSTART] Scheduled task not found: $TaskName" -ForegroundColor Gray
}

# Remove startup shortcut if exists
$startup = [Environment]::GetFolderPath('Startup')
$shortcutPath = Join-Path $startup 'ChromaDB_Server.lnk'
if (Test-Path $shortcutPath) {
    Remove-Item $shortcutPath -Force
    Write-Host "[AUTOSTART] Removed startup shortcut: $shortcutPath" -ForegroundColor Green
}

# Remove wrapper script
$wrapperPath = Join-Path $root 'scripts\chromadb_server_wrapper.cmd'
if (Test-Path $wrapperPath) {
    Remove-Item $wrapperPath -Force
    Write-Host "[AUTOSTART] Removed wrapper: $wrapperPath" -ForegroundColor Green
}

Write-Host "[AUTOSTART] ChromaDB autostart uninstalled" -ForegroundColor Green
