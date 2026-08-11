@echo off
REM AIONS Context MCP Server - HTTP (streamable-http) transport for LAN clients.
REM Same server object as start_aions_mcp.bat, different wire protocol.
REM Remote client:  claude mcp add --transport http aions http://<this-host-ip>:%AIONS_HTTP_PORT%/mcp

cd /d "E:\server wiedzy"
set CHROMA_PATH=E:\server wiedzy\data\chroma
set AIONS_VECTOR_BACKEND=api
set AIONS_PATH=E:\server wiedzy\aions_core
set PYTHONPATH=E:\server wiedzy;E:\server wiedzy\server;E:\server wiedzy\mcpServers\VS_CODE_MCP_CODEX
set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=1

REM Provenance - stamped onto every memory write. Session stays single.
if "%AIONS_AGENT%"=="" set AIONS_AGENT=claude
if "%AIONS_SURFACE%"=="" set AIONS_SURFACE=lan-http

REM Network binding - override before calling this script if needed.
if "%AIONS_HTTP_HOST%"=="" set AIONS_HTTP_HOST=0.0.0.0
if "%AIONS_HTTP_PORT%"=="" set AIONS_HTTP_PORT=8787

echo [AIONS] starting MCP over HTTP on %AIONS_HTTP_HOST%:%AIONS_HTTP_PORT%/mcp
powershell -NoProfile -ExecutionPolicy Bypass -File "E:\server wiedzy\scripts\aions_python.ps1" "E:\server wiedzy\mcpServers\VS_CODE_MCP_CODEX\src\__main__.py" http
