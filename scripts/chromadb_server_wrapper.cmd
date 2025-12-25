@echo off
REM ChromaDB HTTP Server Wrapper for Scheduled Task
cd /d "E:\server wiedzy"
"E:\server wiedzy\venv\Scripts\chroma.exe" run --host 0.0.0.0 --port 8000 --path "E:\server wiedzy\data\chroma"
