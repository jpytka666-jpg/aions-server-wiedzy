@echo off
echo === AIONS MCP Server Test ===
echo.

cd /d "E:\server wiedzy"

echo Activating venv...
call venv\Scripts\activate.bat

echo.
echo Testing minimal server (press Ctrl+C to stop)...
echo.

cd mcpServers\VS_CODE_MCP_CODEX
python -c "from src.test_server import server; print('Import OK'); server.run(transport='stdio')"

pause
