@echo off
REM AIONS Context MCP Server — automat Python (nigdy bare python)
REM Restart Cursor MCP po zmianie: Settings -> MCP -> aions-context -> Reload

cd /d "E:\server wiedzy"
set CHROMA_PATH=E:\server wiedzy\data\chroma
set AIONS_PATH=E:\server wiedzy\aions_core
set PYTHONPATH=E:\server wiedzy;E:\server wiedzy\server;E:\server wiedzy\mcpServers\VS_CODE_MCP_CODEX
set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=1

powershell -NoProfile -ExecutionPolicy Bypass -File "E:\server wiedzy\scripts\aions_python.ps1" "E:\server wiedzy\mcpServers\VS_CODE_MCP_CODEX\src\__main__.py" stdio
