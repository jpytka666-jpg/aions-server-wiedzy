@echo off
setlocal
cd /d "%~dp0"

set "PYEXE=E:\server wiedzy\venv\Scripts\python.exe"

if not exist "%PYEXE%" (
    echo [AIONS Chat] Nie znaleziono Pythona pod: %PYEXE%
    echo Sprawdz sciezke venv i sprobuj ponownie.
    pause
    exit /b 1
)

echo [AIONS Chat] Uruchamiam serwer...
echo (Jesli nie ma pywebview, otworzy sie domyslna przegladarka pod http://127.0.0.1:8770)
echo Aby zatrzymac serwer, zamknij to okno lub wcisnij Ctrl+C.
echo.

"%PYEXE%" server.py

echo.
echo [AIONS Chat] Serwer zatrzymany.
pause
