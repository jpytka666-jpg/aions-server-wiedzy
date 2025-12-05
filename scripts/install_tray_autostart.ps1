# Dodaje AIONS Tray Manager do autostartu Windows

$startupFolder = [Environment]::GetFolderPath('Startup')
$shortcutPath = Join-Path $startupFolder "AIONS Tray Manager.lnk"
$targetPath = "E:\server wiedzy\scripts\aions_tray_silent.vbs"

# Tworzenie skrotu
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = """$targetPath"""
$Shortcut.WorkingDirectory = "E:\server wiedzy"
$Shortcut.Description = "AIONS Tray Manager - kontrola Claude Desktop"
$Shortcut.Save()

Write-Host "AIONS Tray Manager dodany do autostartu!" -ForegroundColor Green
Write-Host ""
Write-Host "Lokalizacja: $shortcutPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "Tray Manager uruchomi sie automatycznie przy starcie Windows."
Write-Host "Aby usunac z autostartu, usun plik: $shortcutPath"
