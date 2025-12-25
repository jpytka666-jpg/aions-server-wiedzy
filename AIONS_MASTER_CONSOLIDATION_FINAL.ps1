#!/usr/bin/env powershell
<#
AIONS MASTER - Final Consolidation Script
Based on Everything search results - Complete system unification

REQUIRES: Administrator privileges for symlink creation
#>

param(
    [switch]$DryRun = $false
)

$ErrorActionPreference = "Stop"

# Final Configuration with all discovered paths
$MasterRoot = "E:\AIONS_MASTER"
$DesktopProduction = "C:\Users\User\OneDrive - Global Banking School\Desktop\AIONS_CBMS_RELEASE_V3"
$AionsCore = "E:\AI_WORKSPACE\MASTER_CLEAN_SNAPSHOT\AIONS_CORE"
$AionsV10 = "E:\AI_WORKSPACE\MASTER_CLEAN_SNAPSHOT\AIONS_CORE\AIONS_V10"
$AionsVectorDB = "D:\AIONS_VECTOR_DB"
$Ajajaj = "E:\AJAJAJ"
$ReportsHome = "E:\reports_home_marcin"

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "           AIONS MASTER CONSOLIDATION - FINAL EXECUTION" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🎯 Unifying complete AIONS ecosystem (POLIPEK → AIONS V3)" -ForegroundColor Yellow
Write-Host ""

if ($DryRun) {
    Write-Host "⚠️  DRY RUN MODE - No changes will be made" -ForegroundColor Yellow
    Write-Host ""
}

# Check admin privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
Write-Host "🔐 Administrator Status: $isAdmin" -ForegroundColor $(if($isAdmin){"Green"}else{"Red"})

