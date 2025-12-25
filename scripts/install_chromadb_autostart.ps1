<#
.SYNOPSIS
    Install ChromaDB HTTP Server as Windows Scheduled Task (autostart on login)

.DESCRIPTION
    Creates a scheduled task that starts ChromaDB server when user logs in.
    Runs BEFORE AIONS Knowledge Server (which depends on it).

.PARAMETER Port
    HTTP port (default: 8000)

.PARAMETER TaskName
    Scheduled task name (default: ChromaDB_HTTP_Server)
#>

param(
    [int]$Port = 8000,
    [string]$TaskName = 'ChromaDB_HTTP_Server'
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $root 'venv'
$chromaExe = Join-Path $venv 'Scripts\chroma.exe'
$chromaPath = Join-Path $root 'data\chroma'
$logDir = Join-Path $root 'logs'

# Verify chroma exists
if (-not (Test-Path $chromaExe)) {
    throw "ChromaDB not found at $chromaExe. Install it first: pip install chromadb"
}

# Ensure directories exist
if (-not (Test-Path $chromaPath)) {
    New-Item -ItemType Directory -Path $chromaPath -Force | Out-Null
}
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# Create a batch wrapper (scheduled tasks work better with batch files)
$wrapperPath = Join-Path $root 'scripts\chromadb_server_wrapper.cmd'
$wrapperContent = @"
@echo off
REM ChromaDB HTTP Server Wrapper for Scheduled Task
cd /d "$root"
"$chromaExe" run --host 0.0.0.0 --port $Port --path "$chromaPath"
"@
Set-Content -Path $wrapperPath -Value $wrapperContent -Encoding ASCII

Write-Host "[AUTOSTART] Created wrapper: $wrapperPath" -ForegroundColor Gray

# Create scheduled task
$action = New-ScheduledTaskAction -Execute $wrapperPath -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -AtLogOn
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -RestartCount 3 `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0)  # No time limit

try {
    # Remove existing task if present
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue | Out-Null
        Write-Host "[AUTOSTART] Removed existing task: $TaskName" -ForegroundColor Yellow
    }

    # Register new task
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Description "Start ChromaDB HTTP Server on user logon (AIONS Knowledge System)" `
        -Action $action `
        -Trigger $trigger `
        -Principal $principal `
        -Settings $settings | Out-Null

    Write-Host "=============================================" -ForegroundColor Green
    Write-Host "  CHROMADB AUTOSTART INSTALLED" -ForegroundColor Green
    Write-Host "=============================================" -ForegroundColor Green
    Write-Host "[AUTOSTART] Task name:  $TaskName" -ForegroundColor Gray
    Write-Host "[AUTOSTART] Port:       $Port" -ForegroundColor Gray
    Write-Host "[AUTOSTART] Data path:  $chromaPath" -ForegroundColor Gray
    Write-Host "[AUTOSTART] Trigger:    At user logon" -ForegroundColor Gray
    Write-Host "=============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "To start now:   schtasks /run /tn `"$TaskName`"" -ForegroundColor Cyan
    Write-Host "To uninstall:   .\uninstall_chromadb_autostart.ps1" -ForegroundColor Cyan
}
catch {
    Write-Warning "[AUTOSTART] Scheduled task registration failed: $($_.Exception.Message)"
    Write-Host "[AUTOSTART] Falling back to Startup folder..." -ForegroundColor Yellow

    $startup = [Environment]::GetFolderPath('Startup')
    $shortcutPath = Join-Path $startup 'ChromaDB_Server.lnk'

    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $wrapperPath
    $shortcut.WorkingDirectory = $root
    $shortcut.WindowStyle = 7  # Minimized
    $shortcut.Description = "ChromaDB HTTP Server"
    $shortcut.Save()

    Write-Host "[AUTOSTART] Created startup shortcut: $shortcutPath" -ForegroundColor Green
}
