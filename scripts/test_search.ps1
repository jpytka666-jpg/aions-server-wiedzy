param(
  [string]$Session = 'system_scan',
  [string]$Query = 'CLAUDE',
  [int]$TopK = 3,
  [string]$Endpoint = 'http://127.0.0.1:8765/search'
)
$ErrorActionPreference='Stop'
$body = @{ session_id=$Session; query=$Query; top_k=$TopK } | ConvertTo-Json
$resp = Invoke-RestMethod -Uri $Endpoint -Method Post -Body $body -ContentType 'application/json'
$resp.results | Select-Object -First $TopK | ForEach-Object {
  Write-Host ("- {0}  (score={1})" -f $_.text, [Math]::Round($_.score,4))
}