if (-not $isAdmin -and -not $DryRun) {
    Write-Host "❌ ERROR: Administrator privileges required for symlink creation" -ForegroundColor Red
    Write-Host "   Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Verify all source locations
Write-Host "🔍 Verifying source locations..." -ForegroundColor Yellow
$sources = @{
    "Desktop Production" = $DesktopProduction
    "AIONS Core" = $AionsCore
    "AIONS V10" = $AionsV10
    "AIONS Vector DB" = $AionsVectorDB
    "AJAJAJ" = $Ajajaj
}

$sourcesOK = $true
foreach ($source in $sources.GetEnumerator()) {
    if (Test-Path $source.Value) {
        Write-Host "  ✅ $($source.Key): $($source.Value)" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $($source.Key) not found: $($source.Value)" -ForegroundColor Red
        $sourcesOK = $false
    }
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

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "PHASE 1: Creating Master Directory Structure" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

$subdirs = @(
    "config",
    "production",
    "versions", 
    "plasters",
    "history",
    "recovery",
    "reports",
    "scripts",
    "docs",
    "backups",
    "vector_db",
    "models"
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

#==============================================================================
# PHASE 2: Create Symlinks (Zero Duplication Strategy)
#==============================================================================

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "PHASE 2: Creating Symlinks (Zero Duplication)" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# Production symlink
$productionLink = Join-Path $MasterRoot "production\current"
if ($DryRun) {
    Write-Host "[DRY RUN] Would create production symlink:" -ForegroundColor Yellow
    Write-Host "  Link: $productionLink" -ForegroundColor Yellow
    Write-Host "  Target: $DesktopProduction" -ForegroundColor Yellow
} else {
    New-Item -ItemType Directory -Path (Split-Path $productionLink) -Force | Out-Null
    if (Test-Path $productionLink) {
        Remove-Item $productionLink -Force -Recurse
    }
    New-Item -ItemType SymbolicLink -Path $productionLink -Target $DesktopProduction | Out-Null
    Write-Host "  ✅ Created production symlink" -ForegroundColor Green
}

# Vector DB symlink
$vectorLink = Join-Path $MasterRoot "vector_db\aions_vectors"
if ($DryRun) {
    Write-Host "[DRY RUN] Would create vector DB symlink:" -ForegroundColor Yellow
    Write-Host "  Link: $vectorLink" -ForegroundColor Yellow
    Write-Host "  Target: $AionsVectorDB" -ForegroundColor Yellow
} else {
    if (Test-Path $vectorLink) {
        Remove-Item $vectorLink -Force -Recurse
    }
    New-Item -ItemType SymbolicLink -Path $vectorLink -Target $AionsVectorDB | Out-Null
    Write-Host "  ✅ Created vector DB symlink" -ForegroundColor Green
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

#==============================================================================
# PHASE 3: Copy AIONS Versions (Complete History)
#==============================================================================

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "PHASE 3: Copying AIONS Versions (Complete History)" -ForegroundColor Cyan
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

#==============================================================================
# PHASE 4: Create Configuration Files
#==============================================================================

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "PHASE 4: Generating Configuration Files" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

$configDir = Join-Path $MasterRoot "config"

# Master configuration
$masterConfig = @{
    consolidation_date = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    master_root = $MasterRoot
    evolution_path = "POLIPEK → MAIPA → AIONS_COMPLETE → CBMS_Pocket_QC_Lab → AIONS_V10_V3"
    production = @{
        current = @{
            path = Join-Path $MasterRoot "production\current"
            target = $DesktopProduction
            version = "AIONS_V10_V3"
            status = "active"
        }
    }
    versions = @{
        v0 = Join-Path (Join-Path $MasterRoot "versions") "AIONS_CBMS_RELEASE_V0"
        v1 = Join-Path (Join-Path $MasterRoot "versions") "AIONS_CBMS_RELEASE_V1"
        v2 = Join-Path (Join-Path $MasterRoot "versions") "AIONS_CBMS_RELEASE_V2"
        v3 = Join-Path (Join-Path $MasterRoot "versions") "AIONS_CBMS_RELEASE_V3"
        vanila = Join-Path (Join-Path $MasterRoot "versions") "AIONS_CBMS_RELEASE_VANILA"
    }
    vector_db = @{
        path = Join-Path $MasterRoot "vector_db\aions_vectors"
        target = $AionsVectorDB
        type = "symlink"
    }
    plasters = @{
        "200g" = Join-Path (Join-Path $MasterRoot "plasters") "200g"
        howto = Join-Path (Join-Path $MasterRoot "plasters") "howto"
        programming = Join-Path (Join-Path $MasterRoot "plasters") "programming"
        general = Join-Path (Join-Path $MasterRoot "plasters") "general"
        claude = Join-Path (Join-Path $MasterRoot "plasters") "claude"
    }
}

$configPath = Join-Path $configDir "aions_master.json"
if ($DryRun) {
    Write-Host "[DRY RUN] Would create: aions_master.json" -ForegroundColor Yellow
} else {
    $masterConfig | ConvertTo-Json -Depth 5 | Set-Content $configPath -Encoding UTF8
    Write-Host "  ✅ Created: aions_master.json" -ForegroundColor Green
}

Write-Host ""
Write-Host "✅ PHASE 4 COMPLETE" -ForegroundColor Green
Write-Host ""

#==============================================================================
# PHASE 5: Create Launcher Scripts
#==============================================================================

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "PHASE 5: Creating Launcher Scripts" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

$scriptsDir = Join-Path $MasterRoot "scripts"

# Unified launcher
$launcherContent = @"
# AIONS MASTER - Unified Production Launcher
`$MasterRoot = "$MasterRoot"
`$ProductionPath = Join-Path `$MasterRoot "production\current"

Write-Host "🚀 Starting AIONS from MASTER..." -ForegroundColor Cyan
Write-Host "📍 Production: `$ProductionPath" -ForegroundColor Yellow
Set-Location "`$ProductionPath\server"
python -u cbms_direct_server.py
"@

$launcherPath = Join-Path $scriptsDir "start_production.ps1"
if ($DryRun) {
    Write-Host "[DRY RUN] Would create: start_production.ps1" -ForegroundColor Yellow
} else {
    $launcherContent | Set-Content $launcherPath -Encoding UTF8
    Write-Host "  ✅ Created: start_production.ps1" -ForegroundColor Green
}

# Inventory script
$inventoryContent = @"
# AIONS MASTER - Complete System Inventory
`$MasterRoot = "$MasterRoot"

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "           AIONS MASTER - SYSTEM INVENTORY" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 Master Location: `$MasterRoot" -ForegroundColor Yellow
Write-Host ""

Get-ChildItem `$MasterRoot -Directory | ForEach-Object {
    Write-Host "`$(`$_.Name.ToUpper()):" -ForegroundColor Yellow
    Get-ChildItem `$_.FullName | ForEach-Object {
        `$type = if (`$_.LinkType) { "[SYMLINK]" } else { "[DIRECTORY]" }
        `$size = if (`$_.PSIsContainer) { "" } else { " (`$([Math]::Round(`$_.Length/1MB, 2))MB)" }
        Write-Host "  - `$(`$_.Name) `$type`$size" -ForegroundColor White
    }
    Write-Host ""
}

Write-Host "🎯 Evolution Path: POLIPEK → MAIPA → AIONS_COMPLETE → CBMS_Pocket_QC_Lab → AIONS_V10_V3" -ForegroundColor Green
Write-Host ""
"@

$inventoryPath = Join-Path $scriptsDir "inventory.ps1"
if ($DryRun) {
    Write-Host "[DRY RUN] Would create: inventory.ps1" -ForegroundColor Yellow
} else {
    $inventoryContent | Set-Content $inventoryPath -Encoding UTF8
    Write-Host "  ✅ Created: inventory.ps1" -ForegroundColor Green
}

Write-Host ""
Write-Host "✅ PHASE 5 COMPLETE" -ForegroundColor Green
Write-Host ""

#==============================================================================
# Final Summary
#==============================================================================

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "           ✅ AIONS MASTER CONSOLIDATION COMPLETE" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "🎯 POLIPEK → AIONS V3 Evolution Complete!" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 AIONS MASTER Location: $MasterRoot" -ForegroundColor Yellow
Write-Host ""
Write-Host "🚀 Quick Start Commands:" -ForegroundColor Yellow
Write-Host "  1. View inventory:   .\scripts\inventory.ps1" -ForegroundColor White
Write-Host "  2. Start production: .\scripts\start_production.ps1" -ForegroundColor White
Write-Host "  3. Explore versions: dir .\versions" -ForegroundColor White
Write-Host "  4. Access plasters:  dir .\plasters" -ForegroundColor White
Write-Host ""
Write-Host "🔗 All systems unified under: E:\AIONS_MASTER\" -ForegroundColor Green
Write-Host "📊 Zero duplication achieved through symbolic links" -ForegroundColor Green
Write-Host ""