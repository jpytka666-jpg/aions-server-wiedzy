#Requires -Version 5.1
<#
.SYNOPSIS
    Resolve AIONS repo on E: or D: (never assume C:).
#>
function Get-AionsRepoRoot {
    if ($env:AIONS_REPO_WIN -and (Test-Path $env:AIONS_REPO_WIN)) {
        return (Resolve-Path $env:AIONS_REPO_WIN).Path
    }
    $candidates = @(
        'E:\server wiedzy',
        'D:\AIONS_DEV\server wiedzy',
        'D:\AIONS_DEV'
    )
    foreach ($root in $candidates) {
        $marker = Join-Path $root 'runtime\host\install_aions_host.sh'
        if (Test-Path $marker) {
            return (Resolve-Path $root).Path
        }
    }
    throw 'Nie znaleziono repo na E:\server wiedzy ani D:\AIONS_DEV'
}

function Get-AionsMilestoneLogDir {
    param(
        [Parameter(Mandatory)][string]$Name,
        [string]$RepoRoot = (Get-AionsRepoRoot)
    )
    $dir = Join-Path $RepoRoot "logs\$Name"
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    return $dir
}
