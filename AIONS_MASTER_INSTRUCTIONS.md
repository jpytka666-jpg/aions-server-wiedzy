# AIONS MASTER Consolidation - Quick Start Instructions

## Overview

The consolidation script `AIONS_MASTER_EXECUTE.ps1` is ready to unify all your AIONS projects into a single location: **E:\AIONS_MASTER\**

## Prerequisites

✅ **Administrator privileges required** (for symlink creation)
✅ **~26GB free space on E:\ drive** (you have 500GB+)
✅ **45-75 minutes execution time** estimated

## Quick Start

### Option 1: Full Consolidation (Recommended)

```powershell
# Open PowerShell AS ADMINISTRATOR
cd E:\
.\AIONS_MASTER_EXECUTE.ps1
```

This will execute all 7 phases automatically.

### Option 2: Dry Run First (Test Without Changes)

```powershell
# Test the script without making any changes
.\AIONS_MASTER_EXECUTE.ps1 -DryRun
```

### Option 3: Selective Phases

```powershell
# Skip specific phases if needed
.\AIONS_MASTER_EXECUTE.ps1 -SkipPhase4  # Skip Linux partition copy
.\AIONS_MASTER_EXECUTE.ps1 -SkipPhase3 -SkipPhase4  # Skip versions and history
```

## What Will Happen

### Phase 1: Directory Structure (~1 second)
Creates E:\AIONS_MASTER\ with 9 subdirectories:
- config/
- production/
- versions/
- plasters/
- history/
- recovery/
- reports/
- scripts/
- docs/
- backups/

### Phase 2: Symlinks (~5 seconds, 0 GB)
Creates symbolic links (no duplication):
- production → C:\Users\User\...\Desktop\AIONS_CBMS_RELEASE_V3
- plasters/200g → E:\AJAJAJ\plasters_200g
- plasters/howto → E:\AJAJAJ\plasters_howto
- plasters/programming → E:\AJAJAJ\plasters_programming
- plasters/general → E:\AJAJAJ\plasters_general
- plasters/claude → E:\AJAJAJ\plasters_claude

### Phase 3: AIONS Versions (~10-15 minutes, ~10GB)
Copies all 5 AIONS versions:
- AIONS_CBMS_RELEASE_V0
- AIONS_CBMS_RELEASE_V1
- AIONS_CBMS_RELEASE_V2
- AIONS_CBMS_RELEASE_V3
- AIONS_CBMS_VANILA

### Phase 4: Historical Projects (~15-20 minutes, ~15GB)
Copies predecessor systems:
- POLIPEK V1 (from Linux partition if accessible)
- MAIPA (from Linux partition if accessible)
- AIONS_COMPLETE (from recovery)
- CBMS_Pocket_QC_Lab (from recovery)

**Note:** If Linux partition (/mnt/data) is not accessible via WSL, these will be skipped with warnings.

### Phase 5: Recovery & Reports (~2-3 minutes, ~600MB)
Copies:
- All CBMS_RECOVERY snapshots
- All audit reports

### Phase 6: Configuration Files (~1 second)
Generates:
- config/aions_paths.json (path mappings)
- config/aions_history.json (evolution timeline)

### Phase 7: Launcher Scripts (~1 second)
Creates:
- scripts/unified_start.ps1 (start production server)
- scripts/inventory.ps1 (view all systems)

## After Consolidation

### Access Everything from One Place

```powershell
cd E:\AIONS_MASTER

# View inventory
.\scripts\inventory.ps1

# Start production server
.\scripts\unified_start.ps1

# Browse history
dir .\history

# Explore versions
dir .\versions

# Access plasters (via symlinks)
dir .\plasters\200g
```

### What Gets Preserved

✅ **Original files untouched**: All symlinked files remain in original locations
✅ **Production copy intact**: Desktop AIONS remains fully functional
✅ **All plasters accessible**: Via symlinks, no duplication
✅ **Complete history**: All predecessor systems preserved
✅ **Recovery snapshots**: Full backup history maintained

### Rollback Plan

If anything goes wrong:
1. Original Desktop AIONS: **Untouched**
2. Original AJAJAJ plasters: **Untouched**
3. Original AIONS_V10: **Untouched**
4. Simply delete E:\AIONS_MASTER\ and you're back to the original state

## Troubleshooting

### "Administrator privileges required"
- Right-click PowerShell icon
- Select "Run as Administrator"
- Navigate to E:\ and run script again

### "Source not found" warnings
- Some paths may not exist on your system
- Script will skip missing sources and continue
- Check warnings at the end to see what was skipped

### Linux partition not accessible
- Phase 4 requires WSL to access /mnt/data
- If WSL is not available, POLIPEK and MAIPA copies will be skipped
- You can manually copy these later if needed

### Script takes longer than expected
- Large file copies (especially plasters) can be slow
- Progress is shown for each phase
- Safe to let it run unattended

## Current System Status

**Production:** C:\Users\User\OneDrive - Global Banking School\Desktop\AIONS_CBMS_RELEASE_V3
- ✅ 197 chunks loaded
- ✅ Deterministic system
- ✅ 100,000+ queries logged
- ✅ Fully operational

**Scattered Locations:**
- E:\AIONS_V10\ (5 versions)
- E:\AJAJAJ\ (plasters + recovery)
- Linux /mnt/data\ (POLIPEK, MAIPA)
- E:\reports_home_marcin\ (audit reports)

**After Consolidation:**
- E:\AIONS_MASTER\ (everything accessible)

## Ready to Begin?

```powershell
# Test first (dry run)
.\AIONS_MASTER_EXECUTE.ps1 -DryRun

# When ready, execute for real
.\AIONS_MASTER_EXECUTE.ps1
```

---

**Status:** ✅ READY FOR EXECUTION

**Files Created:**
- `E:\AIONS_MASTER_EXECUTE.ps1` - Main consolidation script
- `E:\AIONS_MASTER_CONSOLIDATION_PLAN.md` - Detailed plan document
- `E:\AIONS_MASTER_INSTRUCTIONS.md` - This file

**Next Step:** Open PowerShell as Administrator and run `.\AIONS_MASTER_EXECUTE.ps1`
