<#
.SYNOPSIS
    Start ChromaDB HTTP Server with CORS enabled for GUI access

.DESCRIPTION
    Enables CORS so that web-based GUI tools like chroma-ui.vercel.app can connect.
#>

$env:CHROMA_SERVER_CORS_ALLOW_ORIGINS = '["*"]'
$chromaExe = "E:\server wiedzy\venv\Scripts\chroma.exe"
$chromaPath = "E:\server wiedzy\data\chroma"

Write-Host "[CHROMADB] Starting with CORS enabled for all origins..." -ForegroundColor Cyan
Write-Host "[CHROMADB] GUI access: https://chroma-ui.vercel.app/" -ForegroundColor Gray

& $chromaExe run --host 0.0.0.0 --port 8000 --path $chromaPath
