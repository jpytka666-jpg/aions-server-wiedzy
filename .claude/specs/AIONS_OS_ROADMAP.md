# AIONS Cognitive Platform — Roadmap Architektoniczny

**Podtytuł:** Warstwa kognitywna nad OS — nie konkurencja dla kernela Linux  
**Autor:** AIONS Expert Agent (architekt)  
**Data:** 2026-07-02  
**Maszyna:** Marcin — Windows 10/11, `E:\server wiedzy`  
**Status:** Faza 1 zamknięta, **Milestone A: Linux Runtime Stable ~90%**, **Milestone C: real VM install in progress** (Hyper-V agent) — WSL dev path cleanup po Docker milestone-c test

---

## Changelog

| Wersja | Data | Autor | Zmiany |
|--------|------|-------|--------|
| **v14** | 2026-07-02 | Cursor / spec-impl | **Milestone C (WSL slice):** cleanup po Docker `aions-milestone-c` — przywrócone `runtime/systemd/user/*` (WSL dev paths), health timer na `aions_run_health.sh` + `D:\AIONS_DEV`, wdrożony `aions-index.timer`, sync `__main__.py` venv guard (Linux prefix); real VM install → Hyper-V agent |
| **v13** | 2026-07-02 | Cursor / spec-impl | **Milestone A:** `aions-ctl` api-{install,start,stop,status,logs}, `up/down/status/logs` agreguje 4 unity; health service bez hardcoded D: paths (`aions_run_health.sh` + `EnvironmentFile`); healthcheck GREEN z index+api probe; auto `index-refresh` przy pierwszym `up`; smoke WSL user `aions` OK |
| **v13** | 2026-07-02 | Cursor / spec-impl | Etap 5/6 slice #2: `provider_registry.py`, linux-desktop screenshot (mss) + input (xdotool), `aions_indexer ensure`, timer 15m, usunięte fd/plocate fallbacki z `server.py` |
| **v12** | 2026-07-02 | Cursor / spec-impl | Etap 5/6/9/10 groundwork: własny `aions-linux-index` (JSON index + refresh script + env/runtime wiring), provider architektura `desktop_provider.py` z linux-native system slice (`desktop_shell`/launch/window inventory/clipboard), stagingowe skrypty host install / first boot w `runtime/host/` |
| **v11** | 2026-07-02 | Cursor / spec-impl | Etap 3 slice #2: MCP dostał profile/platform abstraction (`AIONS_DEPLOYMENT_PROFILE`, Linux-safe Python path, search provider selection), opcjonalny storage/session proxy przez `aions-api.service` (`AIONS_VECTOR_BACKEND=api`), bez ruszania Windows-only providerów |
| **v10** | 2026-07-02 | Cursor / spec-impl | Unified launcher Windows -> WSL dla dev runtime: `start_aions_dev.bat` deleguje jako user `aions` do `start_aions_dev.sh` / `aions-ctl` (`up/down/restart/status/logs`), smoke z Windows OK; prod `aions-context` bez zmian |
| **v9** | 2026-07-02 | Cursor / spec-impl | Bezpieczny slice Etapu 3: localhost-only `aions-api.service` dla WSL/dev (`runtime/scripts/start_aions_api.sh`, manualny unit user-space, runbook testowy), bez zmian w `aions-ctl`, `mcp.json` i prod MCP |
| **v8** | 2026-07-02 | Cursor / spec-impl | Etap 2.5 domknięty operacyjnie: `aions-ctl up/down/restart/status/logs`, agregat runtime dev (`aions-health.timer`, `aions-health.service`, `aions-mcp.service`), walidacja w WSL user `aions` na mirrorze `D:` |
| **v7** | 2026-07-02 | Cursor / spec-impl | Etap 3 readiness blueprint dla Oracle/Linux always-on: portability matrix, minimal service topology, sample Oracle env w `runtime/` bez zmian w aktywnym runtime |
| **v6** | 2026-07-02 | Cursor / spec-impl | Fix `mcp-start` exit 127: symlink `/mnt/e/aions-repo`, wrapper `~/aions/bin/start_aions_mcp.sh`, `EnvironmentFile`; `aions-ctl mcp-start` → SUCCESS, log `~/aions/logs/mcp.log` |
| **v5** | 2026-07-02 | Cursor / spec-impl | Domknięcie Etap 2 runtime: user `aions` (uid 1000), `loginctl enable-linger`, health GREEN (chromadb 0.5.3), `aions-ctl enable`, sync E→D; MCP unit crash (ExecStart + spacje w ścieżce → Etap 3) |
| **v4** | 2026-07-02 | Cursor / spec-impl | Etap 2 slice #2: `aions-mcp.service` + `aions-ctl mcp-{install,start,stop,status,logs}`; unit bez autostartu, start po health gate |
| **v3** | 2026-07-02 | Cursor / spec-impl | Start Etapu 2: `aions-health.service` + `aions-health.timer`, skrypt `aions-ctl`, health log do `~/aions/logs/health.log`; świadomie bez portu MCP na Linux |
| **v2** | 2026-07-02 | Marcin + koledzy (Brain + practical) | Reframe na Cognitive Platform; Deployment Topology; Architektura v2 (Core/Runtime/Tool Bus/Brain); Etap 6.5 Brain; usunięcie genie; GPU opcjonalne; timeline realistyczny; Gotowość Fazy 1 |
| v1 | 2026-07-02 | AIONS Expert Agent | Pierwsza wersja roadmapy AIONS OS |

---

## Wizja docelowa

AIONS to **warstwa kognitywna** nad istniejącym systemem operacyjnym — planuje, pamięta, wybiera narzędzia i orkiestruje usługi. **Nie budujemy OS od zera** i nie konkurujemy z kernelem Linux.

```
Użytkownik (Marcin)
  └─ Planner (intencja → plan kroków)
       └─ Agent Manager (wykonanie, retry, reflection)
            └─ Tool Bus (jednolity interfejs narzędzi)
                 ├─ MCP adapter        ← Cursor, Claude Desktop
                 ├─ CLI adapter
                 ├─ REST adapter
                 └─ Desktop API adapter
                      ├─ CBMS (wiedza deterministyczna)
                      ├─ Memory / ChromaDB (pamięć semantyczna)
                      ├─ Desktop Control (WindowsDesktop | LinuxSystem | LinuxDesktop | RemoteDesktop)
                      ├─ Browser (Playwright)
                      ├─ Docker
                      ├─ GPU/ML (opcjonalnie)
                      ├─ Filesystem Index (Everything / AIONS Linux Index)
                      └─ Project Scanner
```

