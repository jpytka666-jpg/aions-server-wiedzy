# Operator Next Stages — plan dla Marcina

**Data:** 2026-07-10  
**Dla:** Marcin — student + cyfrowy operator AIONS  
**Canonical:** `E:\server wiedzy`  
**Powiązane:** [AIONS_OS_ROADMAP.md](AIONS_OS_ROADMAP.md), [CBMS_HUMAN_GUIDE.md](../../docs/CBMS_HUMAN_GUIDE.md)

> Ten dokument opisuje **etapy operatora** (Fala 1–7), nie fazy infrastruktury AIONS OS (Faza 1–10). VPS cloud deploy — **pominięty** (decyzja 2026-07-10).

---

## Kontekst

Marcin buduje **cyfrowego operatora studenckiego**: AIONS pamięta sesje (CBMS + Chroma), wykonuje zadania przez MCP w Cursorze, a w kolejnych falach „widzi” kalendarz/mail i proaktywnie przypomina o deadlinach — bez oddawania kontroli AI.

**Dziś działa (Fala 0–4):**
- CBMS kanoniczny na `E:\server wiedzy\aions_core` (561 chunków)
- MCP prod `aions-context` + dev `aions-dev` (WSL mirror)
- Control plane MVP (`aions_plan`, `aions_execute_step`)
- Katalog skarbów E: (`AIONS_CATALOG`, tier-2 Chroma)
- Przewodnik człowieka: `docs/CBMS_HUMAN_GUIDE.md`

---

## Mapa fal operatora

| Fala | Nazwa | Cel | Status | % |
|------|-------|-----|--------|---|
| **0** | CBMS canonical | Migracja D:→E:, AIONS_PATH, junction WSL | **Zamknięta** | **100%** |
| **1** | Operator profile | `operator_profile.json`, tier-1 Chroma, bootstrap MCP | **W toku** | **75%** |
| **2** | Treasure catalog | INDEX.md, `catalog_2026.json`, tier-2 ingest | **Zamknięta** | **100%** |
| **3** | Human CBMS access | `CBMS_HUMAN_GUIDE.md`, ChromaFlowStudio | **Zamknięta** | **90%** |
| **4** | Control plane daily use | Plan/execute z Cursor, health gate | **MVP** | **60%** |
| **5** | Operator Senses | Gmail, Google Calendar, Outlook — **read-only** | **Scaffolding (code-only)** | **~25%** |
| **6** | Scheduler | Poranny brief, deadliny z profilu, timer systemd | **MVP (lokalnie)** | **~40%** |
| **7** | Trust levels | Polityka: co AI może bez pytania / z potwierdzeniem / nigdy | **Design** | **5%** |

**Średnia ważona (etapy 1–7, bez Fali 0):** ~**41%** — infrastruktura podstawowa gotowa; scheduler działa lokalnie (MVP), integracje zewnętrzne i autonomia przed nami.

---

## Fala 5 — Operator Senses (następny priorytet)

**Cel:** AIONS **czyta** (nie wysyła) kontekst z życia Marcina — maile, kalendarz — żeby odpowiadać na pytania typu „co mam jutro?” lub „czy był mail od wykładowcy?”.

| Integracja | Tryb | Status |
|------------|------|--------|
| Gmail | OAuth read-only | **Kod REAL** (`runtime/integrations/gmail/`) — brak credentials w `runtime/secrets/` (tylko przykłady); **nie live E2E** |
| Google Calendar | OAuth read-only | **Kod REAL** (`runtime/integrations/calendar/`) — j.w.; **nie live E2E** |
| Outlook (opcjonalnie) | Graph API read-only | **STUB** — placeholder, nie zaimplementowany |

**Kryterium zamknięcia:**
- [ ] OAuth flow działa lokalnie (bez sekretów w repo)
- [ ] MCP tool `operator_read_calendar` / `operator_read_mail` (read-only, limit N wiadomości)
- [ ] Polityka: brak auto-odpowiedzi, brak usuwania

**Dla studenta:** pierwszy realny „superpower” poza CBMS — harmonogram zajęć i maile w jednym zapytaniu do agenta.

---

## Fala 6 — Scheduler (proaktywność)

**Status:** **MVP działa lokalnie (~40%)** — rdzeń schedulera i brief przechodzą testy na Windows; brakuje wdrożenia timera na Linux i powiadomień.

**Cel:** Codzienny brief operatora bez otwierania Cursora ręcznie.

| Element | Lokalizacja | Stan |
|---------|-------------|------|
| Skrypt brief | `scripts/operator_daily_brief.py` | ✅ działa (`exit 0`) |
| Scheduler core | `control_plane/scheduler.py` | ✅ istnieje: job queue, `collect_deadlines`, emit eventów |
| API | `GET /v1/scheduler/summary`, `POST /v1/scheduler/tick` | ✅ endpointy zamontowane |
| systemd | `aions-scheduler.service` + `.timer` (08:00) | ⬜ do wdrożenia na Linux |

