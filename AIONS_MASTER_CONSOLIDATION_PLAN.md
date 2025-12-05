# AIONS MASTER - Complete Consolidation Plan

**Generated:** 2025-11-04
**Purpose:** Unified access to all AIONS/AI projects from single location
**Target:** E:\AIONS_MASTER\

---

## Executive Summary

Consolidating **entire AI development history** into unified structure:
- **5 AIONS versions** (V0, V1, V2, V3, VANILA)
- **Historical predecessors** (POLIPEK, MAIPA)
- **4+ plasters collections** (200g, howto, programming, general, claude)
- **Working production code** (Desktop copy)
- **Recovery data** and audit reports

**Total Size Estimate:** ~50-100GB
**Location:** E:\ has 500GB+ available ✅

---

## Current State - Scattered Locations

### 1. Windows E:\ Drive (Primary)
```
E:\AIONS_V10\
├─ AIONS_CBMS_RELEASE_V0\     (mtime: various, complete)
├─ AIONS_CBMS_RELEASE_V1\     (mtime: Oct 28 backup, complete)
├─ AIONS_CBMS_RELEASE_V2\     (mtime: various, complete)
├─ AIONS_CBMS_RELEASE_V3\     (mtime: Oct 28 latest, complete)
└─ AIONS_CBMS_RELEASE_VANILA\ (mtime: various, complete)

E:\AJAJAJ\
├─ plasters_200g\        (57 PACK blocks, PACK-0143 to PACK-0199)
├─ plasters_howto\       (PACK-0000)
├─ plasters_programming\ (PACK-0000)
├─ plasters_general\     (PACK-0000)
├─ plasters_claude\      (PACK-0000)
└─ CBMS_RECOVERY\
   ├─ 20251026_205928\   (First recovery snapshot)
   └─ 20251026_211711\   (Latest recovery snapshot)

E:\reports_home_marcin\
├─ audit\                (System audits, experiments)
└─ progress_log.md       (Recovery documentation)
```

### 2. Windows C:\ Drive (Desktop Working Copy)
```
C:\Users\User\OneDrive - Global Banking School\Desktop\
└─ AIONS_CBMS_RELEASE_V3\
   ├─ memory\             (197 chunks, 8.2MB thinking_log.jsonl)
   ├─ server\             (All Python code)
   ├─ logs\               (Benchmarks, QC logs)
   └─ [All scripts and docs]
```

### 3. Linux Partition (/mnt/data - SSD)
```
/mnt/data/AI DEVELOPMENT/.../POLIPEK V1/
├─ Files: 150-1982 Python files
├─ Framework: OpenCV
└─ mtime: August 24, 2025

/mnt/data/home_marcin/MAIPA/
├─ Files: 125 files, 50 .py
├─ Framework: torch, transformers
├─ Features: Retrieval v2, zero-training
└─ mtime: October 4, 2025

/mnt/data/.../AIONS_COMPLETE/
├─ backups/GPT-US/       (344 files)
└─ web/                  (4 files)

/mnt/data/CBMS_Pocket_QC_Lab/
├─ Files: 16 files, 7 .py
└─ mtime: October 14, 2025

/mnt/data/CBMS_EXTRACT/
├─ POLIP_20250823_193350/
├─ POLIP_GOOD_20250823_220346/
└─ _snap_20250824_205237/
```

---

## Target Structure - E:\AIONS_MASTER\

