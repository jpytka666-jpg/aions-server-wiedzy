@echo off
cd /d "E:\server wiedzy\mcpServers\VS_CODE_MCP_CODEX"
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
set PYTHONUNBUFFERED=1
set PYTHONPATH=E:\server wiedzy
set CHROMA_PATH=E:\server wiedzy\data\chroma
powershell -NoProfile -ExecutionPolicy Bypass -File "E:\server wiedzy\scripts\aions_python.ps1" -X utf8 -m src stdio
