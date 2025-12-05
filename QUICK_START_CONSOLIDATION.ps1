# AIONS MASTER - Quick Start Consolidation
# Prosty skrypt do szybkiego uruchomienia konsolidacji
# Użycie: .\QUICK_START_CONSOLIDATION.ps1

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  AIONS MASTER - Quick Start" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Phase 1: Create structure (fast, ~1 second)
Write-Host "Phase 1: Creating directory structure..." -ForegroundColor Yellow

$dirs = @(
    "E:\AIONS_MASTER",
    "E:\AIONS_MASTER\config",
    "E:\AIONS_MASTER\versions",
    "E:\AIONS_MASTER\plasters",
    "E:\AIONS_MASTER\history",
    "E:\AIONS_MASTER\recovery",
    "E:\AIONS_MASTER\reports",
    "E:\AIONS_MASTER\scripts",
    "E:\AIONS_MASTER\docs",
    "E:\AIONS_MASTER\backups"
)

foreach ($dir in $dirs) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
}

Write-Host "✅ Structure created!`n" -ForegroundColor Green

# Phase 2: Create symlinks (fast, ~5 seconds)
Write-Host "Phase 2: Creating symlinks..." -ForegroundColor Yellow

# Production symlink
$prodLink = "E:\AIONS_MASTER\production"
$prodTarget = "C:\Users\User\OneDrive - Global Banking School\Desktop\AIONS_CBMS_RELEASE_V3"

if (Test-Path $prodTarget) {
    New-Item -ItemType SymbolicLink -Path $prodLink -Target $prodTarget -Force | Out-Null
    Write-Host "✅ Production symlink created" -ForegroundColor Green
} else {
    Write-Host "⚠️  Production target not found: $prodTarget" -ForegroundColor Yellow
}

# Plasters symlinks
$plasters = @{
    "200g" = "E:\AJAJAJ\plasters_200g"
    "howto" = "E:\AJAJAJ\plasters_howto"
    "programming" = "E:\AJAJAJ\plasters_programming"
    "general" = "E:\AJAJAJ\plasters_general"
    "claude" = "E:\AJAJAJ\plasters_claude"
}

foreach ($name in $plasters.Keys) {
    $linkPath = "E:\AIONS_MASTER\plasters\$name"
    $targetPath = $plasters[$name]

    if (Test-Path $targetPath) {
        New-Item -ItemType SymbolicLink -Path $linkPath -Target $targetPath -Force | Out-Null
        Write-Host "✅ Plasters/$name symlink created" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Plaster not found: $targetPath" -ForegroundColor Yellow
    }
}

Write-Host "`n✅ Phase 1-2 COMPLETE (symlinks ready)`n" -ForegroundColor Green

# Ask about Phase 3-7 (file copying - slower)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Next: Phases 3-7 (copying files)" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "This will copy:" -ForegroundColor Yellow
Write-Host "  - 5 AIONS versions (~10GB, 10-15 min)"
Write-Host "  - Historical projects (~15GB, 15-20 min)"
Write-Host "  - Recovery & reports (~600MB, 2-3 min)"
Write-Host "  - Total: ~26GB, 30-40 minutes`n"

$continue = Read-Host "Continue with file copying? (Y/N)"

if ($continue -eq 'Y' -or $continue -eq 'y') {
    Write-Host "`nStarting file copy phases...`n" -ForegroundColor Green

    # Execute full script
    & "E:\AIONS_MASTER_EXECUTE.ps1" -SkipPhase1 -SkipPhase2

} else {
    Write-Host "`nStopped after Phase 1-2." -ForegroundColor Yellow
    Write-Host "To continue later, run:" -ForegroundColor Cyan
    Write-Host "  .\AIONS_MASTER_EXECUTE.ps1 -SkipPhase1 -SkipPhase2`n" -ForegroundColor White

    Write-Host "Current status:" -ForegroundColor Cyan
    Write-Host "✅ Directory structure: CREATED"
    Write-Host "✅ Production symlink: CREATED"
    Write-Host "✅ Plasters symlinks: CREATED"
    Write-Host "⏸️  File copies: PENDING`n"
}
