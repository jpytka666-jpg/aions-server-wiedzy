@echo off
color 0E
title AIONS Enhanced Conversational Server

echo.
echo ========================================================
echo         AIONS/CBMS ENHANCED SERVER v2.0
echo       Naturalniejsze konwersacje i lepsza AI
echo ========================================================
echo.
echo ULEPSZENIA:
echo -----------
echo [+] Naturalne odpowiedzi zamiast sztywnych szablonow
echo [+] Pamiec kontekstu (20 ostatnich wymian)
echo [+] Roznorodnosc odpowiedzi (brak powtorzen)
echo [+] Inteligencja emocjonalna
echo [+] Lagodne odmowy zamiast "NIE WIEM"
echo [+] Personalizacja i emotikony
echo.

cd /d "C:\Users\User\Desktop\AIONS_CBMS_RELEASE"

:: Set environment variables
set CBMS_MEMORY_DIR=%cd%\memory
set CBMS_WEB_DIR=%cd%\web

:: Kill old server
echo Zatrzymuje stary serwer...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 >nul

:: Start enhanced server
echo.
echo Uruchamiam ULEPSZONY serwer AIONS...
echo ----------------------------------------
python server\cbms_enhanced_server.py

pause