# AIONS OS Roadmap

**Wersja:** v16  
**Data:** 2026-07-10  
**Maszyna:** Marcin — Windows 10/11, `E:\server wiedzy`  
**Aktywna faza:** **Operator Senses** (Fala 5 — read-only integracje: Gmail, kalendarz, Outlook)

---

## Zasada architektoniczna

> **Linux jest warstwą sprzętową. CBMS jest systemem poznawczym. MCP jest warstwą wykonawczą. LLM jest wymienialnym interfejsem komunikacyjnym.**

Stara numeracja Etap 0–9: [`LEGACY_ETAP_MAP.md`](LEGACY_ETAP_MAP.md)

---

## Status faz (skrót)

| Faza | Nazwa | Status | % |
|------|-------|--------|---|
| 1 | Core Runtime | **Zamknięta** | 100% |
| 2 | Deploy Anywhere | **Zamknięta** | 67% (2/3) |
| 3 | AI Control Plane | **MVP** | 60% |
| 4 | AIONS Identity | **W toku** | 70% |
| 5 | Local Intelligence | Planowana | 0% |
| 6 | Distributed AIONS | Planowana | 0% |
| 7 | Autonomous Infrastructure | Iteracyjna | 25% |
| 8 | AIONS Image | **MVP** | 75% |
| 9 | AIONS Appliance | Planowana | 0% |
| 10 | AIONS Ecosystem | Design only | 0% |

**Milestone C (Hyper-V):** PASS historyczny 2026-07-02 — `D:\AIONS_DEV\logs\milestone-c-hyperv\result.json`. **Stan bieżący 2026-07-11: FAIL** — VM Off, brak L3/Ethernet (szczegóły: `runtime/docs/milestone_c_session_2026-07-11.json`, `PLATFORM_MATRIX.md`).

---

## Faza 1 — Core Runtime ✅

**Cel:** Działający runtime Linux z instalatorem i health.

- [x] CBMS (545+ chunks via `AIONS_PATH`)
- [x] MCP (`aions-context` prod, `aions-dev` WSL staging)
- [x] Health timer + `aions_healthcheck.sh` GREEN
- [x] `install_aions_host.sh` v1 (Milestone B)
- [x] systemd user units (health, mcp, api, index)
- [x] `aions-ctl up/down/status/logs`
- [x] Linux index provider (`aions-linux-index`)
- [x] Python 3.11 unified (`.aions/python.env`)
- [x] Milestone C PASS na Hyper-V VM

**Zamknięcie:** 2026-07-03 — host first-boot z api+index units, runbook SCP w `runtime/host/`

---

## Faza 2 — Deploy Anywhere ✅

**Cel:** AIONS uruchamia się wszędzie: `install → boot → GREEN`

Matryca: [`runtime/docs/PLATFORM_MATRIX.md`](../../runtime/docs/PLATFORM_MATRIX.md)

| Platforma | Status |
|-----------|--------|
| Hyper-V | **PASS** historyczny (2026-07-02); **FAIL bieżący** (2026-07-11, VM Off) |
| Proxmox | **PASS** (2026-07-03, VM 9100 @ 192.168.1.150); health z Windows tylko via jump `.220` |
| VPS cloud-init | **SKIPPED** — decyzja użytkownika 2026-07 (brak płatnej chmury); automation zostaje w `runtime/host/vps/` jako opcjonalna |
| Oracle ARM | TODO |
| Raspberry Pi | TODO |
| Bare metal | TODO (Faza 8) |

**Minimal self-heal (wąski zakres Fazy 7):** `runtime/host/playbooks/` — OnFailure health + daily backup timer

**Kryterium zamknięcia Fazy 2:** min. 3 platformy PASS (Hyper-V + Proxmox + VPS)

**Zamknięcie 2026-07-10:** 2/3 PASS (Hyper-V + Proxmox). VPS Hetzner **permanentnie pominięty** — decyzja Marcina (bez płatnej chmury). Faza uznana za zamkniętą; trzecia platforma opcjonalna, nie blokuje dalszej pracy operatora.

---

## Faza 3 — AI Control Plane

**Cel:** CBMS decyduje → Execution Manager wybiera narzędzia → MCP wykonuje.

```
CBMS Core → Policy Engine → Task Planner → Execution Manager → MCP
```

**MVP:**
- [x] `control_plane/` moduł (`policy`, `planner`, `executor`, `api`)
- [x] `POST /v1/plan`, `POST /v1/execute`, `GET /v1/execution/{id}` (mount w `server/app.py`)
- [x] MCP: `aions_plan`, `aions_execute_step`, `aions_execution_status`
- [x] Smoke: `scripts/test_control_plane.py` — „sprawdź health” → `system_health`

**Zasada:** Nowa logika decyzyjna → `control_plane/`, nie monolit `server.py`.

**Git (2026-07-11):** `cbms_gate.py`, `llm_adapter.py`, `__init__.py` **tracked**; pozostałe moduły MVP (`api.py`, `executor.py`, `models.py`, `orchestrator_loop.py`, `planner.py`, `policy.py`, `scheduler.py`) **untracked** — nie „cały katalog untracked”.

---

## Faza 4 — AIONS Identity

**Cel:** Użytkownik widzi AIONS, nie Ubuntu.

- [x] Hostname `aions`, MOTD, `/etc/issue`
- [x] `runtime/identity/` — motd, profile.d, boot-status unit
- [x] Hook w `install_aions_host.sh` po verify_health
- Boot: „AIONS OS / CBMS ONLINE / Health GREEN / Ready”

---

## Faza 5 — Local Intelligence

