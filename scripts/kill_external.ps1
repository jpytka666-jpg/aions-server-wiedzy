param(
  [bool]$Kill = $false
)
Write-Host "[KILL] Scanning for external PowerShell/python uvicorn/scan processes..." -ForegroundColor Cyan
$targets = @()
try {
  $procs = Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -match 'uvicorn|server\.app:app|run_server\.ps1|scan_system\.ps1'
  }
  foreach($p in $procs){
    $targets += [pscustomobject]@{ PID=$p.ProcessId; Name=$p.Name; Cmd=$p.CommandLine }
  }
} catch {
  Write-Warning "[KILL] Failed to enumerate processes via CIM: $($_.Exception.Message)"
}

if(-not $targets.Count){ Write-Host "[KILL] No matching processes found." -ForegroundColor DarkGray; return }
Write-Host "[KILL] Found $($targets.Count) process(es):" -ForegroundColor Yellow
$targets | ForEach-Object { Write-Host ("  PID={0} Name={1}" -f $_.PID,$_.Name) -ForegroundColor Yellow }

if($Kill){
  foreach($t in $targets){
    try { Stop-Process -Id $t.PID -Force -ErrorAction Stop; Write-Host ("[KILL] Stopped PID {0}" -f $t.PID) -ForegroundColor Green }
    catch { Write-Warning ("[KILL] Failed to stop PID {0}: {1}" -f $t.PID, $_.Exception.Message) }
  }
  Write-Host "[KILL] Done." -ForegroundColor Green
}
