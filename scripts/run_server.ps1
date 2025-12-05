param(
  [int]$Port = 8765,
  [string]$BindHost = "127.0.0.1",
  [switch]$Foreground
)

$ErrorActionPreference = 'SilentlyContinue'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$venv = Join-Path $root 'venv'
$env:PYTHONPATH = $root
# Disable noisy Chroma telemetry logs
$env:CHROMA_TELEMETRY_ENABLED = 'false'

if(Test-Path (Join-Path $venv 'Scripts\Activate.ps1')){ . (Join-Path $venv 'Scripts\Activate.ps1') }

$logDir = Join-Path $root 'logs'
if(!(Test-Path $logDir)){ New-Item -ItemType Directory -Path $logDir | Out-Null }
$logPath = Join-Path $logDir (Get-Date -Format 'yyyy-MM-dd')
if(!(Test-Path $logPath)){ New-Item -ItemType Directory -Path $logPath | Out-Null }
$logFile = Join-Path $logPath 'aions_knowledge_server.log'

Write-Host ("[SERVER] Starting AIONS Knowledge Server on http://{0}:{1}" -f $BindHost,$Port) -ForegroundColor Green
$py = Join-Path $venv 'Scripts\python.exe'
$uvArgs = @('-m','uvicorn','server.app:app','--host', $BindHost,'--port', "$Port",'--log-level','info')
if($Foreground){
  Write-Host "[SERVER] Running in foreground (integrated terminal). Ctrl+C to stop." -ForegroundColor Yellow
  & $py @uvArgs
} else {
  Start-Process -FilePath $py -ArgumentList $uvArgs -WorkingDirectory $root -RedirectStandardOutput $logFile -RedirectStandardError $logFile -WindowStyle Hidden | Out-Null
}
