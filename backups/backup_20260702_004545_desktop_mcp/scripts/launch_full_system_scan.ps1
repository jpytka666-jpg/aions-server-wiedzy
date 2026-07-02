# Detached full-system scan - all drives, independent of Cursor/MCP
$ErrorActionPreference = "Continue"
$Repo = "E:\server wiedzy"
$Python = Join-Path $Repo "venv\Scripts\python.exe"
$Script = Join-Path $Repo "scripts\full_system_scan.py"
$PidFile = Join-Path $Repo "logs\full_system_scan.pid"
$StatusFile = Join-Path $Repo "logs\full_system_scan_status.json"

if (-not (Test-Path $Python)) {
    Write-Error "Python venv not found: $Python"
    exit 1
}

$existing = Get-Content $PidFile -ErrorAction SilentlyContinue
if ($existing) {
    $proc = Get-Process -Id $existing -ErrorAction SilentlyContinue
    if ($proc) {
        Write-Host "Full system scan already running (PID $existing)"
        Write-Host "Status: $StatusFile"
        exit 0
    }
}

$log = Join-Path $Repo "logs\full_system_scan_launcher.log"
$ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content $log "`n[$ts] Starting detached full system scan"

$p = Start-Process -FilePath $Python `
    -ArgumentList @("-u", $Script) `
    -WorkingDirectory $Repo `
    -WindowStyle Hidden `
    -PassThru

$p.Id | Set-Content $PidFile -Encoding ascii
Add-Content $log "[$ts] PID $($p.Id)"
Write-Host "Full system scan started in background (PID $($p.Id))"
Write-Host "Status: $StatusFile"
