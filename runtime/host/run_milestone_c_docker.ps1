#Requires -Version 5.1
<#
.SYNOPSIS
    Milestone C isolated Docker test (no systemd), logs on E:/D:.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\aions_milestone_paths.ps1"

$cacheScript = Join-Path (Get-AionsRepoRoot) 'scripts\set_aions_cache_env.ps1'
if (Test-Path $cacheScript) {
    . $cacheScript -Quiet
}

$repoRoot = Get-AionsRepoRoot
$logHost = Get-AionsMilestoneLogDir -Name 'milestone-c-docker' -RepoRoot $repoRoot
$logFile = Join-Path $logHost 'host-console.log'
$container = 'aions-milestone-c-test'

docker rm -f $container 2>$null | Out-Null

Write-Host "[MILESTONE-C] Repo: $repoRoot"
Write-Host "[MILESTONE-C] Logi host: $logHost"

docker run --name $container --rm `
    -v "${repoRoot}:/repo:ro" `
    -v "${logHost}:/mnt/aions-logs" `
    -e LOG_DIR=/mnt/aions-logs `
    -e REPO_SRC=/repo `
    ubuntu:22.04 `
    bash /repo/runtime/host/docker_milestone_c_test.sh `
    2>&1 | Tee-Object -FilePath $logFile

Write-Host "[MILESTONE-C] Zakończono. Logi: $logHost"