**Cel:** LLM jako wymienialny adapter (`AIONS_LLM_PROVIDER=ollama|none`), nie mózg.

`control_plane/llm_adapter.py` — Ollama / OpenAI / none; planner rule-based bez LLM.

---

## Faza 6 — Distributed AIONS

Węzły (laptop, home server, cloud, NAS); sync Chroma/CBMS; `aions_node_status`, `aions_sync_knowledge`.

Zależność: Faza 3 MVP.

---

## Faza 7 — Autonomous Infrastructure

Monitorowanie, restart znanych usług, backupy, degradacja → playbook. Iteracja od Fazy 2 playbooks.

---

## Faza 8 — AIONS Image

Jeden build → VHDX, OVA, QCOW2, Docker, (ISO później).

- [x] `runtime/host/packer/manifest.yaml`
- [x] `runtime/host/packer/aions-host.pkr.hcl` (naprawiony provision order)
- [x] `runtime/host/packer/build_image.ps1` (`-ValidateOnly` PASS 2026-07-03)
- [x] `runtime/host/packer/PROVISION.md` — runbook ręcznego buildu WSL
- [x] `packer init` + `packer validate` WSL (Packer 1.15.4, plugin qemu 1.1.5)
- [x] `packer build` PASS → qcow2 (2026-07-04, ~81 min; SSH ~3 min; validate_install 33/33 GREEN)

---

## Faza 9 — AIONS Appliance

Mini PC + obraz Fazy 8 + first-boot wizard → GREEN w ~10 min.

---

## Faza 10 — AIONS Ecosystem

Design doc: panel WWW, plugin manifest, OTA, zdalne zarządzanie wieloma hostami. Implementacja po Fazie 9.

---

## Deployment Topology (bez zmian)

```
Windows (primary) ── Cursor + aions-context MCP
    │ sync_dev_mirror.ps1
    ▼
WSL D:\AIONS_DEV (staging, user aions)
    │ install → boot → GREEN
    ▼
Hyper-V / Proxmox / VPS / Oracle (deploy targets)
```

| Dane | Canonical |
|------|-----------|
| Kod | `E:\server wiedzy` (git) |
| Chroma prod | `E:\server wiedzy\data\chroma` |
| CBMS | `E:\server wiedzy\aions_core` |
| Dev mirror | `D:\AIONS_DEV\repo\server-wiedzy` |

---

## Changelog

| Wersja | Data | Zmiany |
|--------|------|--------|
| **v16** | 2026-07-10 | Faza 2 zamknięta 2/3 (VPS SKIPPED — decyzja użytkownika); aktywna faza → Operator Senses; CBMS canonical na E:; `CBMS_HUMAN_GUIDE.md`; sync scheduler → MVP lokalnie (Fala 6 ~40%) |
| **v15.3** | 2026-07-03 | Faza 8 → 75%: Packer build #4 PASS (34e12370); qcow2 validate 33/33 GREEN; PLATFORM_MATRIX |
| **v15.2** | 2026-07-04 | Faza 8 Packer build PASS: cloud-init/dpkg lock fix, bundle-staging, qcow2 50GB (~16.5 GiB artifact) |
| **v15.1** | 2026-07-03 | Faza 8 Fala 4: packer validate WSL PASS; PROVISION.md; build qcow2 blocked (kvm/PATH) |
| **v15** | 2026-07-03 | Reframe na Fazy 1–10; Milestone C PASS; LEGACY_ETAP_MAP; PLATFORM_MATRIX; governance AGENTS.md + .cursor/rules |
| v14 | 2026-07-02 | Milestone A/C slices, Etap 3–5 progress |

---

## Operator Senses (aktywna — Fala 5)

**Cel:** Cyfrowy operator „widzi” świat zewnętrzny — najpierw read-only (Gmail, Google Calendar, Outlook).

- **Kod REAL:** `runtime/integrations/` — Google OAuth flow (`google_oauth.py`), moduły Gmail/Calendar
- **Nie live E2E (2026-07-11):** brak credentials w `runtime/secrets/` (tylko przykłady w docs); OAuth wymaga ręcznego setupu Marcina
- **Outlook:** STUB / placeholder — nie zaimplementowany
- Scheduler + proaktywny brief: **MVP działa lokalnie** — `scripts/operator_daily_brief.py` (exit 0), `control_plane/scheduler.py`, endpointy `/v1/scheduler/summary` + `/v1/scheduler/tick`; zostaje timer systemd 08:00 na Linux + toast Windows (szczegóły: [OPERATOR_NEXT_STAGES.md](OPERATOR_NEXT_STAGES.md) — Fala 6 ~40%)
- Przewodnik CBMS dla człowieka: [`docs/CBMS_HUMAN_GUIDE.md`](../../docs/CBMS_HUMAN_GUIDE.md)

---

## Następne kroki

1. ~~Proxmox PASS~~ — **DONE** 2026-07-03
2. ~~Faza 3 smoke + remote hook~~ — **DONE** (`test_control_plane.py`; remote E2E via SSH tunnel)
3. ~~Faza 8 Packer manifest + validate~~ — **DONE** (`build_image.ps1 -ValidateOnly`; `packer validate` WSL)
4. ~~**Faza 8 Packer build qcow2**~~ — **DONE** 2026-07-04 (`build_image.ps1`; artifact `output-aions-host/packer-aions_ubuntu`)
5. ~~Domknięcie Fazy 2~~ — **DONE** 2026-07-10 (2/3; VPS SKIPPED)
6. **Operator Senses** — OAuth read-only Gmail/kalendarz (`runtime/integrations/`)
7. Tier-1 Chroma ingest + `operator_profile` — w toku (Fala 1)
