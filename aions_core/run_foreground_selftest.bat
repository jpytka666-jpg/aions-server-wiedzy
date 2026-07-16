@echo off
setlocal
set PS1=%~dp0run_foreground_selftest.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS1%"
pause

