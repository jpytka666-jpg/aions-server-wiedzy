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

# Use ONLY venv Python via aions_python launcher — never bare python
$launcher = Join-Path $PSScriptRoot 'aions_python.ps1'
if (-not (Test-Path $launcher)) {
  throw "AIONS Python launcher not found: $launcher"
}
$pythonExe = & $launcher -ResolveOnly
if (-not $pythonExe -or -not (Test-Path $pythonExe)) {
  throw "AIONS venv Python not resolved. Run: scripts\ensure_venv.ps1"
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
