' AIONS Tray Manager - Silent Launcher
' Uruchamia tray manager bez okna konsoli

Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "E:\server wiedzy"
WshShell.Run "E:\server wiedzy\venv\Scripts\pythonw.exe E:\server wiedzy\scripts\aions_tray.py", 0, False
