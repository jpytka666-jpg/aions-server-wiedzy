param(
  [string]$TaskName = 'AIONS_ContextSnapshot',
  [int]$Minutes = 5,
  [switch]$Prune
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$scriptPath = Join-Path $repoRoot 'scripts\context_snapshot.ps1'

if (-not (Test-Path $scriptPath)) {
  throw "Snapshot script not found: $scriptPath"
}

$pwsh = (Get-Command pwsh -ErrorAction SilentlyContinue)?.Source
if (-not $pwsh) {
  $pwsh = (Get-Command powershell -ErrorAction SilentlyContinue)?.Source
}
if (-not $pwsh) {
  throw "Cannot find pwsh or powershell."
}

$arguments = @(
  '-NoProfile','-ExecutionPolicy','Bypass',
  '-File', $scriptPath,
  '-OutputDir', (Join-Path $repoRoot 'logs\context_dumps')
)
if ($Prune) {
  $arguments += '-PruneOnDump'
}
$argString = $arguments -join ' '

$action = New-ScheduledTaskAction -Execute $pwsh -Argument $argString -WorkingDirectory $repoRoot
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $Minutes) -RepetitionDuration ([TimeSpan]::MaxValue)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
  Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false | Out-Null
}

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings |
  Out-Null

Write-Host "[SNAPSHOT] Scheduled task '$TaskName' created (interval ${Minutes}m, prune=$($Prune.IsPresent))." -ForegroundColor Green
