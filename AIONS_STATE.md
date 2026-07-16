# AIONS — STATE (zywy plik stanu)

> Auto-generowany przez runtime/aions_state.py. Sekcja "Roadmapa/decyzje/backlog"
> pochodzi z runtime/aions_state_manual.md (edytuj tam). Odswiez: `python runtime/aions_state.py`.

**Ostatnia aktualizacja:** 2026-07-16 16:03 UTC

## Serwery (health na zywo)
- Phi-4-mini (llama.cpp)  :8877  -> **UP**
- Core (uvicorn)          :8765  -> **UP**
- ChromaDB                :8000  -> **UP**

## Liczby
- Skille: **87**  ·  Recipes: **12**
- ChromaDB kolekcji: **26**  ·  glowna pamiec (session_claude_marcin_main): **936** docs
- Nody w rejestrze: **4**

## Autostart / samozarzadzanie
- Zadania harmonogramu: AIONS_LLM_Server, AIONS_Core, AIONS_Chroma_Server (onstart)
- AIONS_Services_Watchdog (co 2 min, restart+weryfikacja), AIONS_Operator_Soak (co 5 min)

---

## Roadmapa (cel: AI-operated OS)
- Rung 4a (operuje Linuksem): ✅ 100% — 21+ skilli linux, SSHExecutor, bramka ryzyka, forge sandbox, recipes
- Rung 4b (operator autonomiczny): ✅ MVP — pętla observe→diagnose→act→verify→learn, self-heal (systemd+operator), podopieczni nginx+aions-dummy
- Rung 5 (multi-node): 🟡 ~60% — node agent (proxmox-9100 heartbeat), Core registry; TODO C2 dispatch przez agenta
- Rung 6 (appliance): 🔴 ~10% — koncepcja qcow2
- Definicja AI OS (10 pkt Marcina): ~75%
- **NASTĘPNY DUŻY KROK: migracja E:\server wiedzy → Redox na dysku testowym (NIE na żywym systemie)**

## Kluczowe decyzje
- Baza produkcyjna = Linux; Redox = tor badawczy (raport AIONS_OS_PLATFORM_RESEARCH.md)
- Model lokalny = Phi-4-mini na llama.cpp (Bielik skasowany); serwer rezydentny :8877, RAM, --n-gpu-layers 0
- Agenci = bloki (agents_lib), plug-and-play jak skille
- Most recipes↔CBMS = semantyczne trafianie parafraz (próg 0.55; embedder EN — backlog: wielojęzyczny)

## Backlog (priorytety)
1. C2: dispatch z Core przez NodeAgentExecutor (realne rozgłaszanie zadań na nody)
2. Watchdog: potwierdzić auto-recovery przy naturalnym cyklu; rozważyć NSSM (usługi Windows z auto-restart)
3. Embedder wielojęzyczny w Chromie (PL parafrazy 0.7+) + raw-HTTP chroma bez importu SDK (<1s)
4. desktop_shell: restart serwera MCP by aktywować fix _check_deps (cache tylko sukcesu)
5. Migracja Linux→Redox: build w QEMU na dysku testowym, port skill-runnera jako PoC

## Poligon / infrastruktura
- VM Ubuntu "aions" 192.168.1.150 (ssh aions-node-1, user aions z bramką sudoers)
- Proxmox host .220; Hyper-V MacAddressSpoofing=On (fix sieci)
- Dysk lab: G:\AIONS_LAB (exFAT 477GB) — struktura research/architecture/kernel_tests/os_images/backup/documentation
- Repo: E:\server wiedzy (canonical), mirror D:\AIONS_DEV