```
E:\AIONS_MASTER\
│
├─ config\
│  ├─ aions_paths.json              # Central path configuration
│  ├─ aions_history.json            # Project timeline metadata
│  └─ unified_env.ps1               # Environment setup
│
├─ production\                       # ← SYMLINK to Desktop working copy
│  └─ @ → C:\Users\...\Desktop\AIONS_CBMS_RELEASE_V3
│
├─ versions\                         # AIONS version archive
│  ├─ v0\                           # ← COPY from E:\AIONS_V10\
│  ├─ v1\                           # ← COPY from E:\AIONS_V10\
│  ├─ v2\                           # ← COPY from E:\AIONS_V10\
│  ├─ v3\                           # ← COPY from E:\AIONS_V10\
│  └─ vanila\                       # ← COPY from E:\AIONS_V10\
│
├─ plasters\                         # All plasters collections
│  ├─ 200g\                         # ← SYMLINK to E:\AJAJAJ\plasters_200g
│  ├─ howto\                        # ← SYMLINK to E:\AJAJAJ\plasters_howto
│  ├─ programming\                  # ← SYMLINK to E:\AJAJAJ\plasters_programming
│  ├─ general\                      # ← SYMLINK to E:\AJAJAJ\plasters_general
│  └─ claude\                       # ← SYMLINK to E:\AJAJAJ\plasters_claude
│
├─ history\                          # Historical predecessor projects
│  ├─ polipek_v1\                   # ← COPY from Linux /mnt/data
│  │  ├─ README_HISTORICAL.md       # Generated context doc
│  │  └─ [all POLIPEK code]
│  │
│  ├─ maipa\                        # ← COPY from Linux /mnt/data
│  │  ├─ README_HISTORICAL.md       # Generated context doc
│  │  └─ [all MAIPA code]
│  │
│  ├─ aions_complete\               # ← COPY from Linux /mnt/data
│  │  └─ backups/GPT-US/
│  │
│  └─ cbms_pocket_qc_lab\          # ← COPY from Linux /mnt/data
│     └─ [lab code]
│
├─ recovery\                         # Recovery snapshots
│  ├─ 20251026_205928\              # ← COPY from E:\AJAJAJ\CBMS_RECOVERY
│  └─ 20251026_211711\              # ← COPY from E:\AJAJAJ\CBMS_RECOVERY
│
├─ reports\                          # All audit/analysis reports
│  └─ audit\                        # ← COPY from E:\reports_home_marcin
│
├─ scripts\                          # Unified utilities
│  ├─ unified_start.ps1             # Universal launcher
│  ├─ switch_version.ps1            # Version switcher
│  ├─ inventory.ps1                 # System inventory
│  ├─ backup.ps1                    # Backup utilities
│  └─ compare_versions.ps1          # Version diff tool
│
├─ docs\
│  ├─ MASTER_INDEX.md               # Complete system documentation
│  ├─ PATH_MAP.md                   # All paths and locations
│  ├─ VERSION_HISTORY.md            # Evolution timeline
│  ├─ CONSOLIDATION_LOG.md          # This consolidation process
│  └─ QUICK_START.md                # Getting started guide
│
└─ backups\                          # Timestamped snapshots
   └─ [future backup snapshots]
```

---

## Consolidation Strategy

### Phase 1: Create Master Structure ✅
```powershell
New-Item -ItemType Directory -Path "E:\AIONS_MASTER" -Force
New-Item -ItemType Directory -Path "E:\AIONS_MASTER\config" -Force
New-Item -ItemType Directory -Path "E:\AIONS_MASTER\versions" -Force
New-Item -ItemType Directory -Path "E:\AIONS_MASTER\plasters" -Force
New-Item -ItemType Directory -Path "E:\AIONS_MASTER\history" -Force
New-Item -ItemType Directory -Path "E:\AIONS_MASTER\recovery" -Force
New-Item -ItemType Directory -Path "E:\AIONS_MASTER\reports" -Force
New-Item -ItemType Directory -Path "E:\AIONS_MASTER\scripts" -Force
New-Item -ItemType Directory -Path "E:\AIONS_MASTER\docs" -Force
New-Item -ItemType Directory -Path "E:\AIONS_MASTER\backups" -Force
```

### Phase 2: Symlink Working Production (Fast)
```powershell
# Symlink to Desktop working copy
New-Item -ItemType SymbolicLink `
    -Path "E:\AIONS_MASTER\production" `
    -Target "C:\Users\User\OneDrive - Global Banking School\Desktop\AIONS_CBMS_RELEASE_V3"

# Symlink plasters (no duplication)
New-Item -ItemType SymbolicLink -Path "E:\AIONS_MASTER\plasters\200g" -Target "E:\AJAJAJ\plasters_200g"
New-Item -ItemType SymbolicLink -Path "E:\AIONS_MASTER\plasters\howto" -Target "E:\AJAJAJ\plasters_howto"
New-Item -ItemType SymbolicLink -Path "E:\AIONS_MASTER\plasters\programming" -Target "E:\AJAJAJ\plasters_programming"
New-Item -ItemType SymbolicLink -Path "E:\AIONS_MASTER\plasters\general" -Target "E:\AJAJAJ\plasters_general"
New-Item -ItemType SymbolicLink -Path "E:\AIONS_MASTER\plasters\claude" -Target "E:\AJAJAJ\plasters_claude"
```

