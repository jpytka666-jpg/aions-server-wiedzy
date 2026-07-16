@echo off
color 0A
echo.
echo ========================================
echo    AIONS/CBMS BENCHMARK - URUCHAMIANIE
echo ========================================
echo.
echo INSTRUKCJA:
echo -----------
echo 1. Ten skrypt uruchomi pelny benchmark systemu AIONS/CBMS
echo 2. Serwer zostanie uruchomiony automatycznie na porcie 9000
echo 3. Testy obejmuja:
echo    - Test wydajnosci (100-1000 iteracji)
echo    - Test odpowiedzi systemowych
echo    - Test odmowy OOD (Out-Of-Domain)
echo    - Test bezpieczenstwa
echo.
echo WYNIKI BEDA ZAPISANE W:
echo ------------------------
echo - logs\selftest_summary.json (podsumowanie)
echo - logs\selftest_results.jsonl (szczegoly)
echo - logs\bench_summary.json (benchmark)
echo - TEST_REPORT.md (raport)
echo.
pause

cd /d "C:\Users\User\Desktop\AIONS_CBMS_RELEASE"

echo.
echo [KROK 1] Zabijanie starych procesow...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM py.exe 2>nul
timeout /t 2 >nul

echo.
echo [KROK 2] Uruchamianie serwera CBMS...
start /MIN python server\cbms_direct_server.py
timeout /t 5 >nul

echo.
echo [KROK 3] Sprawdzanie serwera...
curl -s http://127.0.0.1:9000/health
echo.

echo.
echo [KROK 4] Uruchamianie testow (to potrwa kilka minut)...
echo.
powershell -ExecutionPolicy Bypass -File selftest.ps1 -IterationsPerQuery 100

echo.
echo [KROK 5] Uruchamianie benchmarku Python...
python tools\bench_runner.py

echo.
echo [KROK 6] Uruchamianie prostego testu...
powershell -ExecutionPolicy Bypass -File simple_test.ps1

echo.
echo ========================================
echo    BENCHMARK ZAKONCZONY!
echo ========================================
echo.
echo Wyniki zapisano w katalogu: logs\
echo.
echo Nacisnij dowolny klawisz aby zatrzymac serwer...
pause >nul

taskkill /F /IM python.exe 2>nul
echo Serwer zatrzymany.