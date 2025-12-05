$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\AIONS MCP Server.lnk")
$Shortcut.TargetPath = "E:\server wiedzy\scripts\start_mcp.bat"
$Shortcut.WorkingDirectory = "E:\server wiedzy"
$Shortcut.IconLocation = "%SystemRoot%\System32\shell32.dll,13"
$Shortcut.Description = "Start AIONS MCP Server for Claude"
$Shortcut.Save()
Write-Host "Skrot utworzony na pulpicie!" -ForegroundColor Green