**Zasady architektoniczne:**
- Nie budujemy kernela — używamy Linux (WSL2 / Oracle Cloud) + Windows jako host GUI
- AIONS = **cognitive layer** (pamięć, planowanie, reasoning, registry) nad **runtime** (systemd, procesy)
- MCP to **jeden adapter** na Tool Bus — nie centrum architektury
- Preferujemy OSS jako prymitywy, ale provider/logika ma być własna AIONS tam, gdzie wcześniej był Windows-only gap
- Minimalizujemy custom code — każdy etap kończy się **działającym systemem**
- Near-term: **hybryda Windows (primary) + WSL2 (dev/staging) + Oracle Cloud (prod 24/7)**
- Event Bus — przyszłość (etapy 5–6+); **nie over-engineerować teraz**

---

## Deployment Topology

*Sekcja obowiązkowa przed Etapem 1 — gdzie co żyje i jak się synchronizuje.*

```
┌─────────────────────────────────────────────────────────────────────────┐
│  WINDOWS LAPTOP (primary — DZIŚ)                                        │
│  ├─ Cursor IDE + aions-context MCP (stdio)                              │
│  ├─ desktop_* (pywin32), Everything (es.exe)                            │
│  ├─ ChromaDB: E:\server wiedzy\data\chroma (122 sesje, ~7 MB)           │
│  ├─ CBMS: D:\AIONS-INTEGRATION\aions_core (545 chunks)                  │
│  ├─ Full system scan, AIOrchestrator                                    │
│  └─ Rola: codzienna praca Marcina, desktop automation, dev MCP          │
└─────────────────────────────────────────────────────────────────────────┘
         │ rsync/replicate (gdy stabilne)              │ git push
         ▼                                               ▼
┌──────────────────────────────┐    ┌──────────────────────────────────────┐
│  WSL2 Ubuntu (dev/staging)   │    │  ORACLE CLOUD ARM (prod 24/7)        │
│  ├─ Native systemd (wsl.conf)│    │  4 OCPU / 24 GB RAM                  │
│  ├─ Test MCP, systemd units  │    │  ├─ MCP always-on (SSE/HTTP)         │
│  ├─ ~/aions/ clone + venv    │    │  ├─ ChromaDB + CBMS (canonical prod) │
│  ├─ NIE 24/7 prod            │    │  ├─ Backup, monitoring               │
│  └─ Rola: walidacja Linux    │    │  └─ Rola: canonical data + MCP 24/7  │
└──────────────────────────────┘    └──────────────────────────────────────┘
```

### Strategia synchronizacji danych

| Dane | Źródło DZIŚ | Docelowo (prod) | Strategia |
|------|-------------|-----------------|-----------|
| ChromaDB | `E:\server wiedzy\data\chroma` | Oracle Cloud ext4 | Replikacja gdy stabilne; **unikać** pełnej migracji ext4↔Windows jeśli cloud jest celem |
| CBMS | `D:\AIONS-INTEGRATION\aions_core` | Oracle Cloud | rsync / git; mirror na E:\ jako backup |
| Kod AIONS | `E:\server wiedzy` (git) | Wszystkie nody | `git push` — single source of truth |
| Config MCP | `.kiro/`, `.cursor/` | Per-node | Ręczna synchronizacja lub template |

**Kluczowa decyzja:** Etap 4 (migracja Chroma na ext4 WSL) ma sens tylko jako **staging** przed Oracle — nie inwestować w podwójną migrację Windows→WSL→Cloud bez potrzeby.

---

## Architektura docelowa v2

Trzy warstwy + przyszły Event Bus:

```
┌─────────────────────────────────────────────────────────────────┐
│  AIONS CORE (logika kognitywna)                                 │
│  ├─ Memory (ChromaDB, sesje, auto-log)                          │
│  ├─ Planner (intencja → plan)                                   │
│  ├─ Reasoning (think_*, reflection)                             │
│  ├─ Registry (narzędzia, usługi, capability map)              │
│  └─ Config (env, paths, deployment profile)                     │
├─────────────────────────────────────────────────────────────────┤
│  AIONS RUNTIME (infrastruktura procesów)                        │
│  ├─ systemd user services (WSL2 / Oracle)                       │
│  ├─ aions-ctl (start/stop/status/logs)                          │
│  ├─ Health timers, backup cron                                  │
│  └─ Process supervision, auto-restart                           │
├─────────────────────────────────────────────────────────────────┤
│  AIONS SERVICES (implementacje capability)                      │
│  ├─ CBMS Service                                                │
│  ├─ Memory Service                                              │
│  ├─ Desktop Provider (WindowsDesktop | LinuxDesktop | Remote)   │
│  ├─ Browser Service                                             │
│  ├─ Docker Service                                              │
│  ├─ Filesystem Index Service                                    │
│  └─ GPU/ML Service (opcjonalny)                                 │
├─────────────────────────────────────────────────────────────────┤
│  TOOL BUS (abstrakcja dostępu)                                  │
│  MCP | CLI | REST | Desktop API  →  Services                    │
├─────────────────────────────────────────────────────────────────┤
│  EVENT BUS (przyszłość — etapy 5–6+)                            │
│  Pub/sub między usługami; NIE implementować w Etapach 1–4       │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  OS SUBSTRATE                                                   │
│  Linux kernel + systemd  |  Windows (GUI, desktop_*, Everything)│
└─────────────────────────────────────────────────────────────────┘
```

### Embryoniczny Brain (już istnieje)

| Komponent docelowy | Stan dziś | Narzędzia MCP |
|--------------------|-----------|---------------|
| Reasoning | ✅ Działa | `think_start`, `think_step`, `think_branch`, `think_finish` |
| Memory fusion | ✅ Działa | `memory_recall`, `memory_store`, `session_list` |
| Auto-log / audit | ✅ Działa | hook `sessionStart`, `conv_dump`, auto-log jsonl |
| CBMS knowledge | ✅ Działa | `cbms_search`, `cbms_get_chunk` |
| Planner | 🔶 Brak | — (Etap 6.5) |
| Goal Manager | 🔶 Brak | — (Etap 6.5) |
| Agent Manager | 🔶 Brak | — (Etap 6.5) |
| Tool selection | 🔶 Częściowy | agent wybiera MCP tools ad-hoc |
| Self-check / Reflection | 🔶 Częściowy | `think_finish`, brak formalnego retry |
| Long-term goals | 🔶 Brak | — (Etap 6.5) |

---

## Faza 0 — Inwentaryzacja środowiska (dziś, 2026-07-02)

### Wyniki audytu

