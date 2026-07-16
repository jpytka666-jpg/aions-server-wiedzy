#Requires -Version 5.1
<#
.SYNOPSIS
  Local probe: AIONS MCP server system_health() via venv Python.

.DESCRIPTION
  Exit 0 when system_health returns status ok; exit 1 otherwise.
  Does NOT verify the Cursor MCP transport — if Cursor shows MCP errors,
  reload aions-context / aions-dev in Cursor Settings > MCP.

.EXAMPLE
  .\scripts\check_aions_mcp_health.ps1
#>
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$launcher = Join-Path $PSScriptRoot 'aions_python.ps1'

$pyCode = @"
import json
import os
import sys

ROOT = r'$repoRoot'
sys.path.insert(0, os.path.join(ROOT, 'mcpServers', 'VS_CODE_MCP_CODEX'))
os.environ.setdefault('CHROMA_PATH', os.path.join(ROOT, 'data', 'chroma'))

from src.server import system_health

raw = system_health()
print(raw)
data = json.loads(raw)
sys.exit(0 if data.get('status') == 'ok' else 1)
"@

& $launcher -c $pyCode
exit $LASTEXITCODE
