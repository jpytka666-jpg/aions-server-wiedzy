# Usuwa AIONS Tray Manager z autostartu Windows

$startupFolder = [Environment]::GetFolderPath('Startup')
$shortcutPath = Join-Path $startupFolder "AIONS Tray Manager.lnk"

if (Test-Path $shortcutPath) {
    Remove-Item $shortcutPath -Force
    Write-Host "✅ AIONS Tray Manager usunięty z autostartu!" -ForegroundColor Green
} else {
    Write-Host "⚠️ Nie znaleziono w autostarcie." -ForegroundColor Yellow
}
