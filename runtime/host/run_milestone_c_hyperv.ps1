#Requires -Version 5.1
#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Milestone C end-to-end on Hyper-V VM - Ubuntu 22.04, VHDX on D:, zero Docker/WSL prod.
.PARAMETER Recreate
    Remove existing VM and disks, start fresh.
.PARAMETER SkipProvision
    VM already exists and is booted - only run guest test scripts.
#>
[CmdletBinding()]
param(
    [switch]$Recreate,
    [switch]$SkipProvision
)

$ErrorActionPreference = 'Stop'

$VmName       = 'aions-milestone-c'
$VmRoot       = 'D:\AIONS_DEV\vm\aions-milestone-c'
$VhdPath      = Join-Path $VmRoot 'vhd\aions-milestone-c.vhdx'
$IsoDir       = Join-Path $VmRoot 'iso'
$KeysDir      = Join-Path $VmRoot 'keys'
$ServerIso    = Join-Path $IsoDir 'ubuntu-22.04.5-live-server-amd64.iso'
$SeedIso      = Join-Path $IsoDir 'aions-seed.iso'
$LogHost      = 'D:\AIONS_DEV\logs\milestone-c-hyperv'
$RepoHost     = 'D:\AIONS_DEV\repo\server-wiedzy'
$SwitchName   = 'Default Switch'
$MemoryGB     = 4
$CpuCount     = 2
$DiskGB       = 40
$GuestUser    = 'ubuntu'
$ServerIsoUrl = 'https://releases.ubuntu.com/jammy/ubuntu-22.04.5-live-server-amd64.iso'

$ScriptDir = $PSScriptRoot
$RunScript = Join-Path $ScriptDir 'hyperv_milestone_c_run.sh'
$RebootScript = Join-Path $ScriptDir 'hyperv_milestone_c_post_reboot.sh'

function Write-McLog([string]$Msg) {
    $ts = Get-Date -Format 'yyyy-MM-ddTHH:mm:ss'
    $line = "[$ts][MILESTONE-C-HYPERV] $Msg"
    Write-Host $line
    Add-Content -Path (Join-Path $LogHost 'host.log') -Value $line -ErrorAction SilentlyContinue
}

function Ensure-Dirs {
    foreach ($d in @($VmRoot, (Split-Path $VhdPath), $IsoDir, $KeysDir, $LogHost)) {
        New-Item -ItemType Directory -Force -Path $d | Out-Null
    }
}

function Ensure-SshKey {
    $priv = Join-Path $KeysDir 'id_ed25519'
    $pub  = Join-Path $KeysDir 'id_ed25519.pub'
    if (-not (Test-Path $priv)) {
        Write-McLog "Generowanie klucza SSH: $priv"
        ssh-keygen -t ed25519 -f $priv -N '""' -C 'aions-milestone-c' | Out-Null
    }
    return @{
        Private = $priv
        Public  = (Get-Content $pub -Raw).Trim()
    }
}

function Ensure-InstallMedia {
    if (-not (Test-Path $ServerIso)) {
        Write-McLog "Pobieranie Ubuntu Server ISO (ok. 2 GB)..."
        Invoke-WebRequest -Uri $ServerIsoUrl -OutFile $ServerIso -UseBasicParsing
    }
    if ($Recreate -and (Test-Path $VhdPath)) {
        Write-McLog "Usuwanie starego VHDX: $VhdPath"
        Remove-Item $VhdPath -Force
    }
    if (-not (Test-Path $VhdPath)) {
        Write-McLog "Tworzenie pustego VHDX ${DiskGB}GB: $VhdPath"
        New-VHD -Path $VhdPath -SizeBytes ($DiskGB * 1GB) -Dynamic | Out-Null
    }
}

