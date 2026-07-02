#Requires -Version 5.1
<#
.SYNOPSIS
    Ustawia katalogi cache AIONS na D:\AIONS_DEV\cache (pip, temp, torch, hf).
.DESCRIPTION
    Tworzy katalogi cache i ustawia zmienne środowiskowe sesji.
    Użyj -EmitBatch aby wyemitować linie SET dla plików .bat.
#>
[CmdletBinding()]
param(
    [switch]$EmitBatch,
    [switch]$Quiet
)

$ErrorActionPreference = 'Stop'

$cacheRoot = 'D:\AIONS_DEV\cache'
$map = [ordered]@{
    PIP_CACHE_DIR = Join-Path $cacheRoot 'pip'
    TEMP          = Join-Path $cacheRoot 'temp'
    TMP           = Join-Path $cacheRoot 'temp'
    HF_HOME       = Join-Path $cacheRoot 'hf'
    TORCH_HOME    = Join-Path $cacheRoot 'torch'
}

foreach ($dir in $map.Values | Select-Object -Unique) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

foreach ($entry in $map.GetEnumerator()) {
    Set-Item -Path "Env:$($entry.Key)" -Value $entry.Value
    if ($EmitBatch) {
        Write-Output "$($entry.Key)=$($entry.Value)"
    }
}

if (-not $EmitBatch -and -not $Quiet) {
    Write-Verbose "[AIONS] Cache env: $cacheRoot"
}