| Komponent | Status | Szczegóły |
|-----------|--------|-----------|
| **WSL2** | ✅ Zainstalowany | Ubuntu (default, **Stopped**), docker-desktop (**Running**) |
| **Hyper-V VMs** | ❌ Brak | `Get-VM` — puste |
| **VMware** | ❌ Brak | `C:\Program Files\VMware` — nie istnieje |
| **VirtualBox** | ❌ Brak | `C:\Program Files\Oracle\VirtualBox` — nie istnieje |
| **QEMU** | ❌ Brak | `where qemu` — nie znaleziono |
| **Docker** | ✅ Running | v29.4.3, Docker Desktop 4.73.1, 4 kontenery (kind/k8s) |
| **Python** | ✅ 3.11.9 | Unified: Windows venv + WSL dev (3.12 blocked by chroma-hnswlib wheels) |
| **Git** | ✅ 2.51.0 | Repo: `aions-server-wiedzy` (main) |
| **GPU** | ⚠️ Opcjonalny | Quadro M2000M 4 GB, Maxwell, CUDA 13 host ≠ GPU capability |
| **Everything** | ✅ OK | es.exe v1.1.0.27, `C:\Program Files\Everything\` |
| **MCP Cursor** | ✅ 1 serwer | `aions-context` via `start_aions_mcp.bat` |
| **MCP Claude Desktop** | ✅ 9 serwerów | AIONS-Context + 8 innych |
| **AIONS Server** | ✅ v6 DEBILOODPORNE | `server.py` — **55 narzędzi** |
| **Desktop Control** | ✅ OK | pyautogui/pywin32 — 11 narzędzi `desktop_*` |
| **CBMS** | ✅ 545 chunks | `D:\AIONS-INTEGRATION\aions_core` |
| **ChromaDB** | ✅ 122 sesje | `E:\server wiedzy\data\chroma` (~7 MB) |
| **Full System Scan** | 🔄 W toku | Kampania `full_system_20260702_035156`, faza 2/4 (dysk E:\) |
| **AIOrchestrator** | ✅ Aktywny | `E:\server wiedzy\AIOrchestrator\` |
| **WSL Export Path** | ✅ Istnieje | `E:\WSL` |
| **Oracle Cloud ARM** | 📋 Planowany | 4 OCPU / 24 GB — prod 24/7 (nie wdrożony) |

### Architektura obecna (baseline)

```
Windows 10/11 (host — PRIMARY)
├── Cursor IDE ──stdio──► aions-context MCP (55 tools) ──► Tool Bus
│                              ├── ChromaDB (E:\server wiedzy\data\chroma)
│                              ├── CBMS (D:\AIONS-INTEGRATION\aions_core)
│                              ├── Everything (es.exe)
│                              ├── Desktop Control (WindowsDesktop)
│                              ├── Playwright Browser
│                              └── Docker/WSL/Git/Network
├── Claude Desktop ──stdio──► AIONS-Context + 8 innych MCP
├── Docker Desktop ──WSL2──► docker-desktop distro
├── WSL2 Ubuntu (Stopped) ──► dev/staging (nie prod)
└── AIOrchestrator (PowerShell)
```

### Rekomendacja strategii (near-term)

**Windows primary + WSL2 staging + Oracle prod** — najlepsza opcja na najbliższe miesiące:

1. AIONS w pełni działa na Windows (55 narzędzi, desktop control, Everything)
2. WSL2 Ubuntu — **dev/staging Linux**, test systemd i MCP; **nie** 24/7 prod
3. Oracle Cloud ARM — docelowy **canonical** Chroma/CBMS + MCP always-on
4. Desktop Control wymaga Windows — hybryda zachowuje oba światy
5. GPU — eksperyment opcjonalny, nie filar roadmapy

**Ścieżka migracji:** Windows+AIONS (dziś) → WSL2 staging (etapy 1–3) → Oracle prod (etap 9+) → opcjonalnie bare metal gdy sprzęt.

---

## Etap 0 — Baseline (obecny stan)

### Cel
Udokumentować i ustabilizować działający system AIONS na Windows jako punkt odniesienia.

### Zależności
- Brak — to jest punkt startowy.

### Ryzyka
| Ryzyko | Prawdop. | Mitygacja |
|--------|----------|-----------|
| Scan w toku blokuje zasoby | Średnie | Nie przerywać; scan kończy się sam |
| CBMS na D:\ — dysk zewnętrzny | Niskie | Backup + mirror na E:\ |
| 55 narzędzi MCP — duży surface | Niskie | Już przetestowane, v6 stabilne |

### Plan implementacji
1. ✅ Inwentaryzacja (ten dokument)
2. ✅ `system_health` = all ok
3. Dokończyć full_system_scan (w toku, nie przerywać)
4. Snapshot konfiguracji (`backups/` już istnieje)

### Testy
- `system_health()` → wszystkie komponenty "ok"
- `fast_search("aions")` → wyniki < 100 ms
- `memory_recall("test")` → odpowiedź < 500 ms
- `cbms_get_chunk("KBOOTSTRAP")` → chunk zwrócony

### Kryteria ukończenia
- [x] Dokument baseline (ten plik v2)
- [x] system_health = ok
- [ ] full_system_scan zakończony (w toku — **nie blokuje Etapu 1**)
- [x] Backup konfiguracji MCP

---

## Etap 1 — Decyzja o substracie Linux (Etap 1-lite)

### Cel
Skonfigurować WSL2 Ubuntu jako **dev/staging** Linux — bez pełnej migracji Chroma/CBMS.

### Architektura

```
Windows 11 (host — GUI, Cursor, Desktop Control, Chroma/CBMS primary)
  └─ WSL2
       ├─ Ubuntu 22.04/24.04 (AIONS staging)
       │    ├─ systemd (natywny — /etc/wsl.conf)
       │    ├─ Python 3.11+ venv
       │    ├─ ~/aions/ (clone repo, struktura)
       │    └─ read-only access: /mnt/e/, /mnt/d/ (bez migracji danych)
       └─ docker-desktop (istniejący, nie ruszać)
