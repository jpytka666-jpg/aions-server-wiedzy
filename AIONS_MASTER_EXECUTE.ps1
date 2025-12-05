#!/usr/bin/env powershell
<#
AIONS MASTER - Complete Consolidation Script
Executes all 7 phases of the consolidation plan

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

# Configuration
$MasterRoot = "E:\AIONS_MASTER"
$DesktopProduction = "C:\Users\User\OneDrive - Global Banking School\Desktop\AIONS_CBMS_RELEASE_V3"
$AionsV10 = "E:\AIONS_V10"
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

    $versions = @("AIONS_CBMS_RELEASE_V0", "AIONS_CBMS_RELEASE_V1", "AIONS_CBMS_RELEASE_V2", "AIONS_CBMS_RELEASE_V3", "AIONS_CBMS_VANILA")

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

#==============================================================================
# PHASE 4: Copy Historical Projects (POLIPEK, MAIPA, etc.)
#==============================================================================

if (-not $SkipPhase4) {
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "PHASE 4: Copying Historical Projects (~15GB, ~15-20 min)" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "⚠️  NOTE: This phase requires access to Linux partition (/mnt/data)" -ForegroundColor Yellow
    Write-Host "    If paths are not accessible, this phase will be skipped." -ForegroundColor Yellow
    Write-Host ""

    $historicalProjects = @(
        @{ Name = "polipek_v1"; Source = "/mnt/data/AI DEVELOPMENT/WORK SPACE/IMPORT FROM _F/AI development project/v6/POLIPEK V1" },
        @{ Name = "maipa"; Source = "/mnt/data/home_marcin/MAIPA" },
        @{ Name = "aions_complete"; Source = "$Ajajaj/CBMS_RECOVERY/20251007_171234" },
        @{ Name = "cbms_pocket_qc_lab"; Source = "$Ajajaj/CBMS_RECOVERY/20251014_085423" }
    )

    foreach ($project in $historicalProjects) {
        $sourcePath = $project.Source
        $destPath = Join-Path (Join-Path $MasterRoot "history") $project.Name

        # Convert /mnt/data paths to Windows paths if needed
        if ($sourcePath -like "/mnt/*") {
            # Check if WSL is available
            if (Get-Command wsl.exe -ErrorAction SilentlyContinue) {
                if ($DryRun) {
                    Write-Host "[DRY RUN] Would copy from Linux partition:" -ForegroundColor Yellow
                    Write-Host "  From: $sourcePath" -ForegroundColor Yellow
                    Write-Host "  To: $destPath" -ForegroundColor Yellow
                } else {
                    Write-Host "  📦 Copying $($project.Name) from Linux partition..." -ForegroundColor Yellow
                    Write-Host "     (This may take several minutes)" -ForegroundColor Yellow

                    # Use WSL to access Linux filesystem
                    $wslPath = $sourcePath -replace '/mnt/', '//'
                    try {
                        $startTime = Get-Date
                        Copy-Item -Path "\\wsl$\Ubuntu$wslPath" -Destination $destPath -Recurse -Force -ErrorAction Stop
                        $elapsed = ((Get-Date) - $startTime).TotalSeconds
                        Write-Host "  ✅ Copied $($project.Name) ($(([Math]::Round($elapsed)))s)" -ForegroundColor Green
                    } catch {
                        Write-Host "  ⚠️  Failed to copy from Linux partition: $_" -ForegroundColor Yellow
                        Write-Host "     Skipping $($project.Name)" -ForegroundColor Yellow
                    }
                }
            } else {
                Write-Host "  ⚠️  WSL not available, skipping Linux partition: $($project.Name)" -ForegroundColor Yellow
            }
        } else {
            # Regular Windows path
            if (Test-Path $sourcePath) {
                if ($DryRun) {
                    Write-Host "[DRY RUN] Would copy:" -ForegroundColor Yellow
                    Write-Host "  From: $sourcePath" -ForegroundColor Yellow
                    Write-Host "  To: $destPath" -ForegroundColor Yellow
                } else {
                    Write-Host "  📦 Copying $($project.Name)..." -ForegroundColor Yellow
                    $startTime = Get-Date
                    Copy-Item -Path $sourcePath -Destination $destPath -Recurse -Force
                    $elapsed = ((Get-Date) - $startTime).TotalSeconds
                    Write-Host "  ✅ Copied $($project.Name) ($(([Math]::Round($elapsed)))s)" -ForegroundColor Green
                }
            } else {
                Write-Host "  ⚠️  Source not found: $sourcePath" -ForegroundColor Yellow
            }
        }
    }

    Write-Host ""
    Write-Host "✅ PHASE 4 COMPLETE" -ForegroundColor Green
    Write-Host ""
}

