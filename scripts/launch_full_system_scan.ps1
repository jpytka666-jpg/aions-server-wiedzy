# Detached full-system scan - configurable drive order, independent of Cursor/MCP
param(
    # F: is the backing/home volume for the Dev Drive on D:, so skip it by default.
    [string]$Drives = "D,E,C"
)
$ErrorActionPreference = "Continue"
$Repo = "E:\server wiedzy"
$Python = & (Join-Path $Repo "scripts\aions_python.ps1") -ResolveOnly
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
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

$log = Join-Path $Repo "logs\full_system_scan_launcher.log"
$ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content $log "`n[$ts] Starting detached full system scan drives=$Drives"

$args = @("-u", $Script)
if ($Drives) {
    $args += @("--drives", $Drives)
}

$p = Start-Process -FilePath $Python `
    -ArgumentList $args `
    -WorkingDirectory $Repo `
    -WindowStyle Hidden `
    -PassThru

$p.Id | Set-Content $PidFile -Encoding ascii
Add-Content $log "[$ts] PID $($p.Id)"
Write-Host "Full system scan started in background (PID $($p.Id))"
Write-Host "Status: $StatusFile"
