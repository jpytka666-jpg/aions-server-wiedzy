param(
  [ValidateSet("stdio","http")]
  [string]$Transport = "stdio"
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot

# ENCODING FIX - force UTF-8 everywhere
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
$env:PYTHONUNBUFFERED = '1'

$venv = Join-Path $repoRoot 'venv'

# Use ONLY venv Python - do not mix with system Python
$pythonExe = Join-Path $venv 'Scripts\python.exe'
if (-not (Test-Path $pythonExe)) {
  throw "Python interpreter not found at $pythonExe. Run: python -m venv venv"
}

# Activate venv
$activateScript = Join-Path $venv 'Scripts\Activate.ps1'
if (Test-Path $activateScript) {
  . $activateScript
}

# Set PYTHONPATH to include repo root
$env:PYTHONPATH = $repoRoot

# Set ChromaDB path
if (-not $env:CHROMA_PATH) {
  $env:CHROMA_PATH = Join-Path $repoRoot 'data\chroma'
}

# Disable ChromaDB telemetry (reduces stderr noise)
$env:ANONYMIZED_TELEMETRY = 'False'
$env:CHROMA_TELEMETRY_ENABLED = 'false'

# Set AIONS path for CBMS integration
$env:AIONS_V10_PATH = 'E:\AIONS_V10\AIONS_CBMS_RELEASE_V3'

# Run the MCP server
$serverDir = Join-Path $repoRoot 'mcpServers\VS_CODE_MCP_CODEX'
Push-Location $serverDir
try {
  & $pythonExe -X utf8 -m src $Transport
}
finally {
  Pop-Location
}