```

**Decyzja: WSL2 Ubuntu** — dev/staging, nie prod 24/7.

### systemd w WSL2 — bez genie

Od WSL 0.67+ natywny systemd:

```ini
# /etc/wsl.conf
[boot]
systemd=true
```

Po edycji: `wsl --shutdown` z Windows, potem `wsl` — systemd startuje automatycznie.

**Usunięte:** `genie`, `systemd-wsl` — niepotrzebne workaroundy.

### Etap 1-lite (minimalny scope — rekomendowany start)

| Krok | Opis | Pełna migracja? |
|------|------|-----------------|
| 1 | `wsl --set-default Ubuntu && wsl` | — |
| 2 | `/etc/wsl.conf` → `systemd=true`, `wsl --shutdown` | — |
| 3 | `sudo apt update && apt install python3.11 python3.11-venv git` | — |
| 4 | `git clone` lub symlink repo do `~/aions/` | — |
| 5 | `python3.11 -m venv ~/aions/venv && pip install -r requirements.txt` | — |
| 6 | Health check: `wsl -d Ubuntu -- ~/aions/venv/bin/python -c "import chromadb"` | — |
| 7 | **NIE** migrować Chroma na ext4 | ❌ Etap 4 |
| 8 | **NIE** systemd services (aions-mcp) | ❌ Etap 2 |

### Zależności
- Etap 0 baseline (system_health ok)
- WSL2 włączony, Ubuntu zainstalowany

### Ryzyka
| Ryzyko | Prawdop. | Mitygacja |
|--------|----------|-----------|
| Wolny I/O na /mnt/ | Średnie | Etap 1-lite tylko read; migracja dopiero gdy Oracle/WSL staging gotowy |
| Ubuntu Stopped | Pewne | `wsl --set-default Ubuntu && wsl` |
| systemd nie startuje | Niskie | WSL 0.67+; `wsl --version` sprawdzić |

### Testy
- `wsl -d Ubuntu -- python3 --version` → 3.11+
- `wsl -d Ubuntu -- systemctl is-system-running` → `running` lub `degraded`
- Dostęp do `/mnt/e/server wiedzy/` → pliki widoczne
- `import chromadb` w venv → OK (bez migracji danych)

### Kryteria ukończenia (1-lite)
- [x] Ubuntu Running (`wsl -u aions`, systemd `running`)
- [x] systemd natywny (`/etc/wsl.conf`)
- [x] Python 3.11+ venv (`/mnt/d/AIONS_DEV/venv`)
- [x] Repo dostępne (`/mnt/e/server wiedzy` + mirror `D:\AIONS_DEV\repo\server-wiedzy`)
- [x] Health import chromadb OK
- [x] **Bez** migracji Chroma/CBMS

---

## Etap 2 — AIONS Runtime jako systemd user services

### Cel
Uruchomić AIONS jako zestaw zarządzanych usług Linux (auto-start, restart, logi) — na WSL2 staging lub Oracle prod.

### Architektura

```
AIONS RUNTIME (systemd user)
├── aions-mcp.service          # MCP server
├── aions-chroma.service       # ChromaDB health monitor
├── aions-cbms.service         # CBMS loader/health
├── aions-scanner.service      # Project scanner (oneshot/timer)
├── aions-index.service        # Filesystem index updater (timer)
└── aions-health.service       # Health check (timer)
```

### Zależności
- Etap 1 (WSL2 Ubuntu z natywnym systemd)

### Ryzyka
| Ryzyko | Prawdop. | Mitygacja |
|--------|----------|-----------|
| MCP stdio vs socket | Średnie | FastMCP SSE/HTTP na Oracle; stdio wrapper na WSL |
| ChromaDB lock przy współdzieleniu | Średnie | Jeden writer; Windows read-only lub osobna kopia staging |

### Plan implementacji
1. Utworzyć `~/aions/runtime/systemd/` z unit files
2. `aions-mcp.service`, `aions-health.timer`, `aions-scanner.timer`
3. Skrypt `aions-ctl` (start/stop/status/restart/logs)
4. `loginctl enable-linger $USER`

### Stan po domknięciu runtime (2026-07-02)
- **User WSL:** `aions` (uid 1000), `Linger=yes`, systemd user `running`
- **Health GREEN:** Python 3.11, venv `/mnt/d/AIONS_DEV/venv`, `chromadb=0.5.3`, log `~/aions/logs/health.log`
- **Włączone:** `aions-health.timer` (enabled, co ~15 min), `aions-ctl up/down/restart/status` OK
- **`aions-ctl`:** działa jako centralny manager runtime dev; komendy legacy (`install`, `enable`, `run-health`, `mcp-*`) zachowane
- **Sync dev mirror:** `sync_dev_mirror.ps1` E→`D:\AIONS_DEV\repo\server-wiedzy` (1624 pliki, zsynchronizowane)
- **`aions-mcp.service`:** `mcp-start` OK — wrapper bez spacji (`/mnt/e/aions-repo` symlink), `EnvironmentFile`, log `~/aions/logs/mcp.log`; bez autostartu (enable opcjonalnie)
- **Minimalny runtime Etapu 2.5:** `aions-health.timer`, `aions-health.service`, `aions-mcp.service`
- **Walidacja daily-use:** `wsl -u aions -- bash -lc "cd /mnt/d/AIONS_DEV/repo/server-wiedzy && ./scripts/aions-ctl up|status|logs mcp|restart|down"` przeszła
- **Brakuje do Etapu 3:** unified Windows→WSL launch jako domyślna ścieżka MCP, dodatkowe unity (`scanner/chroma/cbms/index`) i pełniejszy always-on runtime

### Postęp Etap 2.5: **~95%** (Milestone A slice)

| Kryterium | Status |
|-----------|--------|
| Health runtime (timer + oneshot) | ✅ |
| `aions-ctl` CLI | ✅ |
| `aions-ctl` jako runtime manager | ✅ |
| `aions-api.service` w `aions-ctl` | ✅ |
| Logi `~/aions/logs/` | ✅ |
| User `aions` + linger | ✅ |
| `aions-mcp.service` unit | ✅ |
| MCP start w systemd (`mcp-start`) | ✅ |
| Health GREEN (chromadb + index + api) | ✅ |
| Brak hardcoded Windows paths w Linux units | ✅ |
| 5+ units (scanner, chroma, cbms, index timers) | ❌ Etap 2+ |

---

## Milestone A — Linux Runtime Stable

### Cel
Zero krytycznych zależności od Windows w Linux runtime path; wszystkie usługi przez systemd (`aions-api`, `aions-mcp`, `aions-health`, `aions-ctl`); pełny health check GREEN; własne providery (`aions-linux-index`, `desktop_provider` linux slice); Windows = tylko provider, nie centrum.

### Postęp: **~90%**

| Kryterium | Status | Dowód |
|-----------|--------|-------|
| `aions-ctl up/down/restart/status/logs` | ✅ | WSL user `aions`, mirror `D:\AIONS_DEV` |
| `aions-health.timer` + oneshot | ✅ | enabled=active, log `~/aions/logs/health.log` |
| `aions-api.service` localhost | ✅ | `http://127.0.0.1:8765/health` → 200 OK |
| `aions-mcp.service` stdio | ✅ | active=running, log `~/aions/logs/mcp.log` |
| Health GREEN | ✅ | chromadb 0.5.3, index 2463 entries, api ok |
| `aions-linux-index` provider | ✅ | `index_exists=true`, auto-refresh przy `up` |
| `desktop_provider` linux slice | ✅ | `DESKTOP_ENABLED=false`, LinuxSystemProvider |
| Windows MCP prod bez zmian | ✅ | `E:\`, `mcp.json` aions-context nietknięte |
| Brak hardcoded D:/E: w systemd units | ✅ | `EnvironmentFile` + `aions_run_health.sh` |
| Scanner/index/sync timers | 🟡 | `aions-index.timer` wdrożony WSL; scanner/sync → Etap 2+ |
| Oracle always-on deploy | ❌ | Etap 9 |

### Smoke (2026-07-02, WSL `aions`)
```bash
cd /mnt/d/AIONS_DEV/repo/server-wiedzy
./scripts/aions-ctl up        # install + index-refresh + api + mcp
./scripts/aions-ctl status    # health-timer/api/mcp active
./scripts/aions-ctl run-health # GREEN
./scripts/aions-ctl logs      # health + api + mcp
```

### Blocker / reszta do 100%
- Scanner/index/sync jako osobne `Type=oneshot` timery (nie krytyczne dla daily dev)
- `aions-api` enable-at-boot opcjonalny (dziś manual via `aions-ctl up`)
- Pełny desktop linux slice (X11/Wayland) — poza Milestone A

### Kryteria ukończenia
- [ ] 5+ systemd user units działających
- [x] `aions-ctl` CLI funkcjonalne
- [x] `aions-ctl` agreguje runtime dev daily-use
- [x] Auto-restart po crash (mcp: `Restart=on-failure`)
- [x] Logi w `~/aions/logs/`

---

## Milestone C — Real VM Host Install

### Cel
Walidacja `install_aions_host.sh` + `first_boot_setup.sh` na prawdziwej maszynie wirtualnej (Hyper-V), nie tylko w kontenerze Docker `aions-milestone-c`.

### Postęp: **in progress** (Hyper-V agent)

| Kryterium | Status | Dowód |
|-----------|--------|-------|
| Docker milestone-c smoke (systemd in container) | ✅ done | test layoutu `/tmp/aions-host-test` |
| Docker cleanup (odzysk C:) | ✅ | `docker stop` + `volume rm aions-milestone-c-logs` |
| WSL dev path restore po Docker test | ✅ | `aions-health` → `D:\AIONS_DEV`, env bez `/tmp/aions-host-test` |
| `aions-index.timer` WSL | ✅ | enabled user `aions` |
| Real VM `install_aions_host.sh` | 🟡 | Hyper-V agent |
| `validate_install.sh` na VM | ❌ | po VM install |
| `aions-ctl up` GREEN na VM | ❌ | po VM install |

### Blocker / reszta
- Pełny host install na Hyper-V VM (agent dedykowany — nie kolizja z WSL slice)
- Oracle ARM / cloud image — po VM smoke

---

## Etap 3 — Port MCP server na Linux / unified launch

### Cel
MCP jako **adapter na Tool Bus** — działa natywnie w WSL2; Cursor (Windows) łączy się przez wrapper. Desktop tools zostają na Windows.

### Architektura

```
Cursor (Windows) ──stdio──► start_aions_mcp.bat
                                  └─► wsl -d Ubuntu -- aions-mcp-serve  [opcja]
                                        └─► FastMCP (Linux Python)
                                              ├─ ChromaDB (read /mnt/e/ lub lokalna)
                                              ├─ CBMS (read /mnt/d/)
                                              ├─ locate/plocate (Etap 5)
                                              ├─ Docker (socket)
                                              └─ Browser (Playwright headless)

