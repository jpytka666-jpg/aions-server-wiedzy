# FULL_SCAN_C_DRIVE.ps1
# Skan dysku C:\ - uruchom w drugim oknie PowerShell

$OutputDir = "E:\server wiedzy\FULL_SCAN_C_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $OutputDir -Force

Write-Host "=== FULL C:\ SCAN ===" -ForegroundColor Green
Write-Host "Output: $OutputDir"
Write-Host "Start: $(Get-Date)"

# 1. C:\Users\User - wszystkie pliki kodu/danych
Write-Host "`n[1/4] C:\Users\User full scan..." -ForegroundColor Yellow  
Get-ChildItem -Path "C:\Users\User" -Recurse -File -ErrorAction SilentlyContinue |
    Select-Object FullName, Length, LastWriteTime, Extension |
    Export-Csv "$OutputDir\C_Users_User_ALL_FILES.csv" -NoTypeInformation

# 2. C:\Users\User foldery
Write-Host "`n[2/4] C:\Users\User folders..." -ForegroundColor Yellow
Get-ChildItem -Path "C:\Users\User" -Recurse -Directory -ErrorAction SilentlyContinue | 
    Select-Object FullName, CreationTime, LastWriteTime |
    Export-Csv "$OutputDir\C_Users_User_FOLDERS.csv" -NoTypeInformation

# 3. Caly C:\ - tylko foldery (szybciej)
Write-Host "`n[3/4] C:\ all folders (structure only)..." -ForegroundColor Yellow
Get-ChildItem -Path "C:\" -Recurse -Directory -Depth 5 -ErrorAction SilentlyContinue | 
    Select-Object FullName, CreationTime, LastWriteTime |
    Export-Csv "$OutputDir\C_drive_folders_depth5.csv" -NoTypeInformation

# 4. Wazne lokalizacje
Write-Host "`n[4/4] Important locations..." -ForegroundColor Yellow

$locations = @(
    "C:\Users\User\.codex",
    "C:\Users\User\.cursor", 
    "C:\Users\User\ContextVault",
    "C:\Users\User\AppData\Roaming\Claude",
    "C:\Users\User\AppData\Local\AnthropicClaude",
    "C:\Users\User\notes",
    "C:\Users\User\OneDrive - Global Banking School\Desktop"
)

foreach($loc in $locations) {
    if(Test-Path $loc) {
        $safeName = $loc -replace '[:\\]', '_'
        Write-Host "  Scanning: $loc" -ForegroundColor Gray
        Get-ChildItem -Path $loc -Recurse -File -ErrorAction SilentlyContinue |
            Select-Object FullName, Length, LastWriteTime |
            Export-Csv "$OutputDir\location_$safeName.csv" -NoTypeInformation
    }
}

# Summary
Write-Host "`n=== DONE ===" -ForegroundColor Green
Write-Host "Finish: $(Get-Date)"
Write-Host "Results in: $OutputDir"
Get-ChildItem $OutputDir | Format-Table Name, Length

Write-Host "`nNacisnij Enter aby zamknac..." -ForegroundColor Cyan
Read-Host