#==============================================================================
# PHASE 5: Copy Recovery Snapshots and Reports
#==============================================================================

if (-not $SkipPhase5) {
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "PHASE 5: Copying Recovery & Reports (~600MB, ~2-3 min)" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host ""

    # Recovery snapshots
    $recoverySource = Join-Path $Ajajaj "CBMS_RECOVERY"
    $recoveryDest = Join-Path $MasterRoot "recovery"

    if (Test-Path $recoverySource) {
        if ($DryRun) {
            Write-Host "[DRY RUN] Would copy recovery snapshots:" -ForegroundColor Yellow
            Write-Host "  From: $recoverySource" -ForegroundColor Yellow
            Write-Host "  To: $recoveryDest" -ForegroundColor Yellow
        } else {
            Write-Host "  📦 Copying recovery snapshots..." -ForegroundColor Yellow
            $startTime = Get-Date
            Copy-Item -Path "$recoverySource\*" -Destination $recoveryDest -Recurse -Force
            $elapsed = ((Get-Date) - $startTime).TotalSeconds
            Write-Host "  ✅ Copied recovery snapshots ($(([Math]::Round($elapsed)))s)" -ForegroundColor Green
        }
    }

    # Reports
    if (Test-Path $ReportsHome) {
        $reportsDest = Join-Path $MasterRoot "reports"
        if ($DryRun) {
            Write-Host "[DRY RUN] Would copy reports:" -ForegroundColor Yellow
            Write-Host "  From: $ReportsHome" -ForegroundColor Yellow
            Write-Host "  To: $reportsDest" -ForegroundColor Yellow
        } else {
            Write-Host "  📦 Copying reports..." -ForegroundColor Yellow
            $startTime = Get-Date
            Copy-Item -Path "$ReportsHome\*" -Destination $reportsDest -Recurse -Force
            $elapsed = ((Get-Date) - $startTime).TotalSeconds
            Write-Host "  ✅ Copied reports ($(([Math]::Round($elapsed)))s)" -ForegroundColor Green
        }
    }

    Write-Host ""
    Write-Host "✅ PHASE 5 COMPLETE" -ForegroundColor Green
    Write-Host ""
}

#==============================================================================
# PHASE 6: Generate Configuration Files
#==============================================================================

