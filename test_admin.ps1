$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
Write-Host "Administrator status: $isAdmin"
if ($isAdmin) {
    Write-Host "✅ Running with Administrator privileges" -ForegroundColor Green
} else {
    Write-Host "❌ Not running with Administrator privileges" -ForegroundColor Red
}