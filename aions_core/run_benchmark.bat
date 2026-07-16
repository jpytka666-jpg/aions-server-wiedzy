@echo off
echo Starting AIONS CBMS Benchmark
echo ================================

echo Step 1: Killing existing Python processes...
taskkill /F /IM python.exe 2>nul
if %errorlevel% == 0 (
    echo Python processes killed
) else (
    echo No Python processes found or already stopped
)

echo.
echo Step 2: Starting CBMS server in background...
cd /d "C:\Users\User\Desktop\AIONS_CBMS_RELEASE"
start /B py -u "server\cbms_direct_server.py"

echo.
echo Step 3: Waiting 5 seconds for server to start...
timeout /t 5 /nobreak

echo.
echo Step 4: Checking server health...
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://127.0.0.1:9000/health' -UseBasicParsing -TimeoutSec 10; Write-Host 'Server is healthy:' $response.Content } catch { Write-Host 'Server health check failed:' $_.Exception.Message }"

echo.
echo Step 5: Running self-test with 100 iterations...
powershell -ExecutionPolicy Bypass -File "selftest.ps1" -IterationsPerQuery 100

echo.
echo Step 6: Running simple test...
powershell -ExecutionPolicy Bypass -File "simple_test.ps1"

echo.
echo Benchmark complete! Check results in logs directory.
pause