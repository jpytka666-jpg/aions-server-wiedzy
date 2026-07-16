@echo off
color 0A
title AIONS ULTIMATE UNIFIED SYSTEM - MEGA LAUNCHER

echo.
echo ==============================================================
echo           AIONS ULTIMATE UNIFIED SYSTEM v3.0
echo                  WSZYSTKO W JEDNYM!
echo ==============================================================
echo.
echo LADOWANIE WSZYSTKICH KOMPONENTOW:
echo ----------------------------------
echo [+] CBMS Memory System (76+ chunks)
echo [+] Korean Compression Engine (3.29:1)
echo [+] CRLA Tournament System (K=12, J=0.893)
echo [+] Facts System (261+ facts)
echo [+] Conversation Enhancer
echo [+] Math Solver
echo [+] Natural Language Processing
echo [+] Hybrid Retrieval
echo.

cd /d "C:\Users\User\Desktop\AIONS_CBMS_RELEASE"

:: Ustaw zmienne środowiskowe
set CBMS_MEMORY_DIR=%cd%\memory
set CBMS_WEB_DIR=%cd%\web
set PYTHONPATH=%cd%;%cd%\server;%cd%\tools;E:\AI DEVELOPMENT\WORK SPACE\IMPORT FROM _F

:: Zabij stare procesy
echo Czyszczenie starych procesow...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 >nul

:: Menu wyboru
echo.
echo WYBIERZ TRYB URUCHOMIENIA:
echo --------------------------
echo [1] Chat Interaktywny
echo [2] Pelny Test Systemu
echo [3] Benchmark Wydajnosci
echo [4] Serwer Web (API)
echo [5] Test + Serwer (wszystko)
echo.

set /p choice="Wybierz opcje (1-5): "

if "%choice%"=="1" goto CHAT
if "%choice%"=="2" goto TEST
if "%choice%"=="3" goto BENCHMARK
if "%choice%"=="4" goto SERVER
if "%choice%"=="5" goto ALL

:CHAT
echo.
echo Uruchamiam Chat Interaktywny...
echo ================================
python AIONS_ULTIMATE_UNIFIED.py --mode chat
goto END

:TEST
echo.
echo Uruchamiam Pelny Test Systemu...
echo =================================
python AIONS_ULTIMATE_UNIFIED.py --mode test
goto END

:BENCHMARK
echo.
echo Uruchamiam Benchmark Wydajnosci...
echo ===================================
python AIONS_ULTIMATE_UNIFIED.py --mode benchmark
goto END

:SERVER
echo.
echo Uruchamiam Serwer Web API...
echo =============================
start "AIONS Server" /MIN python server\cbms_enhanced_server.py
echo.
echo Serwer uruchomiony na http://127.0.0.1:9000
echo.
echo Mozesz teraz:
echo - Otworzyc przegladarke: http://127.0.0.1:9000
echo - Uzyc API: POST http://127.0.0.1:9000/api/chat
echo - Sprawdzic status: GET http://127.0.0.1:9000/health
echo.
pause
goto END

:ALL
echo.
echo Uruchamiam WSZYSTKO!
echo ====================

:: Najpierw test
echo.
echo [1/3] Test systemu...
python AIONS_ULTIMATE_UNIFIED.py --mode test

:: Potem benchmark
echo.
echo [2/3] Benchmark...
python AIONS_ULTIMATE_UNIFIED.py --mode benchmark

:: Na koniec serwer
echo.
echo [3/3] Uruchamiam serwer...
start "AIONS Server" /MIN python server\cbms_enhanced_server.py

echo.
echo WSZYSTKO URUCHOMIONE!
echo Serwer: http://127.0.0.1:9000
echo.

:: I chat
echo Uruchamiam chat...
timeout /t 3 >nul
python AIONS_ULTIMATE_UNIFIED.py --mode chat

:END
echo.
echo ========================================
echo     DZIEKUJEMY ZA UZYCIE AIONS!
echo ========================================
echo.
pause