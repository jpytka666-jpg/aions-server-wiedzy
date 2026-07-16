# 📚 AIONS KNOWLEDGE CATALOG
## Master Index — Server Wiedzy (canonical E:)
### Generated: 2026-07-10

---

## 🗂️ STRUKTURA KATALOGU

```
E:\server wiedzy\AIONS_CATALOG\
├── INDEX.md              # Ten plik — mapa skarbów (human-readable)
├── catalog_2026.json     # Katalog maszynowy (generowany przez scripts/catalog_e_treasures.py)
├── indices\              # Indeksy CBMS referencyjne (archiwum)
├── chunks\               # Archiwum chunków (nie operacyjne)
├── plasters\             # Odnośniki do paczek plastrów
├── thinking_patterns\      # Wzorce myślenia
├── codebooks\            # Codebooki
├── facts\                # Bazy faktów
├── models\               # Odnośniki do modeli
├── tools\                # Narzędzia
└── docs\                 # Dokumentacja
```

**Operacyjny CBMS (AIONS_PATH):** `E:\server wiedzy\aions_core` — **561 chunków** w `memory\chunks\` (manifest) + 1 chunk poza manifestem (`KCBMSACCESS001`).

---

## 📊 MAPA SKARBÓW E: (2026-07)

| ID | Lokalizacja | Typ | Rozmiar (szac.) | Status | CBMS |
|----|-------------|-----|-----------------|--------|------|
| **aions_core_cbms** | `E:\server wiedzy\aions_core` | cbms_operational | ~20 MB | **connected** | ✅ |
| **chroma_prod** | `E:\server wiedzy\data\chroma` | vector_store | zmienny | **connected** | ✅ |
| **plasters_200g_master** | `E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\plasters_200g` | plasters | ~0.4 GB / 200 PACK | **connected** | ✅ meta |
| **plasters_fullstack** | `E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\plasters_fullstack` | plasters | ~większy / 448 PACK | **connected** | ✅ meta |
| **master_clean_unclassified** | `E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED` | workspace | **~61 GB** | **connected** | częściowo |
| **ajajaj_root** | `E:\AJAJAJ` | backup_archive | **~184 GB** | **connected** | ❌ |
| **cbms_index_full** | `E:\AJAJAJ\CBMS_INDEX_FULL` | cbms_index | ~10 MB / 6819 docs | **disconnected** | ❌ |
| **cbms_index_korean** | `E:\AJAJAJ\CBMS_INDEX_KOREAN` | cbms_index | ~2 MB | **disconnected** | ❌ |
| **cbms_seed** | `E:\AJAJAJ\CBMS_SEED` | model_artifacts | metadata only | **archived** | ❌ |
| **ajajaj_plasters_200g** | `E:\AJAJAJ\plasters_200g` | plasters | ~0.4 GB kopia | **archived** | ✅ meta |
| **aions_complete** | `E:\AJAJAJ\AIONS_COMPLETE` | legacy_snapshot | ~20 MB | **archived** | ❌ |
| **full_system_scan** | `E:\server wiedzy\scan_results\full_system_20260702_035156` | scan_artifact | ~0.6 GB | **connected** | ❌ |

**Uwaga:** `E:\AI_WORKSPACE\MASTER_CLEAN\CBMS\` i `chunks_unified\` — **brak na dysku** (2026-07); indeksy przeniesione do `E:\AJAJAJ\`.

---

## 📈 STATYSTYKI SUMARYCZNE (scan 2026-07-02)

| Metryka | Wartość |
|---------|---------|
| **Dysk E: (turbo scan)** | 115 130 plików kodu, **~226 GB** (226 482 MB) |
| **CBMS operacyjny (manifest)** | **561** chunków |
| **CBMS_INDEX_FULL (AJAJAJ)** | 6 819 docs |
| **plasters_200g PACK** | 200 (× ~1716 Q&A ≈ 343k) |
| **plasters_fullstack PACK** | 448 |
| **Korean index** | ~8 042 patterns |

Pełny scan: `E:\server wiedzy\scan_results\full_system_20260702_035156\master_map.json`

---

## 🔗 SZYBKIE LINKI (aktywne 2026-07)

| Co | Ścieżka |
|----|---------|
| **CBMS kanoniczny** | `E:\server wiedzy\aions_core` |
| **Chunki** | `E:\server wiedzy\aions_core\memory\chunks\` |
| **Manifest** | `E:\server wiedzy\aions_core\memory\knowledge_manifest.json` |
| **Chroma prod** | `E:\server wiedzy\data\chroma` |
| **MCP prod (Cursor)** | `aions-context` → `E:\server wiedzy\venv` |
| **Przewodnik dla człowieka** | `E:\server wiedzy\docs\CBMS_HUMAN_GUIDE.md` |
| **Dev mirror** | `D:\AIONS_DEV\repo\server-wiedzy` (sync z E:) |
| **Junction CBMS (WSL)** | `D:\AIONS_DEV\cbms` → `E:\server wiedzy\aions_core` |

### Workspace / archiwa

| Co | Ścieżka |
|----|---------|
| Plastery robocze | `E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\` |
| Backup pełny | `E:\AJAJAJ\` |
| MCP Server | `E:\server wiedzy\mcpServers\VS_CODE_MCP_CODEX\` |

---

## 🛠️ NARZĘDZIA KATALOGU

| Narzędzie | Opis |
|-----------|------|
| `scripts/catalog_e_treasures.py` | Generuje `AIONS_CATALOG\catalog_2026.json` |
| `scripts/ingest_treasures_tier2.py` | Rejestruje lokalizacje skarbów w Chroma (tier-2, bez binariów) |
| `scripts/ingest_tier1_chroma.py` | Tier-1: operator_profile + CBMS manifest sample |
| `scripts/sync_dev_mirror.ps1` | E: → D:\AIONS_DEV mirror |
| `scripts/audit_cbms_sources.ps1` | Audyt źródeł chunków |

**Regeneracja katalogu:**
```powershell
cd "E:\server wiedzy"
python scripts\catalog_e_treasures.py
python scripts\ingest_treasures_tier2.py
```

---

## ⚠️ ZNANE PROBLEMY (2026-07-10)

1. **Manifest vs dysk:** 561 w manifeście, 562 plików JSON (`KCBMSACCESS001` poza manifestem) — niski priorytet
2. **Stare ścieżki D:\ w treści chunków** — historyczne; kanoniczne `E:\server wiedzy\aions_core` (naprawiono `KCBMSACCESS001`, `cbms_seed_reference.json`)
3. **CBMS_INDEX_FULL disconnected** — 6819 docs w AJAJAJ, nie podłączone do MCP search
4. **Plastery — metadata only** — 343k Q&A w mmap; ingest tier-2 rejestruje *gdzie*, nie kopiuje binariów
5. **MASTER_CLEAN/CBMS** — folder usunięty/przeniesiony; używaj `E:\AJAJAJ\CBMS_*`

---

## 📌 HISTORIA MIGRACJI

| Data | Zdarzenie |
|------|-----------|
| 2025-11-28 | Pierwsza wersja INDEX (ContextVault, OneDrive V3) |
| 2026-07-03 | Fala 0: `AIONS_PATH` → `E:\server wiedzy\aions_core` |
| 2026-07-10 | Pełna mapa skarbów E:, `catalog_2026.json`, tier-2 Chroma ingest |

---

*Katalog: human `INDEX.md` + machine `catalog_2026.json`*
*Ostatnia aktualizacja: 2026-07-10*
