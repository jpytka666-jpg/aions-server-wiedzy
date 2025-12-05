param(
  [string]$OutputDir = "logs/context_dumps",
  [switch]$PruneOnDump
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $repoRoot 'venv'

if (Test-Path (Join-Path $venv 'Scripts\Activate.ps1')) {
  . (Join-Path $venv 'Scripts\Activate.ps1')
}

if (-not $env:PYTHONPATH -or -not ($env:PYTHONPATH.Split([IO.Path]::PathSeparator) -contains $repoRoot)) {
  $env:PYTHONPATH = if ($env:PYTHONPATH) { "$repoRoot$([IO.Path]::PathSeparator)$env:PYTHONPATH" } else { $repoRoot }
}

if (-not $env:CHROMA_PATH) {
  $env:CHROMA_PATH = Join-Path $repoRoot 'data\chroma'
}

$targetDir = if ([System.IO.Path]::IsPathRooted($OutputDir)) { $OutputDir } else { Join-Path $repoRoot $OutputDir }
if (-not (Test-Path $targetDir)) {
  New-Item -ItemType Directory -Path $targetDir | Out-Null
}
$resolved = Resolve-Path -LiteralPath $targetDir

$argsDump = @('dump','--output', $resolved)
python context_admin.py @argsDump

if ($PruneOnDump) {
  # Prune each session individually after snapshot
  $sessionsJson = python context_admin.py list
  $sessions = ($sessionsJson | ConvertFrom-Json).sessions
  foreach ($s in $sessions) {
    python context_admin.py prune $s.session_id | Out-Null
  }
}
