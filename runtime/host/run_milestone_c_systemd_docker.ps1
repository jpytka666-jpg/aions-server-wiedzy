#Requires -Version 5.1
<#
.SYNOPSIS
    Milestone C full test — Docker privileged + systemd image, logs on E:/D: (bind mount).
#>
[CmdletBinding()]
param(
    [switch]$RebuildImage,
    [switch]$Detach,
    [switch]$Recreate
)

$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\aions_milestone_paths.ps1"

$cacheScript = Join-Path (Get-AionsRepoRoot) 'scripts\set_aions_cache_env.ps1'
if (Test-Path $cacheScript) {
    . $cacheScript -Quiet
}

$repoRoot = Get-AionsRepoRoot
$logHost = Get-AionsMilestoneLogDir -Name 'milestone-c-systemd' -RepoRoot $repoRoot
$image = 'aions-systemd-test:22.04'
$container = 'aions-milestone-c'
$dockerfile = Join-Path $PSScriptRoot 'Dockerfile.systemd-test'

if ($RebuildImage -or -not (docker image inspect $image 2>$null)) {
    docker build -t $image -f $dockerfile $PSScriptRoot
}

$running = docker ps -q -f "name=^${container}$" 2>$null
if ($running -and -not $Recreate) {
    Write-Host "[MILESTONE-C] Kontener $container już działa (PID $running). Logi zsynchronizuj: docker cp ${container}:/mnt/aions-logs/. `"$logHost`""
    Write-Host "[MILESTONE-C] Aby uruchomić od nowa: -Recreate"
    exit 0
}

$existing = docker ps -aq -f "name=^${container}$" 2>$null
if ($existing) {
    docker rm -f $container | Out-Null
}

$runArgs = @(
    'run', '--name', $container, '--privileged',
    '-v', '/sys/fs/cgroup:/sys/fs/cgroup:rw',
    '-v', "${repoRoot}:/repo:ro",
    '-v', "${logHost}:/mnt/aions-logs",
    '-v', "${PSScriptRoot}\docker_milestone_c_systemd_run.v2.sh:/run-test.sh:ro",
    '-e', 'LOG_DIR=/mnt/aions-logs',
    '-e', 'REPO_SRC=/repo'
)
if ($Detach) { $runArgs += '-d' }
$runArgs += $image, 'bash', '/run-test.sh'

Write-Host "[MILESTONE-C] Repo: $repoRoot"
Write-Host "[MILESTONE-C] Logi host: $logHost"
& docker @runArgs

