<#
.SYNOPSIS
    Stop ChromaDB HTTP Server

.PARAMETER Port
    Port to find and kill (default: 8000)
#>

param(
    [int]$Port = 8000
)

Write-Host "[CHROMADB] Looking for process on port $Port..." -ForegroundColor Yellow

# Find PID using the port
$netstatOutput = netstat -ano | Select-String ":$Port\s.*LISTENING"

if (-not $netstatOutput) {
    Write-Host "[CHROMADB] No process found listening on port $Port" -ForegroundColor Gray
    exit 0
}

# Extract PID
$line = $netstatOutput.Line.Trim()
$pid = ($line -split '\s+')[-1]

if ($pid -and $pid -match '^\d+$') {
    Write-Host "[CHROMADB] Found process PID: $pid" -ForegroundColor Yellow
    try {
        Stop-Process -Id $pid -Force
        Write-Host "[CHROMADB] Process $pid stopped successfully" -ForegroundColor Green
    } catch {
        Write-Host "[CHROMADB] Failed to stop process: $_" -ForegroundColor Red
    }
} else {
    Write-Host "[CHROMADB] Could not extract PID from: $line" -ForegroundColor Red
}
