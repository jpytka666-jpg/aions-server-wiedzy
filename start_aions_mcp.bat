@echo off
REM AIONS Context MCP Server Wrapper
REM Resolves path issues with spaces

cd /d "E:\server wiedzy"
set CHROMA_PATH=E:\server wiedzy\data\chroma
set PYTHONPATH=E:\server wiedzy;E:\server wiedzy\server;E:\server wiedzy\mcpServers\VS_CODE_MCP_CODEX

"E:\server wiedzy\venv\Scripts\python.exe" "E:\server wiedzy\mcpServers\VS_CODE_MCP_CODEX\src\__main__.py" stdio
