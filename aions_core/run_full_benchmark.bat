@echo off
setlocal EnableDelayedExpansion
title AIONS CBMS Full Benchmark

echo ===============================================
echo     AIONS/CBMS FULL BENCHMARK SUITE
echo ===============================================
echo.

cd /d "C:\Users\User\Desktop\AIONS_CBMS_RELEASE"

echo [1/6] Killing any existing server processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *cbms_direct_server*" >nul 2>&1
taskkill /F /IM py.exe /FI "WINDOWTITLE eq *cbms_direct_server*" >nul 2>&1
timeout /t 2 >nul

echo [2/6] Starting CBMS server on port 9000...
start "CBMS_Server" /MIN cmd /c "python server\cbms_direct_server.py"
timeout /t 5 >nul

echo [3/6] Checking server health...
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:9000/health' -UseBasicParsing; $h = $r.Content | ConvertFrom-Json; Write-Host \"Server OK: $($h.chunks) chunks loaded\" -ForegroundColor Green } catch { Write-Host 'Server not responding!' -ForegroundColor Red; exit 1 }"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Server failed to start!
    pause
    exit /b 1
)

echo.
echo [4/6] Running quick test (10 iterations)...
powershell -NoProfile -ExecutionPolicy Bypass -File ".\selftest.ps1" -IterationsPerQuery 10
echo.

echo [5/6] Running full benchmark (100 iterations)...
echo This will take a few minutes...
powershell -NoProfile -ExecutionPolicy Bypass -File ".\selftest.ps1" -IterationsPerQuery 100

echo.
echo [6/6] Running Python benchmark tool...
python tools\bench_runner.py

echo.
echo ===============================================
echo     BENCHMARK COMPLETE
echo ===============================================
echo.
echo Results saved to:
echo   - logs\selftest_summary.json
echo   - logs\selftest_results.jsonl
echo   - logs\bench_summary.json
echo   - logs\bench_latency.jsonl
echo.

echo Press any key to stop the server...
pause >nul

taskkill /F /FI "WINDOWTITLE eq CBMS_Server*" >nul 2>&1
echo Server stopped.