if (-not $SkipPhase6) {
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "PHASE 6: Generating Configuration Files" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host ""

    $configDir = Join-Path $MasterRoot "config"

    # aions_paths.json
    $pathsConfig = @{
        master_root = $MasterRoot
        production = @{
            path = Join-Path $MasterRoot "production"
            target = $DesktopProduction
            type = "symlink"
            status = "active"
        }
        versions = @{
            v0 = Join-Path (Join-Path $MasterRoot "versions") "AIONS_CBMS_RELEASE_V0"
            v1 = Join-Path (Join-Path $MasterRoot "versions") "AIONS_CBMS_RELEASE_V1"
            v2 = Join-Path (Join-Path $MasterRoot "versions") "AIONS_CBMS_RELEASE_V2"
            v3 = Join-Path (Join-Path $MasterRoot "versions") "AIONS_CBMS_RELEASE_V3"
            vanila = Join-Path (Join-Path $MasterRoot "versions") "AIONS_CBMS_VANILA"
        }
        plasters = @{
            "200g" = Join-Path (Join-Path $MasterRoot "plasters") "200g"
            howto = Join-Path (Join-Path $MasterRoot "plasters") "howto"
            programming = Join-Path (Join-Path $MasterRoot "plasters") "programming"
            general = Join-Path (Join-Path $MasterRoot "plasters") "general"
            claude = Join-Path (Join-Path $MasterRoot "plasters") "claude"
        }
        history = @{
            polipek_v1 = Join-Path (Join-Path $MasterRoot "history") "polipek_v1"
            maipa = Join-Path (Join-Path $MasterRoot "history") "maipa"
            aions_complete = Join-Path (Join-Path $MasterRoot "history") "aions_complete"
            cbms_pocket_qc_lab = Join-Path (Join-Path $MasterRoot "history") "cbms_pocket_qc_lab"
        }
    }

    $pathsJsonPath = Join-Path $configDir "aions_paths.json"
    if ($DryRun) {
        Write-Host "[DRY RUN] Would create: $pathsJsonPath" -ForegroundColor Yellow
    } else {
        $pathsConfig | ConvertTo-Json -Depth 5 | Set-Content $pathsJsonPath -Encoding UTF8
        Write-Host "  ✅ Created: aions_paths.json" -ForegroundColor Green
    }

    # aions_history.json
    $historyConfig = @{
        evolution = @(
            @{ name = "POLIPEK V1"; date = "2025-08-24"; description = "OpenCV-based vision system, early prototype" },
            @{ name = "MAIPA"; date = "2025-10-02"; description = "PyTorch/Transformers retrieval system, zero-training" },
            @{ name = "AIONS_COMPLETE"; date = "2025-09-07"; description = "Complete CBMS system backup" },
            @{ name = "CBMS_Pocket_QC_Lab"; date = "2025-10-14"; description = "QC validation laboratory" },
            @{ name = "AIONS_V10"; date = "2025-10-28"; description = "Current production (197 chunks, deterministic)" }
        )
        current_production = @{
            version = "AIONS_V10_V3"
            location = $DesktopProduction
            chunks = 197
            status = "operational"
        }
    }

    $historyJsonPath = Join-Path $configDir "aions_history.json"
    if ($DryRun) {
        Write-Host "[DRY RUN] Would create: $historyJsonPath" -ForegroundColor Yellow
    } else {
        $historyConfig | ConvertTo-Json -Depth 5 | Set-Content $historyJsonPath -Encoding UTF8
        Write-Host "  ✅ Created: aions_history.json" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "✅ PHASE 6 COMPLETE" -ForegroundColor Green
    Write-Host ""
}

#==============================================================================
# PHASE 7: Create Unified Launcher Scripts
#==============================================================================

if (-not $SkipPhase7) {
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "PHASE 7: Creating Unified Launcher Scripts" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host ""

    $scriptsDir = Join-Path $MasterRoot "scripts"

    # unified_start.ps1
    $unifiedStartContent = @"
# AIONS MASTER - Unified Startup Script
`$MasterRoot = "$MasterRoot"
`$ProductionPath = Join-Path `$MasterRoot "production"

Write-Host "Starting AIONS from MASTER..." -ForegroundColor Cyan
Set-Location `$ProductionPath\server
python -u cbms_direct_server.py
"@

    $unifiedStartPath = Join-Path $scriptsDir "unified_start.ps1"
    if ($DryRun) {
        Write-Host "[DRY RUN] Would create: unified_start.ps1" -ForegroundColor Yellow
    } else {
        $unifiedStartContent | Set-Content $unifiedStartPath -Encoding UTF8
        Write-Host "  ✅ Created: unified_start.ps1" -ForegroundColor Green
    }

    # inventory.ps1
    $inventoryContent = @"
# AIONS MASTER - System Inventory
`$MasterRoot = "$MasterRoot"

Write-Host "AIONS MASTER INVENTORY" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan
Write-Host ""

Get-ChildItem `$MasterRoot -Directory | ForEach-Object {
    Write-Host "`$(`$_.Name):" -ForegroundColor Yellow
    Get-ChildItem `$_.FullName | ForEach-Object {
        `$type = if (`$_.LinkType) { "[LINK]" } else { "" }
        Write-Host "  - `$(`$_.Name) `$type"
    }
    Write-Host ""
}
"@

    $inventoryPath = Join-Path $scriptsDir "inventory.ps1"
    if ($DryRun) {
        Write-Host "[DRY RUN] Would create: inventory.ps1" -ForegroundColor Yellow
    } else {
        $inventoryContent | Set-Content $inventoryPath -Encoding UTF8
        Write-Host "  ✅ Created: inventory.ps1" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "✅ PHASE 7 COMPLETE" -ForegroundColor Green
    Write-Host ""
}

#==============================================================================
# Final Summary
#==============================================================================

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