function New-SeedIso([string]$PubKey) {
    $metaDir = Join-Path $IsoDir 'seed'
    if (Test-Path $metaDir) { Remove-Item -Recurse -Force $metaDir }
    New-Item -ItemType Directory -Force -Path $metaDir | Out-Null

    $pwHash = (wsl -d Ubuntu -u root -- openssl passwd -6 -salt aionsmc aions-temp-install 2>$null).Trim()

    $userData = @"
#cloud-config
autoinstall:
  version: 1
  locale: en_US.UTF-8
  keyboard:
    layout: us
  network:
    network:
      version: 2
      ethernets:
        all-en:
          match:
            name: en*
          dhcp4: true
  storage:
    layout:
      name: direct
  identity:
    hostname: aions-milestone-c
    username: ubuntu
    password: "$pwHash"
  ssh:
    install-server: true
    allow-pw: false
    authorized-keys:
      - $PubKey
  packages:
    - openssh-server
    - python3.11
    - python3.11-venv
    - python3-pip
    - git
    - curl
    - jq
    - cifs-utils
    - qemu-guest-agent
    - rsync
    - adduser
    - ca-certificates
    - dbus-user-session
    - systemd-sysv
  late-commands:
    - curtin in-target --target=/target -- adduser --disabled-password --gecos "" aions
    - curtin in-target --target=/target -- systemctl enable ssh
    - curtin in-target --target=/target -- systemctl enable qemu-guest-agent
  shutdown: reboot
"@
    Set-Content -Path (Join-Path $metaDir 'user-data') -Value $userData -Encoding UTF8
    'instance-id: aions-milestone-c-001' | Set-Content (Join-Path $metaDir 'meta-data') -Encoding ascii

    Write-McLog "Budowa seed ISO (autoinstall)..."
    $wslMeta = ($metaDir -replace '\\', '/') -replace '^D:', '/mnt/d'
    $wslSeed = ($SeedIso -replace '\\', '/') -replace '^D:', '/mnt/d'
    $cmd = @"
set -e
export DEBIAN_FRONTEND=noninteractive
if ! command -v xorriso >/dev/null 2>&1; then
  apt-get update -qq
  apt-get install -y -qq xorriso
fi
xorriso -as mkisofs -output '$wslSeed' -volid cidata -joliet -rock '$wslMeta'
"@
    wsl -d Ubuntu -u root -- bash -lc $cmd
}

function Ensure-SmbShare {
    $shareName = 'aions-dev'
    $existing = Get-SmbShare -Name $shareName -ErrorAction SilentlyContinue
    if ($existing) {
        Write-McLog "SMB share $shareName juz istnieje"
        return $shareName
    }
    Write-McLog "Tworzenie SMB share D:\AIONS_DEV jako $shareName"
    New-SmbShare -Name $shareName -Path 'D:\AIONS_DEV' -FullAccess 'Everyone' -ErrorAction Stop | Out-Null
    return $shareName
}

function Get-HostSwitchIp {
    $ip = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object { $_.InterfaceAlias -like '*Default Switch*' -and $_.IPAddress -notlike '169.*' } |
        Select-Object -First 1 -ExpandProperty IPAddress)
    if (-not $ip) { $ip = '172.20.112.1' }
    return $ip
}

function Find-VmIpByScan {
    $base = Get-HostSwitchIp
    $prefix = ($base -split '\.')[0..2] -join '.'
    Write-McLog "Skan SSH w podsieci ${prefix}.0/24..."
    foreach ($last in 1..254) {
        $ip = "${prefix}.$last"
        if ($ip -eq $base) { continue }
        try {
            $t = New-Object Net.Sockets.TcpClient
            $r = $t.BeginConnect($ip, 22, $null, $null)
            if ($r.AsyncWaitHandle.WaitOne(200) -and $t.Connected) {
                $t.Close()
                return $ip
            }
        } catch {}
    }
    return $null
}

