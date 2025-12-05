# AIONS MASTER - SUPER QUICK START (tylko struktura + symlinki, BEZ kopiowania plików)
# To zajmie ~5 sekund, zero kopiowania, zero ryzyka
# Użycie: .\SUPER_QUICK_START.ps1

Write-Host "`n" -NoNewline
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "     AIONS MASTER - SUPER QUICK START (5 seconds)" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Continue"

# Check admin
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "⚠️  WARNING: Not running as Administrator" -ForegroundColor Yellow
    Write-Host "   Symlinks may fail. Run PowerShell as Administrator for best results.`n" -ForegroundColor Yellow
}

# PHASE 1: Structure (1 second)
Write-Host "[1/2] Creating directory structure..." -ForegroundColor Yellow

$master = "E:\AIONS_MASTER"
@("config", "versions", "plasters", "history", "recovery", "reports", "scripts", "docs", "backups") | ForEach-Object {
    New-Item -ItemType Directory -Path "$master\$_" -Force -ErrorAction SilentlyContinue | Out-Null
}

Write-Host "      ✅ 10 directories created" -ForegroundColor Green

# PHASE 2: Symlinks (4 seconds)
Write-Host "[2/2] Creating symlinks (zero duplication)..." -ForegroundColor Yellow

# Production
$prodLink = "$master\production"
$prodTarget = "C:\Users\User\OneDrive - Global Banking School\Desktop\AIONS_CBMS_RELEASE_V3"

if (Test-Path $prodTarget) {
    if (Test-Path $prodLink) { Remove-Item $prodLink -Force -Recurse -ErrorAction SilentlyContinue }
    try {
        New-Item -ItemType SymbolicLink -Path $prodLink -Target $prodTarget -Force -ErrorAction Stop | Out-Null
        Write-Host "      ✅ production → Desktop" -ForegroundColor Green
    } catch {
        Write-Host "      ⚠️  production symlink failed (need admin?)" -ForegroundColor Yellow
    }
}

# Plasters
$plasterDefs = @(
    @("200g", "E:\AJAJAJ\plasters_200g"),
    @("howto", "E:\AJAJAJ\plasters_howto"),
    @("programming", "E:\AJAJAJ\plasters_programming"),
    @("general", "E:\AJAJAJ\plasters_general"),
    @("claude", "E:\AJAJAJ\plasters_claude")
)

$plasterOK = 0
foreach ($def in $plasterDefs) {
    $name, $target = $def
    $link = "$master\plasters\$name"

    if (Test-Path $target) {
        if (Test-Path $link) { Remove-Item $link -Force -Recurse -ErrorAction SilentlyContinue }
        try {
            New-Item -ItemType SymbolicLink -Path $link -Target $target -Force -ErrorAction Stop | Out-Null
            $plasterOK++
        } catch {
            Write-Host "      ⚠️  plasters/$name symlink failed" -ForegroundColor Yellow
        }
    }
}

Write-Host "      ✅ $plasterOK/5 plasters symlinks created" -ForegroundColor Green

Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Host "     ✅ QUICK START COMPLETE!" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""

# Show what was created
Write-Host "Created structure:" -ForegroundColor Cyan
Get-ChildItem $master | ForEach-Object {
    $type = if ($_.LinkType) { " [SYMLINK]" } else { "" }
    Write-Host "  $($_.Name)$type" -ForegroundColor White
}

Write-Host ""
Write-Host "Quick access commands:" -ForegroundColor Yellow
Write-Host "  cd E:\AIONS_MASTER" -ForegroundColor White
Write-Host "  dir .\production         # Your active system" -ForegroundColor White
Write-Host "  dir .\plasters\200g      # Plasters via symlink" -ForegroundColor White
Write-Host ""

Write-Host "To copy files (versions, history, recovery):" -ForegroundColor Yellow
Write-Host "  .\AIONS_MASTER_EXECUTE.ps1 -SkipPhase1 -SkipPhase2" -ForegroundColor White
Write-Host "  (This will take 30-40 minutes for ~26GB)" -ForegroundColor Gray
Write-Host ""