**Co działa (lokalnie na Windows + WSL):**
- `operator_daily_brief.py` — uruchamia się i kończy `exit 0`
- `control_plane/scheduler.py` — kolejka zadań (`daily_brief`, `deadline_check`, `case_reminder`), scalanie deadline'ów z `deadlines[]` + `active_cases`, alert dla terminów ≤ 3 dni
- Endpointy `/v1/scheduler/summary` i `/v1/scheduler/tick`
- Emisja zdarzeń do `AIONS_LOG_DIR/control_plane/scheduler_events.jsonl`

**Co zostaje do zamknięcia:**
- [ ] Timer systemd 08:00 (`aions-scheduler.timer`) faktycznie **wdrożony na Linux** (WSL/host), nie tylko plik unitu
- [ ] Powiadomienie Windows (toast) — nie email
- [ ] Brief o pełną treść: health MCP + 1 rekomendowana akcja na dziś
- [ ] Weryfikacja end-to-end: timer → brief → zdarzenie w `scheduler_events.jsonl`

**Zależność:** Fala 5 ułatwia brief (kalendarz), ale MVP działa już tylko na `operator_profile` + CBMS.

---

## Fala 7 — Trust levels (bezpieczeństwo operatora)

**Cel:** Jasne reguły — co agent robi sam, co wymaga „tak/nie” od Marcina, czego nigdy.

| Poziom | Przykłady |
|--------|-----------|
| **L0 — auto** | `cbms_search`, `memory_recall`, read plików w repo, health check |
| **L1 — notify** | Zapis do Chroma, nowy chunk CBMS, sync mirror |
| **L2 — confirm** | Git commit/push, skrypt shell poza whitelistą, OAuth token refresh |
| **L3 — forbidden** | Usuwanie maili, płatności, force push, edycja `.env` z sekretami |

**Implementacja:** rozszerzenie `control_plane/policy.py` + wpisy w `operator_profile.json` → egzekwowane przez `aions_execute_step`.

**Dla studenta:** spokój, że „AI nie wyśle maila za mnie” dopóki nie podniesiesz trust level.

---

## VPS — pominięty

| Element | Status |
|---------|--------|
| Hetzner / cloud-init | **SKIPPED** (2026-07-10) |
| Automation (`provision_hetzner.ps1`) | Gotowa, czeka na decyzję |
| Faza 2 AIONS OS | Zamknięta **2/3** (Hyper-V + Proxmox PASS) |

Marcin pracuje **lokalnie na Windows + WSL**; deploy VPS nie blokuje fal operatora 5–7.

---

## Priorytet dla Marcina (kolejność pracy)

1. **Używaj CBMS codziennie** — `docs/CBMS_HUMAN_GUIDE.md`, MCP `cbms_search` + czytanie chunków
2. **Uzupełnij `operator_profile.json`** — kierunek studiów, deadliny w `active_cases`
3. **Fala 5** — jedna integracja read-only (kalendarz Google jako pierwsza — mniej wrażliwe niż Gmail)
4. **Fala 6** — poranny brief (nawet bez kalendarza: lista z profilu)
5. **Fala 7** — trust levels przed jakimkolwiek write do usług zewnętrznych
6. **Opcjonalnie później:** pełny ingest plastrów (nie 343k binariów — tylko wybrane PACK-i)

---

## Procent ukończenia — podsumowanie

```
Etap 1 (profile)     ███████████████░░░░░  75%
Etap 2 (catalog)     ████████████████████ 100%
Etap 3 (human CBMS)  ██████████████████░░  90%
Etap 4 (control)     ████████████░░░░░░░░  60%
Etap 5 (senses)      █████░░░░░░░░░░░░░░░  25%
Etap 6 (scheduler)   ████████░░░░░░░░░░░░  40%
Etap 7 (trust)       █░░░░░░░░░░░░░░░░░░░   5%
─────────────────────────────────────────
Średnia etapów 1–7:  ~41%
Fala 0 (infra CBMS): 100% ✅
```

---

## Następne kroki (konkretne)

| # | Akcja | Właściciel | ETA |
|---|-------|------------|-----|
| 1 | Uzupełnić studies + deadlines w `operator_profile.json` | Marcin | tydzień 1 |
| 2 | OAuth Google Calendar read-only w `runtime/integrations/` | dev | Fala 5 |
| 3 | `operator_daily_brief.py` + timer 08:00 | dev | Fala 6 |
| 4 | Policy trust L0–L3 w control_plane | dev | Fala 7 |
| 5 | Naprawa manifestu `KCBMSACCESS001` (opcjonalnie) | dev | niski |

---

## Changelog

| Data | Zmiana |
|------|--------|
| 2026-07-11 | Korekta live verification: Fala 5 = kod REAL (Google OAuth) bez credentials → nie E2E; Outlook STUB; % 10→25 (scaffolding, nie live) |
| 2026-07-10 | Fala 6 Scheduler: Szkic 15% → MVP ~40% (kod działa lokalnie: `operator_daily_brief.py` exit 0, `control_plane/scheduler.py`, endpointy `/v1/scheduler/*`); zostaje timer systemd 08:00 + toast Windows; średnia 1–7 ~37% → ~41% |
| 2026-07-10 | Utworzono OPERATOR_NEXT_STAGES.md; VPS skip; % per fala 1–7 |

*Dokument w `.claude/specs/` — nie edytować `.cursor/plans/`.*
