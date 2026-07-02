@echo off
setlocal

rem Cache dev/test tylko D:\AIONS_DEV\cache (nie C:, nie E:)
set "SCRIPT_DIR=%~dp0"
if exist "%SCRIPT_DIR%scripts\set_aions_cache_env.ps1" (
  set "CACHE_PS1=%SCRIPT_DIR%scripts\set_aions_cache_env.ps1"
) else (
  set "CACHE_PS1=D:\AIONS_DEV\repo\server-wiedzy\scripts\set_aions_cache_env.ps1"
)
for /f "usebackq tokens=1,* delims==" %%a in (`powershell -NoProfile -ExecutionPolicy Bypass -File "%CACHE_PS1%" -EmitBatch`) do set "%%a=%%b"

set "WSL_USER=aions"
set "AIONS_DEV_ROOT=/mnt/d/AIONS_DEV"
set "REPO_ROOT=%AIONS_DEV_ROOT%/repo/server-wiedzy"
set "LAUNCHER_SH=%AIONS_DEV_ROOT%/start_aions_dev.sh"
set "COMMAND=%~1"
set "ARG2=%~2"

if "%COMMAND%"=="" set "COMMAND=status"

set "WSL_ARGS=%COMMAND%"
if not "%ARG2%"=="" set "WSL_ARGS=%WSL_ARGS% %ARG2%"

wsl -u %WSL_USER% -- bash -lc "chmod +x \"%LAUNCHER_SH%\" \"%REPO_ROOT%/scripts/aions-ctl\" \"%REPO_ROOT%/scripts/aions_python.sh\" 2>/dev/null || true; cd \"%REPO_ROOT%\" && \"%LAUNCHER_SH%\" %WSL_ARGS%"
set "EXIT_CODE=%ERRORLEVEL%"

endlocal & exit /b %EXIT_CODE%
