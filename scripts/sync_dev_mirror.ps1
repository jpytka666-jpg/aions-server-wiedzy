<#
.SYNOPSIS
  One-way sync: E:\server wiedzy -> D:\AIONS_DEV\repo\server-wiedzy (dev mirror for WSL/Linux).

.DESCRIPTION
  Uses robocopy on Windows. Excludes venv, ChromaDB, scan artifacts, Python cache, and .git
  when the destination is a separate clone.

.PARAMETER Source
  Canonical working tree on E: (default).

.PARAMETER Destination
  Dev mirror path on D: (default).

.PARAMETER DryRun
  List files that would be copied; print summary counts without writing.

.PARAMETER Mirror
  Delete files in destination that no longer exist in source (/MIR). Use with care.

.PARAMETER IncludeGit
  Copy .git directory (default: excluded — destination is usually a separate clone).

.EXAMPLE
  .\scripts\sync_dev_mirror.ps1 -DryRun

.EXAMPLE
  .\scripts\sync_dev_mirror.ps1
#>
param(
    [string]$Source = "E:\server wiedzy",
    [string]$Destination = "D:\AIONS_DEV\repo\server-wiedzy",
    [switch]$DryRun,
    [switch]$Mirror,
    [switch]$IncludeGit
)

$ErrorActionPreference = "Stop"

function Resolve-RepoPath {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Path does not exist: $Path"
    }
    return (Resolve-Path -LiteralPath $Path).Path
}

$sourcePath = Resolve-RepoPath $Source
$destParent = Split-Path -Parent $Destination
if (-not (Test-Path -LiteralPath $destParent)) {
    New-Item -ItemType Directory -Path $destParent -Force | Out-Null
}
if (-not (Test-Path -LiteralPath $Destination)) {
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
}
$destPath = (Resolve-Path -LiteralPath $Destination).Path

# Name-based /XD matches every directory with that name in the tree (e.g. nested venv/).
$excludeDirNames = @("venv", "__pycache__", "scan_results")
$excludeDirPaths = @(
    (Join-Path $sourcePath "data\chroma")
)
if (-not $IncludeGit) {
    $excludeDirPaths += (Join-Path $sourcePath ".git")
}

$robocopyArgs = @(
    $sourcePath,
    $destPath,
    "/E",
    "/COPY:DAT",
    "/R:2",
    "/W:3",
    "/MT:8"
)
foreach ($name in $excludeDirNames) {
    $robocopyArgs += "/XD"
    $robocopyArgs += $name
}
foreach ($dir in $excludeDirPaths) {
    $robocopyArgs += "/XD"
    $robocopyArgs += $dir
}
if ($Mirror) {
    $robocopyArgs += "/MIR"
}
if ($DryRun) {
    $robocopyArgs += "/L"
    Write-Host "=== DRY-RUN: no files will be copied ===" -ForegroundColor Cyan
}
else {
    $robocopyArgs += "/NFL"
    $robocopyArgs += "/NDL"
    Write-Host "=== Syncing dev mirror ===" -ForegroundColor Green
}

Write-Host "Source:      $sourcePath"
Write-Host "Destination: $destPath"
Write-Host "Excluded:    venv, data\chroma, scan_results, __pycache__$(if (-not $IncludeGit) { ', .git' })"
Write-Host ""

& robocopy @robocopyArgs
$exitCode = $LASTEXITCODE

# Robocopy: 0-7 = success (with informational flags), >= 8 = failure
if ($exitCode -ge 8) {
    throw "robocopy failed with exit code $exitCode"
}

if ($DryRun) {
    Write-Host ""
    Write-Host "Dry-run finished (robocopy exit $exitCode). Review the summary above:" -ForegroundColor Cyan
    Write-Host "  Files : ... Copied  = would be copied/updated"
    Write-Host "  Dirs  : ... Copied  = would be created/updated"
    Write-Host "  Extras = already in destination but not in source (use -Mirror to remove)"
}
else {
    Write-Host ""
    Write-Host "Sync complete (robocopy exit $exitCode)." -ForegroundColor Green
}

exit 0
