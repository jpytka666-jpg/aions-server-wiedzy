param(
  [string]$GraphPath = 'C:\Users\User\ContextVault\AIONS_SYSTEM_MAP\output\system_graph.json',
  [string]$Session = 'system_scan',
  [string]$Endpoint = 'http://127.0.0.1:8765/contexts',
  [int]$BatchSize = 50
)

if(!(Test-Path $GraphPath)){ throw "Graph file not found: $GraphPath" }

Write-Host "[INGEST] Loading graph $GraphPath" -ForegroundColor Cyan
$json = Get-Content -Path $GraphPath -Raw | ConvertFrom-Json
$nodes = $json.nodes
if(-not $nodes){ throw 'No nodes found in graph JSON.' }

## Use a hashtable as base payload and a generic List for efficient appends
$payloadBase = @{ session_id = $Session }

$counter = 0
$batch = New-Object 'System.Collections.Generic.List[object]'
foreach($n in $nodes){
  $text = $n.label
  if([string]::IsNullOrWhiteSpace($text)){ continue }
  $meta = @{ type = $n.type; id = $n.id; degree = $n.degree; group = $n.group }
  # append as object to the generic list
  $batch.Add(@{ session_id = $Session; text = $text; metadata = $meta }) | Out-Null
  if($batch.Count -ge $BatchSize){
    $payloadBase.items = $batch
    $body = $payloadBase | ConvertTo-Json -Depth 6
    # reliable post with simple retry
    $tries = 0; $maxTries = 2; $posted = $false
    while(-not $posted -and $tries -le $maxTries){
      try{
  $null = Invoke-RestMethod -Uri $Endpoint -Method Post -ContentType 'application/json' -Body $body -TimeoutSec 30
        $posted = $true
      } catch {
        $tries++
        Write-Warning "[INGEST] Post failed (try $tries): $($_.Exception.Message)"
        if($tries -le $maxTries){ Start-Sleep -Seconds 1 }
        else { throw "[INGEST] Failed to post batch after $tries attempts: $($_.Exception.Message)" }
      }
    }
    $counter += $batch.Count
    Write-Host "[INGEST] Sent batch, total $counter" -ForegroundColor Green
    $batch = New-Object 'System.Collections.Generic.List[object]'
  }
}
if($batch.Count -gt 0){
  $payloadBase.items = $batch
  $body = $payloadBase | ConvertTo-Json -Depth 6
  $tries = 0; $maxTries = 2; $posted = $false
  while(-not $posted -and $tries -le $maxTries){
    try{
  $null = Invoke-RestMethod -Uri $Endpoint -Method Post -ContentType 'application/json' -Body $body -TimeoutSec 30
      $posted = $true
    } catch {
      $tries++
      Write-Warning "[INGEST] Final post failed (try $tries): $($_.Exception.Message)"
      if($tries -le $maxTries){ Start-Sleep -Seconds 1 } else { throw "[INGEST] Failed final post after $tries attempts: $($_.Exception.Message)" }
    }
  }
  $counter += $batch.Count
  Write-Host "[INGEST] Final batch sent, total $counter" -ForegroundColor Green
}
Write-Host "[INGEST] Completed ingestion for session '$Session'." -ForegroundColor Cyan