Windows MCP (bez zmian) ──► desktop_*, Everything (primary na Windows)
Tool Bus ──► MCP | CLI | REST | Desktop API
```

**Kluczowe:** MCP nie jest centrum — to jeden z adapterów. Windows MCP nadal primary dla `desktop_*` i Everything.

### Zależności
- Etap 2 (systemd services) — opcjonalnie dla auto-start
- Etap 1-lite minimum

### Ryzyka
| Ryzyko | Prawdop. | Mitygacja |
|--------|----------|-----------|
| desktop_* wymaga Windows | Pewne | WindowsDesktop provider; Linux graceful skip |
| Everything nie działa w Linux | Pewne | Etap 5: plocate; Windows primary |
| stdio przez WSL boundary | Średnie | Sprawdzone — `wsl cmd` działa z Cursor |

### Plan implementacji
1. Zależności w WSL2 venv
2. Adaptacja `server.py`: env vars `CHROMA_PATH`, `AIONS_PATH`; `DESKTOP_ENABLED=false` na Linux
3. `aions-mcp-serve` wrapper; opcjonalna delegacja w `start_aions_mcp.bat`
4. **Nie wymuszać** pełnego przełączenia Cursor na WSL — hybryda OK
5. Blueprint wykonawczy: `runtime/docs/ETAP3_LINUX_ALWAYS_ON_READINESS.md`
6. Slice #2 gotowy: env-driven profile/platform abstraction + opcjonalny proxy dla storage/session/search przez `aions-api.service`

### Kryteria ukończenia
- [ ] MCP server startuje w WSL2 bez błędów
- [ ] 45+ narzędzi działa (bez desktop_*)
- [ ] Windows MCP nadal primary dla Cursor (desktop, Everything)
- [ ] Tool Bus pattern udokumentowany

### Postęp operacyjny (2026-07-02, slice #2)

- `mcpServers/VS_CODE_MCP_CODEX/src/server.py` nie zakłada już wyłącznie `venv/Scripts/python.exe`; wybór interpretera jest platform-aware.
- Search provider nie jest już Everything-only: Windows zachowuje `Everything`, Linux może zejść do `fd` / `locate`.
- Wybrane ścieżki storage/session mogą być świadomie przepięte na `aions-api.service` przez `AIONS_VECTOR_BACKEND=api` i `AIONS_API_BASE_URL`, bez ruszania `desktop_*`.
- Profile `wsl-dev` i `oracle-linux` mają jawne env dla `AIONS_DEPLOYMENT_PROFILE`, `AIONS_SEARCH_ROOTS`, `DESKTOP_ENABLED`, backendu vector store.

---

## Etap 4 — CBMS + Chroma na ścieżkach Linux (staging → Oracle)

### Cel
Dane na natywnym ext4 — **jako staging przed Oracle Cloud**, nie jako docelowa migracja Windows↔WSL jeśli cloud jest celem.

### Architektura

```
Oracle Cloud (docelowy canonical)     WSL2 ext4 (staging)
├── ~/aions/data/chroma/              ├── ~/aions/data/chroma/ (test)
├── ~/aions/data/cbms/                └── rsync → Oracle gdy gotowe
│
Windows (dziś primary)
├── E:\server wiedzy\data\chroma\     ← replikacja gdy stabilne
└── D:\AIONS-INTEGRATION\             ← CBMS source
```

**Unikać:** pełnej migracji Windows→WSL ext4→Oracle jeśli Oracle jest od razu celem prod.

### Zależności
- Etap 3 (MCP na Linux)
- Decyzja: WSL staging vs bezpośrednio Oracle

### Ryzyka
| Ryzyko | Prawdop. | Mitygacja |
|--------|----------|-----------|
| Podwójna migracja | Wysokie | Sync strategy z Deployment Topology |
| ChromaDB dual-write | Wysokie | Jeden writer; Windows read-only podczas migracji |

### Kryteria ukończenia
- [ ] ChromaDB na ext4 (WSL lub Oracle), 122+ sesji
- [ ] CBMS dostępny, 545 chunks
- [ ] Jeden writer, brak corruption
- [ ] Plan replikacji Windows→Cloud udokumentowany

---

## Etap 5 — Filesystem Index (AIONS Linux Index vs Everything)

### Cel
Własny AIONS provider dla `fast_search` na Linux/WSL; Everything pozostaje na Windows.

### Architektura

```
Tool Bus → Filesystem Index Service
├── WindowsDesktop: Everything (es.exe) — primary
└── LinuxDesktop: `aions-linux-index` (własny indeks AIONS, opcjonalnie zasilany systemowymi prymitywami)
```

### Zależności
- Etap 3 (MCP na Linux)

### Uwaga
Etap **iteracyjny** — równolegle z codziennym użyciem; nie blokuje Etapów 1–4.

### Postęp operacyjny (2026-07-02, slice #1)

- `mcpServers/VS_CODE_MCP_CODEX/src/filesystem_provider.py` wprowadza własny provider `aions-linux-index` oparty o indeks JSON budowany przez AIONS.
- `scripts/aions_indexer.py` pozwala odświeżać i sprawdzać status indeksu z CLI / systemd joba.
- `server.py`, `start_aions_dev.sh`, `start_aions_api.sh` i env templates mają już jawne zmienne `AIONS_SEARCH_PROVIDER`, `AIONS_SEARCH_INDEX_PATH`, `AIONS_SEARCH_AUTO_REFRESH_SECONDS`.
- `runtime/systemd/templates/aions-index.service.example` odświeża teraz indeks AIONS zamiast odpalać ciężki full scan jako domyślny provider search.

### Postęp operacyjny (2026-07-02, slice #2)

- `aions_indexer.py` — akcja `ensure` (refresh tylko gdy brak/stale), bogatszy `status`.
- `filesystem_provider.ensure_fresh()` używany przez `fast_search` na Linux.
- `aions-index.timer.example` — `OnUnitActiveSec=15min` + `Persistent=true`.
- `server.py` — usunięte martwe ścieżki fd/plocate; registry jako single source of truth.

### Kryteria ukończenia
- [x] Własny provider Linux search/index w repo
- [x] Adapter platformowy w `server.py`
- [x] Everything nadal primary na Windows
- [ ] Incremental watcher / inotify dla szybszych refreshy

---

## Etap 6 — Desktop Layer (Desktop Provider abstraction)

### Cel
Abstrakcja `DesktopProvider` — jednolity interfejs, wielu backendów, z pierwszym linux-native slice zamiast samego disabled/fallback.

### Architektura

```
Tool Bus → Desktop Provider Interface
├── WindowsDesktop    ← pywin32, desktop_* (primary — Marcin)
├── LinuxSystem       ← shell / clipboard / window inventory / launch
├── LinuxDesktop      ← screenshot / input / accessibility (kolejny slice)
└── RemoteDesktop     ← freerdp → Windows RDP z WSL2/Oracle
```

```
Windows (primary)
  └─ WindowsDesktop → desktop_* MCP (11 tools)

