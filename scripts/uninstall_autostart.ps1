param(
  [string]$TaskName = 'AIONS_Knowledge_Server'
)
$ErrorActionPreference = 'Stop'
try {
  if(Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue){
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false | Out-Null
    Write-Host "[AUTOSTART] Scheduled Task '$TaskName' removed." -ForegroundColor Yellow
  } else {
    Write-Host "[AUTOSTART] Task '$TaskName' not found." -ForegroundColor DarkGray
  }
} catch {
  Write-Error $_
  throw
}
