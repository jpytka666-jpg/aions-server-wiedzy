@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "REPO_ROOT=%SCRIPT_DIR%..\.."
powershell -NoProfile -ExecutionPolicy Bypass -File "%REPO_ROOT%\scripts\aions_python.ps1" "%SCRIPT_DIR%autolog_bootstrap.py"
exit /b %ERRORLEVEL%