WSL2 / Oracle
  └─ LinuxSystem  → shell/clipboard/window inventory
  └─ LinuxDesktop → screenshot/input/accessibility (kolejny slice)
  └─ RemoteDesktop → RDP do Windows (gdy potrzeba GUI)
```

**Decyzja: Hybrid** — `WindowsDesktop` primary; Wayland w WSL2 — **nie teraz**.

### Zależności
- Etap 3 (MCP)
- Etap 0 (desktop_* na Windows)

### Postęp operacyjny (2026-07-02, slice #1)

- `mcpServers/VS_CODE_MCP_CODEX/src/desktop_provider.py` wyciąga provider architecture z `server.py`.
- Windows zostaje bezpiecznie na `desktop_control.py`; Linux dostaje własny provider `linux-system`.
- Linux slice obsługuje już `desktop_shell`, `desktop_launch`, `desktop_windows`, `desktop_clipboard`, a reszta akcji zwraca jawny komunikat o brakującej warstwie input/screenshot zamiast ukrytego fallbacku.
- `system_health` raportuje teraz aktywny `desktop_provider`.

### Postęp operacyjny (2026-07-02, slice #2)

- `provider_registry.py` — jawny rejestr search/desktop bez fd/plocate fallbacków na Linux.
- `LinuxDesktopProvider` (`linux-desktop`) — composite: system slice + automation slice (mss screenshot, xdotool click/type/key/scroll/focus).
- `system_health` zwraca `desktop_capabilities` i `search.linux_index` status.
- Windows path (`desktop_control.py`) nietknięty.

### Plan implementacji
1. Rozszerzyć `LinuxDesktop` o screenshot / input / accessibility
2. Dołożyć capability map do dokumentacji runtime
3. Opcjonalnie wpiąć browser/headless jako osobny provider, nie jako ukryty fallback

### Kryteria ukończenia
- [x] WindowsDesktop działa (bez regresji w kodzie ścieżki Windows)
- [x] Linux-native provider architecture istnieje
- [x] LinuxSystem slice działa dla shell/launch/window inventory/clipboard
- [x] LinuxDesktop: screenshot / input / accessibility
- [x] Capability map: które narzędzia gdzie

---

## Etap 6.5 — AIONS Brain (warstwa kognitywna)

### Cel
Formalizacja i rozbudowa warstwy kognitywnej — Planner, Goal Manager, Agent Manager nad istniejącymi `think_*`, `memory_*`, auto-log.

### Architektura

```
AIONS CORE / Brain
├── Planner           ← intencja użytkownika → plan kroków (NOWY)
├── Goal Manager      ← long-term goals, sub-goals (NOWY)
├── Agent Manager     ← wykonanie, delegacja, retry (NOWY)
├── Memory fusion     ← think_* + memory_* + CBMS + auto-log (ISTNIEJE)
├── Tool selection    ← wybór adaptera/narzędzia z Tool Bus (CZĘŚCIOWY)
├── Self-check        ← walidacja wyniku przed return (NOWY)
├── Reflection        ← think_finish, post-mortem (CZĘŚCIOWY)
└── Retry             ← ponowienie przy błędzie (NOWY)
```

### Mapowanie na istniejące narzędzia

| Brain component | MCP / hook | Status |
|-----------------|------------|--------|
| Reasoning | `think_start`, `think_step`, `think_branch`, `think_finish` | ✅ |
| Memory | `memory_recall`, `memory_store`, `session_list` | ✅ |
| Audit trail | auto-log hook, `conv_dump`, `conv_log` | ✅ |
| Domain knowledge | `cbms_search`, `cbms_get_chunk` | ✅ |
| Planner | — | 🔶 Etap 6.5 |
| Goal Manager | — | 🔶 Etap 6.5 |
| Agent Manager | — | 🔶 Etap 6.5 |
| Tool selection | ad-hoc przez agenta | 🔶 formalizacja |
| Self-check | — | 🔶 Etap 6.5 |
| Retry | — | 🔶 Etap 6.5 |

### Zależności
- Etapy 1–3 (runtime + MCP)
- Embryoniczny Brain już działa — to **ewolucja**, nie rewrite

### Ryzyka
| Ryzyko | Prawdop. | Mitygacja |
|--------|----------|-----------|
| Over-engineering | Wysokie | Iteracyjnie; Planner MVP przed pełnym Goal Manager |
| Scope creep | Wysokie | Etap 6.5 = dokumentacja + thin wrappers na think_* |

### Plan implementacji (fazy)
1. **6.5a** — Dokumentacja Brain API; mapowanie think_* → Brain
2. **6.5b** — Planner MVP: `plan_create`, `plan_step`, `plan_status`
3. **6.5c** — Agent Manager: retry wrapper, tool selection registry
4. **6.5d** — Goal Manager: long-term goals w Chroma (session `goals_*`)
5. **6.5e** — Self-check + Reflection hooks w `think_finish`

### Kryteria ukończenia
- [ ] Brain architecture udokumentowana
- [ ] Planner MVP (3+ narzędzia)
- [ ] Retry działa w Agent Manager
- [ ] Long-term goals w memory
- [ ] Brak regresji think_*, memory_*

---

## Etap 7 — AIONS Desktop Shell (UI)

### Cel
Własny interfejs — dashboard, chat, memory browser. **Iteracyjny** — równolegle z codziennym użyciem.

### Technologia
Tauri v2 + Svelte 5 — lżejszy od Electron.

### Zależności
- Etapy 2–5 (runtime, MCP, data, search)

### Kryteria ukończenia
- [ ] Tauri app Windows + Linux
- [ ] Dashboard z system_health
- [ ] Chat z 5+ narzędziami MCP

---

## Etap 8 — GPU/ML Workloads (OPCJONALNY / eksperyment)

### Cel
Eksperymentalne wykorzystanie GPU — **nie filar roadmapy**.

### Hardware reality check

| Parametr | Wartość | Implikacja |
|----------|---------|------------|
| GPU | Quadro M2000M | Maxwell, compute 5.0 |
| VRAM | 4 GB | Za mało na duże LLM |
| CUDA host | 13.0 | Host driver ≠ capability GPU |
| Rola | Opcjonalna | sentence-transformers, tiny quantized models |

```
GPU Service (opcjonalny)
├── embed_text (sentence-transformers) — realistyczne
├── ml_classify (small models) — realistyczne
└── ml_summarize (phi-2 Q4) — eksperyment, VRAM limit
```

**Decyzja:** Etap 8 = **nice-to-have**. Brak GPU nie blokuje Etapów 1–7 ani prod na Oracle ARM (bez GPU).

### Zależności
- Etap 1 (WSL2 CUDA passthrough — opcjonalnie)
- **Brak zależności** dla core platform

### Kryteria ukończenia (jeśli w ogóle)
- [ ] `nvidia-smi` w WSL2 (opcjonalnie)
- [ ] 1+ ML tool działa
- [ ] Udokumentowany verdict: warto / nie warto na M2000M

---

## Etap 9 — Production Hardening (Oracle Cloud + ops)

### Cel
Prod 24/7 na **Oracle Cloud ARM 4 OCPU / 24 GB** — MCP always-on, canonical Chroma/CBMS, backup, monitoring.

### Architektura

```
Oracle Cloud ARM (prod 24/7)
├── aions-mcp (SSE/HTTP, always-on)
├── ChromaDB + CBMS (canonical)
├── systemd services
├── Backup → object storage / E:\ mirror
├── Health alerting
└── Runbook

