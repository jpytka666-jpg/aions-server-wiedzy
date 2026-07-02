#Requires -Version 5.1
<#
.SYNOPSIS
    Tworzy lub weryfikuje venv AIONS zgodnie z .aions/python.env (Windows prod).
#>
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'set_aions_cache_env.ps1')

$repoRoot = Split-Path -Parent $PSScriptRoot
$configPath = Join-Path $repoRoot '.aions\python.env'
if (-not (Test-Path $configPath)) {
    throw "[AIONS] Brak $configPath"
}

$config = @{}
Get-Content $configPath -Encoding UTF8 | ForEach-Object {
    $line = $_.Trim()
    if ($line -eq '' -or $line.StartsWith('#')) { return }
    $idx = $line.IndexOf('=')
    if ($idx -lt 1) { return }
    $config[$line.Substring(0, $idx).Trim()] = $line.Substring($idx + 1).Trim()
}

$expectedVersion = $config['AIONS_PYTHON_VERSION']
$venvPath = $config['AIONS_VENV_WIN']
$pythonExe = Join-Path $venvPath 'Scripts\python.exe'

if (-not $expectedVersion -or -not $venvPath) {
    throw '[AIONS] python.env: brak AIONS_PYTHON_VERSION lub AIONS_VENV_WIN'
}

$pyLauncher = "py -$expectedVersion"
Write-Host "[AIONS] Oczekiwana wersja: Python $expectedVersion"
Write-Host "[AIONS] Venv: $venvPath"

if (Test-Path $pythonExe) {
    $actual = & $pythonExe -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    if ("$actual".Trim() -eq $expectedVersion) {
        Write-Host "[AIONS] OK: venv istnieje, wersja $actual"
        exit 0
    }
    Write-Warning "[AIONS] Venv ma złą wersję ($actual). Usuń $venvPath i uruchom ponownie."
    exit 1
}

Write-Host "[AIONS] Tworzenie venv..."
$parent = Split-Path -Parent $venvPath
if (-not (Test-Path $parent)) {
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
}

& py "-$expectedVersion" -m venv $venvPath
if ($LASTEXITCODE -ne 0) {
    throw "[AIONS] py -$expectedVersion -m venv nie powiodło się. Zainstaluj Python $expectedVersion."
}

$actual = & $pythonExe -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ("$actual".Trim() -ne $expectedVersion) {
    throw "[AIONS] Nowy venv ma złą wersję: $actual"
}

$req = Join-Path $repoRoot 'requirements.txt'
if (Test-Path $req) {
    Write-Host "[AIONS] Instalacja requirements.txt..."
    & (Join-Path $venvPath 'Scripts\pip.exe') install -r $req
}

Write-Host "[AIONS] Venv gotowy: $pythonExe ($actual)"
