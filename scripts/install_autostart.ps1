param(
  [int]$Port = 8765,
  [string]$BindHost = '127.0.0.1',
  [string]$TaskName = 'AIONS_Knowledge_Server'
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$runner = Join-Path $root 'scripts\run_server.ps1'
if(!(Test-Path $runner)){
  throw "Runner not found: $runner"
}

$ps = (Get-Command pwsh -ErrorAction SilentlyContinue)?.Source
if(-not $ps){ $ps = (Get-Command powershell -ErrorAction SilentlyContinue)?.Source }
if(-not $ps){ throw 'Cannot find PowerShell executable (pwsh or powershell).' }

$arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$runner`" -Port $Port -BindHost $BindHost"
$action = New-ScheduledTaskAction -Execute $ps -Argument $arguments -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -AtLogOn
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -RestartInterval (New-TimeSpan -Minutes 1) -RestartCount 3

try{
  if(Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue){
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue | Out-Null
  }
  Register-ScheduledTask -TaskName $TaskName -Description 'Start AIONS Knowledge Server on user logon' -Action $action -Trigger $trigger -Principal $principal -Settings $settings | Out-Null
  Write-Host "[AUTOSTART] Scheduled Task '$TaskName' installed." -ForegroundColor Green
}
catch{
  Write-Warning "[AUTOSTART] Register-ScheduledTask failed. Error: $($_.Exception.Message)"
  Write-Warning "[AUTOSTART] Falling back to Startup folder script instead of scheduled task."
  $startup = [Environment]::GetFolderPath('Startup')
  if(-not (Test-Path $startup)) { throw "Startup folder not found: $startup" }
  $launcher = Join-Path $startup 'launch_aions_knowledge_server.cmd'
  $cmdLine = ('"{0}" -NoProfile -ExecutionPolicy Bypass -File "{1}" -Port {2} -BindHost {3}' -f $ps, $runner, $Port, $BindHost)
  $cmdContent = "@echo off`r`n$cmdLine`r`n"
  Set-Content -Path $launcher -Value $cmdContent -Encoding ASCII
  Write-Host "[AUTOSTART] Created startup launcher: $launcher" -ForegroundColor Green
  Write-Host "[AUTOSTART] Server will start on next user logon via Startup folder." -ForegroundColor Green
}