function Ensure-HyperVVm {
    $vm = Get-VM -Name $VmName -ErrorAction SilentlyContinue
    if ($vm -and $Recreate) {
        Write-McLog "Usuwanie istniejacej VM $VmName"
        if ($vm.State -ne 'Off') { Stop-VM -Name $VmName -Force -TurnOff }
        Remove-VM -Name $VmName -Force
        $vm = $null
    }
    if ($vm) {
        Write-McLog "VM $VmName juz istnieje (State=$($vm.State), Gen=$($vm.Generation))"
        return $vm
    }

    Write-McLog "Tworzenie VM Gen2 $VmName"
    New-VM -Name $VmName -MemoryStartupBytes ($MemoryGB * 1GB) -Generation 2 -Path $VmRoot -SwitchName $SwitchName | Out-Null
    Set-VM -Name $VmName -ProcessorCount $CpuCount -AutomaticStartAction Nothing -AutomaticStopAction ShutDown
    Set-VMMemory -VMName $VmName -DynamicMemoryEnabled $false

    Add-VMHardDiskDrive -VMName $VmName -Path $VhdPath
    Set-VMFirmware -VMName $VmName -EnableSecureBoot Off
    Add-VMDvdDrive -VMName $VmName -Path $ServerIso
    Add-VMDvdDrive -VMName $VmName -Path $SeedIso
    $ubuntuDvd = (Get-VMDvdDrive -VMName $VmName | Where-Object { $_.Path -eq $ServerIso } | Select-Object -First 1)
    Set-VMFirmware -VMName $VmName -FirstBootDevice $ubuntuDvd

    Enable-VMIntegrationService -VMName $VmName -Name 'Guest Service Interface' -ErrorAction SilentlyContinue
    return Get-VM -Name $VmName
}

function Start-AndWaitSsh([string]$PrivKey, [int]$TimeoutSec = 1800) {
    $vm = Get-VM -Name $VmName
    if ($vm.State -ne 'Running') {
        Write-McLog "Start VM $VmName"
        Start-VM -Name $VmName
    }

    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    $ip = $null
    $sshOpts = @('-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=NUL', '-o', 'ConnectTimeout=8', '-i', $PrivKey)

    while ((Get-Date) -lt $deadline) {
        $ips = @(Get-VMNetworkAdapter -VMName $VmName | Select-Object -ExpandProperty IPAddresses |
            Where-Object { $_ -match '^\d+\.\d+\.\d+\.\d+$' -and $_ -notlike '169.*' })
        if ($ips.Count -eq 0) {
            $scanIp = Find-VmIpByScan
            if ($scanIp) { $ips = @($scanIp) }
        }
        foreach ($candidate in $ips) {
            & ssh @sshOpts "${GuestUser}@${candidate}" 'echo ssh-ready' 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-McLog "SSH gotowy: ${GuestUser}@${candidate}"
                return $candidate
            }
        }
        $remaining = [int]($deadline - (Get-Date)).TotalSeconds
        if ($remaining % 60 -lt 15) {
            Write-McLog "Czekam na SSH/autoinstall... (~${remaining}s)"
        }
        Start-Sleep -Seconds 15
    }
    throw "Timeout: SSH nieosiagnalny po ${TimeoutSec}s"
}

function Invoke-GuestScript {
    param(
        [string]$Ip,
        [string]$PrivKey,
        [string]$LocalScript,
        [string]$RemoteName,
        [string]$ExtraEnv = ''
    )
    $sshOpts = @('-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=NUL', '-i', $PrivKey)
    $remote = "/tmp/$RemoteName"
    & scp @sshOpts $LocalScript "${GuestUser}@${Ip}:$remote"
    if ($LASTEXITCODE -ne 0) { throw "scp failed: $LocalScript" }
    $hostIp = Get-HostSwitchIp
    $cmd = @"
set -e
sudo mkdir -p /mnt/aions-dev /mnt/aions-cache /var/log/aions/milestone-c
if ! mountpoint -q /mnt/aions-dev; then
  sudo mount -t cifs //$hostIp/aions-dev /mnt/aions-dev -o guest,vers=3.0,uid=0,gid=0,file_mode=0755,dir_mode=0755 || \
  sudo mount -t cifs //$hostIp/aions-dev /mnt/aions-dev -o username=guest,vers=3.0,uid=0,gid=0
fi
if ! mountpoint -q /mnt/aions-cache; then
  sudo mkdir -p /mnt/aions-cache
  sudo mount --bind /mnt/aions-dev/cache /mnt/aions-cache || true
fi
export REPO_SRC=/mnt/aions-dev/repo/server-wiedzy
export LOG_DIR=/var/log/aions/milestone-c
export PIP_CACHE_DIR=/mnt/aions-cache/pip
$ExtraEnv
chmod +x $remote
sudo bash $remote
"@
    & ssh @sshOpts "${GuestUser}@${Ip}" $cmd
    return $LASTEXITCODE
}