Windows laptop
├── Cursor + Windows MCP (desktop, Everything)
└── Replikacja Chroma z Oracle (read) gdy stabilne

WSL2
└── dev/staging — nie prod
```

### Zależności
- Etapy 1–4 (staging validated)
- Oracle Cloud instance provisioned
- 2+ tygodnie stabilnego staging

### Plan implementacji
1. Provision Oracle ARM Ubuntu
2. Deploy AIONS Runtime (Etap 2 units)
3. Migracja Chroma/CBMS → Oracle (canonical)
4. MCP SSE/HTTP endpoint (nie tylko stdio)
5. Backup, logrotate, health alerting
6. Replikacja Oracle → Windows (read) dla Cursor
7. Runbook: `AIONS_RUNBOOK.md`

### Postęp operacyjny (2026-07-02, groundwork)

- `runtime/host/install_aions_host.sh` przygotowuje docelowy layout hosta (`/opt/aions`, `/var/lib/aions`, `/var/log/aions`, `/etc/aions`) i manifest instalacji.
- `runtime/host/first_boot_setup.sh` przygotowuje user-space first-boot (`~/aions/config`, `~/aions/logs`, linger) bez ciężkiego provisioningu cloud.
- Oracle env template zna już ścieżki dla własnego indeksu Linux, co zamyka część nośnikowalności runtime między WSL staging a docelowym hostem Linux.

### Kryteria ukończenia
- [ ] MCP 24/7 na Oracle
- [ ] Chroma/CBMS canonical na cloud
- [ ] Daily backup testowany
- [ ] Windows Cursor działa (Windows MCP lub cloud MCP)
- [ ] 14 dni uptime
- [ ] Runbook napisany

---

## Podsumowanie etapów

### Must-have (wartość biznesowa — Etapy 1–4)

| Etap | Nazwa | Czas est. | Working System |
|------|-------|-----------|----------------|
| 0 | Baseline | ✅ Done | AIONS na Windows, 55 tools |
| 1 | WSL2 staging (1-lite) | 2–3 dni | systemd, ~/aions/, venv |
| 2 | AIONS Runtime | 1 tydzień | systemd services, aions-ctl |
| 3 | MCP na Linux | 1–2 tyg. | Tool Bus, MCP adapter WSL2 |
| 4 | Data staging | 1 tydzień | Chroma/CBMS ext4 lub Oracle plan |

**Must-have łącznie:** ~3–4 tygodnie (realistyczne solo+ADHD)

### Iteracyjny polish (równolegle z codziennym użyciem — Etapy 5–9)

| Etap | Nazwa | Czas est. | Priorytet |
|------|-------|-----------|-----------|
| 5 | Filesystem Index | 1 tydzień | Średni |
| 6 | Desktop Provider | 1–2 tyg. | Średni |
| 6.5 | AIONS Brain | 2–3 tyg. | Wysoki (po Etap 3) |
| 7 | Desktop UI | 4 tyg. | Niski (MVP później) |
| 8 | GPU/ML | opcjonalny | Bardzo niski |
| 9 | Oracle prod | 2 tyg. | Wysoki (gdy staging OK) |

**v1 timeline 16 tygodni — odrzucony** jako zbyt długi dla solo+ADHD. Etapy 5–9 = **iteracja równoległa**, nie sekwencyjny waterfall.

---

## Decyzje architektoniczne — rejestr

| Decyzja | Wybór | Odrzucone | Uzasadnienie |
|---------|-------|-----------|--------------|
| Platform framing | AIONS Cognitive Platform | "AIONS OS", custom kernel | Warstwa nad OS, nie konkurencja Linux |
| Linux substrate | WSL2 Ubuntu (staging) | VM, dual-boot, bare metal | Już zainstalowany, niski overhead |
| Prod hosting | Oracle Cloud ARM 24/7 | WSL2 24/7 prod | WSL nie jest prod; laptop nie 24/7 |
| Init system | systemd natywny (wsl.conf) | genie, systemd-wsl, supervisord | WSL 0.67+; prostsze |
| Tool integration | Tool Bus (MCP\|CLI\|REST\|Desktop) | MCP jako centrum | Adapter pattern |
| Desktop strategy | DesktopProvider (Win\|Linux\|Remote) | Wayland w WSL2 | Marcin na Windows |
| Event Bus | Przyszłość (etap 5–6+) | Teraz | Nie over-engineerować |
| Filesystem index | Everything (Win), plocate (Linux) | Tylko jeden | < 100 ms, cross-platform |
| ML/GPU | Opcjonalny eksperyment | Filar roadmapy | M2000M 4GB, Maxwell limit |
| Data canonical | Oracle Cloud (docelowo) | WSL ext4 jako final | Unikaj podwójnej migracji |
| Timeline | 1–4 must-have (~4 tyg.) | 16 tyg. waterfall | Solo+ADHD realistyczny |

---

## Gotowość do Fazy 1

### Co jest gotowe TERAZ (Etap 0 — baseline)

| Element | Status | Dowód |
|---------|--------|-------|
| AIONS MCP v6 (55 tools) | ✅ | `system_health` = ok |
| ChromaDB 122 sesje | ✅ | `E:\server wiedzy\data\chroma` |
| CBMS 545 chunks | ✅ | `D:\AIONS-INTEGRATION\aions_core` |
| Desktop Control (Windows) | ✅ | 11× `desktop_*` |
| Everything search | ✅ | es.exe OK |
| Docker | ✅ | 4 kontenery running |
| WSL2 Ubuntu | ✅ Running | User `aions`, systemd `running`, linger OK |
| Python 3.11 + venv | ✅ | Windows + WSL (unified 3.11; not 3.12 — chromadb/hnswlib) |
| Git repo | ✅ | `aions-server-wiedzy` |
| Backup MCP config | ✅ | `backups/backup_20260702_*` |
| Roadmap v2 | ✅ | Ten dokument |
| Embryoniczny Brain | ✅ | think_*, memory_*, auto-log, CBMS |

### Etap 1-lite — co obejmuje start

| # | Krok | Szacowany czas |
|---|------|----------------|
| 1 | `wsl --set-default Ubuntu && wsl` | 2 min |
| 2 | Edycja `/etc/wsl.conf` → `[boot] systemd=true` | 5 min |
| 3 | `wsl --shutdown` → restart WSL | 2 min |
| 4 | `sudo apt update && apt install python3.11 python3.11-venv git` | 10 min |
| 5 | Clone/symlink repo → `~/aions/` | 5 min |
| 6 | `python3.11 -m venv ~/aions/venv && pip install -r requirements.txt` | 15–30 min |
| 7 | Health: `systemctl is-system-running`, `import chromadb` | 5 min |

**Świadomie POZA scope 1-lite:**
- ❌ Migracja Chroma na ext4 (Etap 4)
- ✅ systemd aions-mcp.service — unit + `aions-ctl mcp-*` (Etap 2 slice #2; bez autostartu)
- ❌ Zmiana `start_aions_mcp.bat` na WSL (Etap 3)
- ❌ Oracle Cloud deploy (Etap 9)

### Blockers

| Blocker | Status | Wpływ na Etap 1 |
|---------|--------|-----------------|
| full_system_scan w toku | 🔄 OK kontynuować | **Brak** — scan nie blokuje WSL setup |
| Ubuntu Stopped | ⚠️ Do uruchomienia | Rozwiązywany krokiem 1 |
| Oracle Cloud nie provisioned | 📋 Planowany | **Brak** — Etap 9, nie 1 |
| CBMS na D:\ | ℹ️ Info | Read-only z WSL `/mnt/d/` OK |

### Werdykt: GO / NO-GO

| | |
|---|---|
| **Werdykt** | **✅ GO** |
| **Uzasadnienie** | Baseline kompletny; WSL2 zainstalowany; brak krytycznych blockerów; scan może trwać równolegle |
| **Akcja Marcina** | Powiedzieć **"start etap 1"** → wykonać Etap 1-lite (7 kroków, ~1 h) |
| **Rollback** | `wsl --unregister Ubuntu` tylko w skrajności; 1-lite nie modyfikuje danych Windows |

---

## Następne kroki

1. **Etap 6 slice #2:** dołożyć linux-native screenshot/input provider zamiast pozostawiać tylko shell/system slice
2. **Etap 9/10 slice #2:** spiąć `runtime/host/` z user/systemd templates i przygotować pierwszy powtarzalny host bootstrap
3. **Etap 3/4:** dalej przepinać wybrane ścieżki MCP na control plane HTTP bez ruszania Windows/prod MCP
4. **Nie przerywać** full_system_scan

---

*Dokument v2 — 2026-07-02 — feedback Marcin + koledzy (Brain + practical). Inwentaryzacja baseline: 2026-07-02T03:26 UTC.*
