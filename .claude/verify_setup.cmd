@echo off
echo ========================================
echo Claude Code Configuration Verification
echo ========================================
echo.

set ERRORS=0
set WARNINGS=0

echo 1. Checking Claude Code Extension...
if exist "C:\Users\User\.kiro\extensions\anthropic.claude-code-2.0.59-win32-x64" (
    echo    [OK] Extension found
) else (
    echo    [ERROR] Extension not found!
    set /a ERRORS+=1
)

echo.
echo 2. Checking Configuration Files...
if exist ".claude\settings.json" (
    echo    [OK] .claude\settings.json
) else (
    echo    [ERROR] .claude\settings.json missing!
    set /a ERRORS+=1
)

if exist ".claude\settings.local.json" (
    echo    [OK] .claude\settings.local.json
) else (
    echo    [ERROR] .claude\settings.local.json missing!
    set /a ERRORS+=1
)

if exist ".mcp.json" (
    echo    [OK] .mcp.json
) else (
    echo    [ERROR] .mcp.json missing!
    set /a ERRORS+=1
)

if exist ".claude\settings\kfc-settings.json" (
    echo    [OK] .claude\settings\kfc-settings.json
) else (
    echo    [ERROR] .claude\settings\kfc-settings.json missing!
    set /a ERRORS+=1
)

echo.
echo 3. Checking Python Environment...
if exist "E:\server wiedzy\venv\Scripts\python.exe" (
    echo    [OK] Python found
) else (
    echo    [ERROR] Python not found!
    set /a ERRORS+=1
)

echo.
echo 4. Checking ChromaDB Path...
if exist "E:\server wiedzy\data\chroma" (
    echo    [OK] ChromaDB directory exists
) else (
    echo    [WARNING] ChromaDB directory not found
    set /a WARNINGS+=1
)

echo.
echo 5. Checking MCP Server Files...
if exist "E:\server wiedzy\mcpServers\VS_CODE_MCP_CODEX\src\server.py" (
    echo    [OK] AIONS Context MCP server found
) else (
    echo    [ERROR] AIONS Context MCP server not found!
    set /a ERRORS+=1
)

echo.
echo 6. Checking WSL...
if exist "C:\Windows\System32\wsl.exe" (
    echo    [OK] WSL executable found
) else (
    echo    [WARNING] WSL not found
    set /a WARNINGS+=1
)

echo.
echo 7. Checking Documentation...
if exist ".claude\CLAUDE_CODE_SETUP.md" (
    echo    [OK] CLAUDE_CODE_SETUP.md
) else (
    echo    [WARNING] CLAUDE_CODE_SETUP.md missing
    set /a WARNINGS+=1
)

if exist ".claude\EXAMPLE_PROMPTS.md" (
    echo    [OK] EXAMPLE_PROMPTS.md
) else (
    echo    [WARNING] EXAMPLE_PROMPTS.md missing
    set /a WARNINGS+=1
)

echo.
echo ========================================
echo Verification Summary
echo ========================================
echo.

if %ERRORS%==0 (
    if %WARNINGS%==0 (
        echo [SUCCESS] All checks passed!
        echo.
        echo Next steps:
        echo 1. Open VS Code/Kiro with this workspace
        echo 2. Press Ctrl+Escape to open Claude Code
        echo 3. Try: "Check system health and verify all MCP servers"
    ) else (
        echo [WARNING] Configuration complete with warnings
        echo Claude Code should work, but some features may be limited.
    )
) else (
    echo [ERROR] Configuration has errors!
    echo Please fix the errors before using Claude Code.
)

echo.
echo For detailed setup instructions, see: .claude\CLAUDE_CODE_SETUP.md
echo.
pause
