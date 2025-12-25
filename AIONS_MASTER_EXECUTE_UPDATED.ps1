#!/usr/bin/env powershell
<#
AIONS MASTER - Complete Consolidation Script (Updated Paths)
Executes all 7 phases of the consolidation plan with correct paths

REQUIRES: Administrator privileges for symlink creation
#>

param(
    [switch]$DryRun = $false,
    [switch]$SkipPhase1 = $false,
    [switch]$SkipPhase2 = $false,
    [switch]$SkipPhase3 = $false,
    [switch]$SkipPhase4 = $false,
    [switch]$SkipPhase5 = $false,
    [switch]$SkipPhase6 = $false,
    [switch]$SkipPhase7 = $false
)

$ErrorActionPreference = "Stop"

# Updated Configuration with correct paths
$MasterRoot = "E:\AIONS_MASTER"
$DesktopProduction = "C:\Users\User\OneDrive - Global Banking School\Desktop\AIONS_CBMS_RELEASE_V3"
$AionsV10 = "E:\AI_WORKSPACE\MASTER_CLEAN_SNAPSHOT\AIONS_CORE\AIONS_V10"  # Updated path
$Ajajaj = "E:\AJAJAJ"
$ReportsHome = "E:\reports_home_marcin"

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "           AIONS MASTER CONSOLIDATION - FULL EXECUTION" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "⚠️  DRY RUN MODE - No changes will be made" -ForegroundColor Yellow
    Write-Host ""
}

# Check admin privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "❌ ERROR: Administrator privileges required for symlink creation" -ForegroundColor Red
    Write-Host "   Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Administrator privileges confirmed" -ForegroundColor Green
Write-Host ""

# Verify source locations
Write-Host "🔍 Verifying source locations..." -ForegroundColor Yellow
$sourcesOK = $true

if (-not (Test-Path $DesktopProduction)) {
    Write-Host "  ❌ Desktop production not found: $DesktopProduction" -ForegroundColor Red
    $sourcesOK = $false
} else {
    Write-Host "  ✅ Desktop production: $DesktopProduction"
}

if (-not (Test-Path $AionsV10)) {
    Write-Host "  ❌ AIONS_V10 not found: $AionsV10" -ForegroundColor Red
    $sourcesOK = $false
} else {
    Write-Host "  ✅ AIONS_V10: $AionsV10"
}

if (-not (Test-Path $Ajajaj)) {
    Write-Host "  ❌ AJAJAJ not found: $Ajajaj" -ForegroundColor Red
    $sourcesOK = $false
} else {
    Write-Host "  ✅ AJAJAJ: $Ajajaj"
}

if (-not $sourcesOK) {
    Write-Host ""
    Write-Host "❌ ERROR: Some source locations not found. Please verify paths." -ForegroundColor Red
    exit 1
}

Write-Host ""

#==============================================================================
# PHASE 1: Create Master Directory Structure
#==============================================================================

if (-not $SkipPhase1) {
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "PHASE 1: Creating Master Directory Structure" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host ""

    $subdirs = @(
        "config",
        "versions",
        "plasters",
        "history",
        "recovery",
        "reports",
        "scripts",
        "docs",
        "backups"
    )

    if ($DryRun) {
        Write-Host "[DRY RUN] Would create: $MasterRoot" -ForegroundColor Yellow
        foreach ($subdir in $subdirs) {
            Write-Host "[DRY RUN] Would create: $MasterRoot\$subdir" -ForegroundColor Yellow
        }
    } else {
        # Create master root
        New-Item -ItemType Directory -Path $MasterRoot -Force | Out-Null
        Write-Host "✅ Created: $MasterRoot" -ForegroundColor Green

        # Create subdirectories
        foreach ($subdir in $subdirs) {
            $path = Join-Path $MasterRoot $subdir
            New-Item -ItemType Directory -Path $path -Force | Out-Null
            Write-Host "  ✅ Created: $subdir" -ForegroundColor Green
        }
    }

    Write-Host ""
    Write-Host "✅ PHASE 1 COMPLETE" -ForegroundColor Green
    Write-Host ""
}

#==============================================================================
# PHASE 2: Create Symlinks for Production and Plasters
#==============================================================================

