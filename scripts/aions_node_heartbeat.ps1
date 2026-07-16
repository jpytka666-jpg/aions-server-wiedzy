#Requires -Version 5.1
<#
.SYNOPSIS
  Send one AIONS node heartbeat to Core API (Windows wrapper).

.EXAMPLE
  .\scripts\aions_node_heartbeat.ps1
  .\scripts\aions_node_heartbeat.ps1 -Interval 60
  .\scripts\aions_node_heartbeat.ps1 -Once -NodeId proxmox-vm9100
#>
param(
  [string]$CoreUrl = $env:AIONS_CORE_URL,
  [string]$NodeId = $env:AIONS_NODE_ID,
  [int]$Interval = 60,
  [switch]$Once
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$launcher = Join-Path $root 'scripts\aions_python.ps1'
$script = Join-Path $root 'scripts\aions_node_heartbeat.py'

$args = @($script)
if ($CoreUrl) { $args += @('--core-url', $CoreUrl) }
if ($NodeId) { $args += @('--node-id', $NodeId) }
if ($Once) { $args += '--once' } else { $args += @('--interval', "$Interval") }

& $launcher @args