function Copy-GuestLogs([string]$Ip, [string]$PrivKey) {
    $sshOpts = @('-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=NUL', '-i', $PrivKey)
    $guestLog = '/var/log/aions/milestone-c'
    & scp @sshOpts -r "${GuestUser}@${Ip}:${guestLog}/*" $LogHost 2>$null
}

# --- main ---
Ensure-Dirs
Write-McLog "=== Milestone C Hyper-V start (ISO autoinstall) ==="
Write-McLog "VM=$VmName VHD=$VhdPath LOG=$LogHost REPO=$RepoHost"

if (-not (Test-Path $RepoHost)) {
    throw "Brak repo mirror: $RepoHost - uruchom sync_dev_mirror.ps1"
}

$keys = Ensure-SshKey

if (-not $SkipProvision) {
    Ensure-InstallMedia
    New-SeedIso -PubKey $keys.Public
    Ensure-SmbShare | Out-Null
    Ensure-HyperVVm | Out-Null
}

$ip = Start-AndWaitSsh -PrivKey $keys.Private -TimeoutSec 2400
Write-McLog "SSH gotowy: ${GuestUser}@${ip}"

Write-McLog "=== Faza 1: install + validate (pre-reboot) ==="
$ec1 = Invoke-GuestScript -Ip $ip -PrivKey $keys.Private -LocalScript $RunScript -RemoteName 'milestone_c_run.sh'
Copy-GuestLogs -Ip $ip -PrivKey $keys.Private

Write-McLog "=== Reboot VM ==="
$sshOpts = @('-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=NUL', '-i', $keys.Private)
& ssh @sshOpts "${GuestUser}@${ip}" 'sudo reboot' 2>$null
Start-Sleep -Seconds 20
$ip = Start-AndWaitSsh -PrivKey $keys.Private -TimeoutSec 600

Write-McLog "=== Faza 2: validate post-reboot ==="
$ec2 = Invoke-GuestScript -Ip $ip -PrivKey $keys.Private -LocalScript $RebootScript -RemoteName 'milestone_c_post_reboot.sh'
Copy-GuestLogs -Ip $ip -PrivKey $keys.Private

$preExit = 'missing'
$postExit = 'missing'
$preFile = Join-Path $LogHost 'overall_pre_reboot.exit'
$postFile = Join-Path $LogHost 'overall_post_reboot.exit'
if (Test-Path $preFile) { $preExit = (Get-Content $preFile -Raw).Trim() }
if (Test-Path $postFile) { $postExit = (Get-Content $postFile -Raw).Trim() }

$strictPass = ($ec1 -eq 0 -and $ec2 -eq 0)
Write-McLog "=== WYNIK ==="
Write-McLog "VM: $VmName"
Write-McLog "VHD: $VhdPath"
Write-McLog "IP: $ip"
Write-McLog "SSH: ssh -i `"$($keys.Private)`" ${GuestUser}@${ip}"
Write-McLog "Hyper-V Connect: vmconnect localhost $VmName"
Write-McLog "pre-reboot exit=$ec1 overall_pre=$preExit"
Write-McLog "post-reboot exit=$ec2 overall_post=$postExit"
Write-McLog "strict-health: $(if ($strictPass) { 'PASS' } else { 'FAIL' })"

@{
    vm_name = $VmName
    vhd_path = $VhdPath
    vm_ip = $ip
    ssh_command = "ssh -i `"$($keys.Private)`" ${GuestUser}@${ip}"
    hyperv_connect = "vmconnect localhost $VmName"
    pre_reboot_exit = $ec1
    post_reboot_exit = $ec2
    strict_health = $(if ($strictPass) { 'PASS' } else { 'FAIL' })
    log_dir = $LogHost
} | ConvertTo-Json | Set-Content (Join-Path $LogHost 'result.json')

if (-not $strictPass) { exit 1 }
exit 0