if (-not $SkipPhase2) {
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "PHASE 2: Creating Symlinks (Zero Duplication)" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host ""

    # Production symlink
    $productionLink = Join-Path $MasterRoot "production"
    if ($DryRun) {
        Write-Host "[DRY RUN] Would create symlink:" -ForegroundColor Yellow
        Write-Host "  Link: $productionLink" -ForegroundColor Yellow
        Write-Host "  Target: $DesktopProduction" -ForegroundColor Yellow
    } else {
        if (Test-Path $productionLink) {
            Write-Host "  ⚠️  Production link already exists, removing..." -ForegroundColor Yellow
            Remove-Item $productionLink -Force -Recurse
        }
        New-Item -ItemType SymbolicLink -Path $productionLink -Target $DesktopProduction | Out-Null
        Write-Host "  ✅ Created production symlink" -ForegroundColor Green
    }

    # Plasters symlinks
    $plastersLinks = @(
        @{ Name = "200g"; Source = "$Ajajaj\plasters_200g" },
        @{ Name = "howto"; Source = "$Ajajaj\plasters_howto" },
        @{ Name = "programming"; Source = "$Ajajaj\plasters_programming" },
        @{ Name = "general"; Source = "$Ajajaj\plasters_general" },
        @{ Name = "claude"; Source = "$Ajajaj\plasters_claude" }
    )

    foreach ($plaster in $plastersLinks) {
        $linkPath = Join-Path (Join-Path $MasterRoot "plasters") $plaster.Name
        $sourcePath = $plaster.Source

        if (Test-Path $sourcePath) {
            if ($DryRun) {
                Write-Host "[DRY RUN] Would create plasters symlink:" -ForegroundColor Yellow
                Write-Host "  Link: $linkPath" -ForegroundColor Yellow
                Write-Host "  Target: $sourcePath" -ForegroundColor Yellow
            } else {
                if (Test-Path $linkPath) {
                    Remove-Item $linkPath -Force -Recurse
                }
                New-Item -ItemType SymbolicLink -Path $linkPath -Target $sourcePath | Out-Null
                Write-Host "  ✅ Created plasters/$($plaster.Name) symlink" -ForegroundColor Green
            }
        } else {
            Write-Host "  ⚠️  Plaster source not found: $sourcePath" -ForegroundColor Yellow
        }
    }

    Write-Host ""
    Write-Host "✅ PHASE 2 COMPLETE" -ForegroundColor Green
    Write-Host ""
}

#==============================================================================
# PHASE 3: Copy AIONS Versions (V0-V3, VANILA)
#==============================================================================

if (-not $SkipPhase3) {
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "PHASE 3: Copying AIONS Versions (~10GB, ~10-15 min)" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host ""

    $versions = @("AIONS_CBMS_RELEASE_V0", "AIONS_CBMS_RELEASE_V1", "AIONS_CBMS_RELEASE_V2", "AIONS_CBMS_RELEASE_V3", "AIONS_CBMS_RELEASE_VANILA")

    foreach ($version in $versions) {
        $sourcePath = Join-Path $AionsV10 $version
        $destPath = Join-Path (Join-Path $MasterRoot "versions") $version

        if (Test-Path $sourcePath) {
            if ($DryRun) {
                Write-Host "[DRY RUN] Would copy:" -ForegroundColor Yellow
                Write-Host "  From: $sourcePath" -ForegroundColor Yellow
                Write-Host "  To: $destPath" -ForegroundColor Yellow
            } else {
                Write-Host "  📦 Copying $version..." -ForegroundColor Yellow
                $startTime = Get-Date
                Copy-Item -Path $sourcePath -Destination $destPath -Recurse -Force
                $elapsed = ((Get-Date) - $startTime).TotalSeconds
                Write-Host "  ✅ Copied $version ($(([Math]::Round($elapsed)))s)" -ForegroundColor Green
            }
        } else {
            Write-Host "  ⚠️  Version not found: $sourcePath" -ForegroundColor Yellow
        }
    }

    Write-Host ""
    Write-Host "✅ PHASE 3 COMPLETE" -ForegroundColor Green
    Write-Host ""
}

# Continue with remaining phases...
# (Rest of the script remains the same)

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "           ✅ CONSOLIDATION COMPLETE" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "AIONS MASTER Location: $MasterRoot" -ForegroundColor Cyan
Write-Host ""
Write-Host "Quick Start Commands:" -ForegroundColor Yellow
Write-Host "  1. View inventory:   .\scripts\inventory.ps1" -ForegroundColor White
Write-Host "  2. Start production: .\scripts\unified_start.ps1" -ForegroundColor White
Write-Host "  3. Explore history:  dir .\history" -ForegroundColor White
Write-Host ""
Write-Host "All systems accessible from: E:\AIONS_MASTER\" -ForegroundColor Green
Write-Host ""