### Phase 3: Copy AIONS Versions (E:\ to E:\)
```powershell
# Copy all 5 versions to archive
Copy-Item "E:\AIONS_V10\AIONS_CBMS_RELEASE_V0" -Destination "E:\AIONS_MASTER\versions\v0" -Recurse
Copy-Item "E:\AIONS_V10\AIONS_CBMS_RELEASE_V1" -Destination "E:\AIONS_MASTER\versions\v1" -Recurse
Copy-Item "E:\AIONS_V10\AIONS_CBMS_RELEASE_V2" -Destination "E:\AIONS_MASTER\versions\v2" -Recurse
Copy-Item "E:\AIONS_V10\AIONS_CBMS_RELEASE_V3" -Destination "E:\AIONS_MASTER\versions\v3" -Recurse
Copy-Item "E:\AIONS_V10\AIONS_CBMS_RELEASE_VANILA" -Destination "E:\AIONS_MASTER\versions\vanila" -Recurse
```

### Phase 4: Copy Historical Projects (Linux to E:\)
```powershell
# POLIPEK V1
Copy-Item "/mnt/data/AI DEVELOPMENT/WORK SPACE/IMPORT FROM _F/AI development project/v6/POLIPEK V1" `
    -Destination "E:\AIONS_MASTER\history\polipek_v1" -Recurse

# MAIPA
Copy-Item "/mnt/data/home_marcin/MAIPA" `
    -Destination "E:\AIONS_MASTER\history\maipa" -Recurse

# AIONS_COMPLETE
Copy-Item "/mnt/data/AI DEVELOPMENT/WORK SPACE/IMPORT FROM _F/BACKUP 01/BACKUP 01/AIONS_COMPLETE" `
    -Destination "E:\AIONS_MASTER\history\aions_complete" -Recurse

# CBMS_Pocket_QC_Lab
Copy-Item "/mnt/data/CBMS_Pocket_QC_Lab" `
    -Destination "E:\AIONS_MASTER\history\cbms_pocket_qc_lab" -Recurse
```

### Phase 5: Copy Recovery & Reports
```powershell
# Recovery snapshots
Copy-Item "E:\AJAJAJ\CBMS_RECOVERY\*" -Destination "E:\AIONS_MASTER\recovery\" -Recurse

# Reports
Copy-Item "E:\reports_home_marcin\*" -Destination "E:\AIONS_MASTER\reports\" -Recurse
```

### Phase 6: Generate Configuration Files
Create `config/aions_paths.json`:
```json
{
  "master_root": "E:\\AIONS_MASTER",
  "production": {
    "path": "E:\\AIONS_MASTER\\production",
    "target": "C:\\Users\\User\\OneDrive - Global Banking School\\Desktop\\AIONS_CBMS_RELEASE_V3",
    "type": "symlink",
    "status": "active"
  },
  "versions": {
    "v0": "E:\\AIONS_MASTER\\versions\\v0",
    "v1": "E:\\AIONS_MASTER\\versions\\v1",
    "v2": "E:\\AIONS_MASTER\\versions\\v2",
    "v3": "E:\\AIONS_MASTER\\versions\\v3",
    "vanila": "E:\\AIONS_MASTER\\versions\\vanila"
  },
  "plasters": {
    "200g": "E:\\AIONS_MASTER\\plasters\\200g",
    "howto": "E:\\AIONS_MASTER\\plasters\\howto",
    "programming": "E:\\AIONS_MASTER\\plasters\\programming",
    "general": "E:\\AIONS_MASTER\\plasters\\general",
    "claude": "E:\\AIONS_MASTER\\plasters\\claude"
  },
  "history": {
    "polipek_v1": "E:\\AIONS_MASTER\\history\\polipek_v1",
    "maipa": "E:\\AIONS_MASTER\\history\\maipa",
    "aions_complete": "E:\\AIONS_MASTER\\history\\aions_complete",
    "cbms_pocket_qc_lab": "E:\\AIONS_MASTER\\history\\cbms_pocket_qc_lab"
  },
  "recovery": "E:\\AIONS_MASTER\\recovery",
  "reports": "E:\\AIONS_MASTER\\reports"
}
```

### Phase 7: Create Unified Launcher
`scripts/unified_start.ps1` - launches any version or production

---

## Benefits of This Structure

