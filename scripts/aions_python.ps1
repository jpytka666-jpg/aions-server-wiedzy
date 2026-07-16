#Requires -Version 5.1
<#
.SYNOPSIS
    AIONS Python launcher (Windows) — resolves correct venv interpreter from .aions/python.env
.DESCRIPTION
    Nigdy nie wołaj bare `python` w AIONS. Użyj tego skryptu lub start_aions_mcp.bat.
.EXAMPLE
    .\aions_python.ps1 -ResolveOnly
    .\aions_python.ps1 scripts\verify_python_env.py
    .\aions_python.ps1 -EnsureVenv
#>
param(
    [switch]$ResolveOnly,
    [switch]$EnsureVenv,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PythonArgs
)

$ErrorActionPreference = 'Stop'

function Get-AionsRepoRoot {
    $scriptDir = Split-Path -Parent $PSScriptRoot
    if (Test-Path (Join-Path $scriptDir '.aions\python.env')) {
        return (Resolve-Path $scriptDir).Path
    }
    throw "[AIONS] Nie znaleziono .aions\python.env (oczekiwano w $scriptDir)"
}

function Read-AionsPythonConfig {
    param([string]$RepoRoot)
    $configPath = Join-Path $RepoRoot '.aions\python.env'
    if (-not (Test-Path $configPath)) {
        throw "[AIONS] Brak pliku konfiguracji: $configPath"
    }
    $cfg = @{}
    Get-Content $configPath -Encoding UTF8 | ForEach-Object {
        $line = $_.Trim()
        if ($line -eq '' -or $line.StartsWith('#')) { return }
        $idx = $line.IndexOf('=')
        if ($idx -lt 1) { return }
        $key = $line.Substring(0, $idx).Trim()
        $val = $line.Substring($idx + 1).Trim()
        $cfg[$key] = $val
    }
    return $cfg
}

function Test-AionsPythonVersion {
    param(
        [string]$PythonExe,
        [string]$ExpectedVersion
    )
    $out = & $PythonExe -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "[AIONS] Nie można odczytać wersji Pythona: $PythonExe`n$out"
    }
    $actual = "$out".Trim()
    if ($actual -ne $ExpectedVersion) {
        throw "[AIONS] Zła wersja Pythona: oczekiwano $ExpectedVersion, jest $actual ($PythonExe). Uruchom scripts\ensure_venv.ps1"
    }
}

$repoRoot = Get-AionsRepoRoot
$config = Read-AionsPythonConfig -RepoRoot $repoRoot
$expectedVersion = $config['AIONS_PYTHON_VERSION']
$venvWin = $config['AIONS_VENV_WIN']
if (-not $expectedVersion -or -not $venvWin) {
    throw '[AIONS] python.env musi zawierać AIONS_PYTHON_VERSION i AIONS_VENV_WIN'
}

$pythonExe = Join-Path $venvWin 'Scripts\python.exe'

if ($EnsureVenv -and -not (Test-Path $pythonExe)) {
    & (Join-Path $PSScriptRoot 'ensure_venv.ps1')
    if (-not (Test-Path $pythonExe)) {
        throw "[AIONS] ensure_venv.ps1 nie utworzył: $pythonExe"
    }
}

if (-not (Test-Path $pythonExe)) {
    throw "[AIONS] Brak venv Python: $pythonExe`nUruchom: scripts\ensure_venv.ps1"
}

Test-AionsPythonVersion -PythonExe $pythonExe -ExpectedVersion $expectedVersion

# Export optional runtime keys from python.env (mouth backend, GGUF paths, etc.)
$skipExport = @{
    'AIONS_PYTHON_VERSION' = $true
    'AIONS_VENV_WIN' = $true
    'AIONS_VENV_LINUX' = $true
    'AIONS_REPO_WIN' = $true
    'AIONS_REPO_LINUX' = $true
}
foreach ($key in $config.Keys) {
    if ($skipExport.ContainsKey($key)) { continue }
    if ($key -notmatch '^AIONS_') { continue }
    Set-Item -Path "Env:$key" -Value $config[$key]
}

if ($ResolveOnly) {
    Write-Output $pythonExe
    exit 0
}

if ($PythonArgs.Count -eq 0) {
    Write-Output $pythonExe
    exit 0
}

& $pythonExe @PythonArgs
exit $LASTEXITCODE
