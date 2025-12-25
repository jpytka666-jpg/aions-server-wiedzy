<#
.SYNOPSIS
    Start ChromaDB HTTP Server for AIONS Knowledge System

.DESCRIPTION
    Runs ChromaDB as HTTP server on port 8000.
    All clients (MCP aions-context, AIONS Knowledge Server, TS MCP server) connect here.

.PARAMETER Port
    HTTP port (default: 8000)

.PARAMETER Host
    Bind host (default: 0.0.0.0 for all interfaces)

.PARAMETER Foreground
    Run in foreground (don't detach)

.EXAMPLE
    .\start_chromadb_server.ps1
    .\start_chromadb_server.ps1 -Port 8000 -Foreground
#>

param(
    [int]$Port = 8000,
    [string]$Host = "0.0.0.0",
    [switch]$Foreground
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $root 'venv'
$chromaPath = Join-Path $root 'data\chroma'

# Ensure data directory exists
if (-not (Test-Path $chromaPath)) {
    New-Item -ItemType Directory -Path $chromaPath -Force | Out-Null
    Write-Host "[CHROMADB] Created data directory: $chromaPath" -ForegroundColor Yellow
}

# Check if port is already in use
$portCheck = netstat -ano | Select-String ":$Port\s"
if ($portCheck) {
    Write-Host "[CHROMADB] Port $Port is already in use!" -ForegroundColor Red
    Write-Host $portCheck
    exit 1
}

# Find chroma executable
$chromaExe = Join-Path $venv 'Scripts\chroma.exe'
if (-not (Test-Path $chromaExe)) {
    Write-Host "[CHROMADB] chroma.exe not found at $chromaExe" -ForegroundColor Red
    Write-Host "[CHROMADB] Installing chromadb..." -ForegroundColor Yellow
    & (Join-Path $venv 'Scripts\pip.exe') install chromadb
    if (-not (Test-Path $chromaExe)) {
        throw "Failed to install chromadb"
    }
}

# Prepare log directory
$logDir = Join-Path $root 'logs'
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}
$logFile = Join-Path $logDir 'chromadb_server.log'

# Build arguments
$chromaArgs = @('run', '--host', $Host, '--port', "$Port", '--path', $chromaPath)

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  CHROMADB HTTP SERVER" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "[CHROMADB] Executable: $chromaExe" -ForegroundColor Gray
Write-Host "[CHROMADB] Data path:  $chromaPath" -ForegroundColor Gray
Write-Host "[CHROMADB] URL:        http://${Host}:${Port}" -ForegroundColor Green
Write-Host "[CHROMADB] Log file:   $logFile" -ForegroundColor Gray
Write-Host "=============================================" -ForegroundColor Cyan

if ($Foreground) {
    Write-Host "[CHROMADB] Running in foreground. Press Ctrl+C to stop." -ForegroundColor Yellow
    & $chromaExe @chromaArgs
} else {
    Write-Host "[CHROMADB] Starting in background..." -ForegroundColor Yellow
    $process = Start-Process -FilePath $chromaExe `
        -ArgumentList $chromaArgs `
        -WorkingDirectory $root `
        -RedirectStandardOutput $logFile `
        -RedirectStandardError $logFile `
        -WindowStyle Hidden `
        -PassThru

    Start-Sleep -Seconds 2

    # Verify it started
    $portCheck = netstat -ano | Select-String ":$Port\s.*LISTENING"
    if ($portCheck) {
        Write-Host "[CHROMADB] Server started successfully! PID: $($process.Id)" -ForegroundColor Green
        Write-Host "[CHROMADB] Test: curl http://localhost:$Port/api/v1/heartbeat" -ForegroundColor Gray
    } else {
        Write-Host "[CHROMADB] Server may have failed to start. Check log: $logFile" -ForegroundColor Red
        Get-Content $logFile -Tail 20
    }
}
