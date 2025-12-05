# FULL_SCAN_AIONS.ps1
# Uruchom w PowerShell jako admin przed wyjściem

$OutputDir = "E:\server wiedzy\FULL_SCAN_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $OutputDir -Force

Write-Host "=== FULL AIONS SCAN ===" -ForegroundColor Green
Write-Host "Output: $OutputDir"
Write-Host "Start: $(Get-Date)"

# 1. Everything full export
Write-Host "`n[1/5] Everything export..." -ForegroundColor Yellow
& "C:\Program Files\Everything\es.exe" -export-csv "$OutputDir\everything_full.csv" *

# 2. Skan E:\ struktura
Write-Host "`n[2/5] E:\ tree scan..." -ForegroundColor Yellow
Get-ChildItem -Path "E:\" -Recurse -Directory -ErrorAction SilentlyContinue | 
    Select-Object FullName, CreationTime, LastWriteTime |
    Export-Csv "$OutputDir\E_drive_folders.csv" -NoTypeInformation

# 3. Skan C:\Users\User
Write-Host "`n[3/5] C:\Users\User scan..." -ForegroundColor Yellow  
Get-ChildItem -Path "C:\Users\User" -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Extension -match '\.(py|json|jsonl|md|txt|yaml|yml)$' } |
    Select-Object FullName, Length, LastWriteTime |
    Export-Csv "$OutputDir\C_user_files.csv" -NoTypeInformation

# 4. Wszystkie .json/.jsonl z rozmiarami
Write-Host "`n[4/5] All JSON/JSONL files..." -ForegroundColor Yellow
& "C:\Program Files\Everything\es.exe" "ext:json|jsonl" | 
    ForEach-Object { 
        $f = Get-Item $_ -ErrorAction SilentlyContinue
        if($f) { "$($f.Length),$_" }
    } | Out-File "$OutputDir\all_json_files.txt"

# 5. Wszystkie CBMS/AIONS related
Write-Host "`n[5/5] AIONS keywords scan..." -ForegroundColor Yellow
$keywords = @("CBMS", "AIONS", "CRLA", "plasters", "chunks", "korean", "thinking", "facts")
foreach($kw in $keywords) {
    & "C:\Program Files\Everything\es.exe" $kw | Out-File "$OutputDir\search_$kw.txt"
}

# Summary
Write-Host "`n=== DONE ===" -ForegroundColor Green
Write-Host "Finish: $(Get-Date)"
Write-Host "Results in: $OutputDir"
Get-ChildItem $OutputDir | Format-Table Name, Length

Write-Host "`nNacisnij Enter aby zamknac..." -ForegroundColor Cyan
Read-Host
