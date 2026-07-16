@echo off
setlocal
set CBMS_MEMORY_DIR=%~dp0memory
set CBMS_WEB_DIR=%~dp0web
py -u "%~dp0server\cbms_direct_server.py"