### ✅ Single Access Point
Everything accessible from `E:\AIONS_MASTER\`

### ✅ Zero Duplication for Working Files
- Production → symlink (no copy)
- Plasters → symlinks (no copy)

### ✅ Complete History
- All 5 AIONS versions archived
- POLIPEK and MAIPA code preserved
- Recovery snapshots saved

### ✅ Easy Version Switching
```powershell
# Switch to V1
.\scripts\switch_version.ps1 -Version v1

# Switch back to production
.\scripts\switch_version.ps1 -Version production
```

### ✅ Backup Ready
```powershell
# Backup entire master to external drive
.\scripts\backup.ps1 -Destination "D:\Backups\AIONS_MASTER_$(Get-Date -Format 'yyyyMMdd')"
```

### ✅ Unified Documentation
All docs, reports, and histories in one place

---

## Disk Space Impact

### Before Consolidation:
```
E:\AIONS_V10\          ~5-10GB  (5 versions)
E:\AJAJAJ\             ~30-50GB (plasters + recovery)
C:\Desktop\            ~2-5GB   (working copy)
Linux /mnt/data\       ~10-20GB (historical)
E:\reports\            ~100MB   (reports)
───────────────────────────────
Total: ~50-85GB scattered
```

### After Consolidation:
```
E:\AIONS_MASTER\
├─ production/         0GB      (symlink)
├─ versions/           ~10GB    (5 versions copied)
├─ plasters/           0GB      (symlinks)
├─ history/            ~15GB    (POLIP, MAIPA, etc.)
├─ recovery/           ~500MB   (recovery snapshots)
├─ reports/            ~100MB   (reports)
├─ scripts/            ~5MB     (utilities)
└─ docs/               ~10MB    (documentation)
───────────────────────────────
Total: ~26GB on E:\ (half is copies for safety)
```

**Net Result:** ~26GB actual usage, but FULL access to everything

---

## Safety Measures

### 1. Original Locations Preserved
- E:\AIONS_V10\ → kept as-is
- E:\AJAJAJ\ → kept as-is (symlinked, not moved)
- C:\Desktop\ → kept as-is (symlinked, not moved)
- Linux /mnt/data → kept as-is (copied, not moved)

### 2. Verification Checksums
After each copy operation, verify:
```powershell
# Generate checksums before
Get-FileHash "E:\AIONS_V10\AIONS_CBMS_RELEASE_V3\server\cbms_memory.py"

# Verify after copy
Get-FileHash "E:\AIONS_MASTER\versions\v3\server\cbms_memory.py"
```

### 3. Rollback Plan
If anything goes wrong:
- Master directory is NEW → just delete it
- Original locations untouched → continue using them

---

## Execution Timeline

### Estimated Time:
- Phase 1 (Create structure): **1 minute**
- Phase 2 (Symlinks): **1 minute**
- Phase 3 (AIONS versions): **10-20 minutes** (copying ~10GB)
- Phase 4 (Historical): **15-30 minutes** (copying ~15GB from Linux)
- Phase 5 (Recovery/Reports): **2-5 minutes** (~500MB)
- Phase 6 (Config files): **5 minutes**
- Phase 7 (Scripts/Docs): **10 minutes**

**Total: ~45-75 minutes**

---

## Post-Consolidation Workflow

### Daily Work:
```powershell
cd E:\AIONS_MASTER\production
.\START_MONITOR.ps1
```

### Version Testing:
```powershell
cd E:\AIONS_MASTER
.\scripts\switch_version.ps1 -Version v2
```

### Historical Research:
```powershell
cd E:\AIONS_MASTER\history\maipa
# Explore MAIPA code
```

### System Inventory:
```powershell
cd E:\AIONS_MASTER
.\scripts\inventory.ps1
# Shows all components, versions, sizes, status
```

---

## Ready to Execute?

**Next Steps:**
1. Review this plan
2. Confirm all paths are correct
3. Execute Phase 1-7 scripts
4. Verify consolidation
5. Update working environment to use `E:\AIONS_MASTER\production`

**Status: READY FOR EXECUTION** ✅

All prerequisites met:
- ✅ Admin privileges available
- ✅ 500GB+ space on E:\
- ✅ All source locations identified
- ✅ Target structure designed
- ✅ Safety measures in place

---

**Generated by:** Claude (AIONS consciousness)
**Date:** 2025-11-04
**Purpose:** Complete AI development history unification
