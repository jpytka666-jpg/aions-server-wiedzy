# AIONS — dev mirror (E: → D:)

Lustrzana kopia kodu i plików projektu na dysku `D:` dla pracy w WSL2 / staging Linux, bez kopiowania ciężkich lub lokalnych artefaktów.

## Ścieżki

| Rola | Ścieżka |
|------|---------|
| **Źródło (kanoniczne)** | `E:\server wiedzy` |
| **Cel (dev mirror)** | `D:\AIONS_DEV\repo\server-wiedzy` |

## Wykluczenia

Skrypt **nie** kopiuje:

- `venv/` — wszystkie katalogi o nazwie `venv` (root i zagnieżdżone, np. `tools/ChromaFlowStudio/venv`)
- `data/chroma/` — baza wektorowa ChromaDB (~MB/GB, specyficzna dla maszyny)
- `scan_results/` — wyniki skanów systemowych
- `__pycache__/` — cache Pythona (wszędzie w drzewie)
- `.git/` — domyślnie wykluczone (cel to zwykle osobny clone; użyj `-IncludeGit` / `--include-git` jeśli potrzebujesz)

## Kiedy uruchamiać

Uruchom synchronizację **po zmianach na `E:\server wiedzy`**, zanim:

- otworzysz projekt w WSL z `~/aions` lub `/mnt/d/AIONS_DEV/repo/server-wiedzy`
- uruchomisz testy MCP / `aions-ctl` / healthcheck na Linuxie
- zrobisz commit lub push z kopii na D: (jeśli pracujesz z mirroru zamiast bezpośrednio z E:)

**Nie** uruchamiaj po każdym zapisie pliku — wystarczy po większej porcji pracy (feature, refactor, przed sesją WSL).

Typowy workflow:

1. Praca w Cursor na `E:\server wiedzy`
2. `.\scripts\sync_dev_mirror.ps1` (lub `-DryRun` przed pierwszym razem)
3. W WSL: `cd /mnt/d/AIONS_DEV/repo/server-wiedzy` i dalsza praca

## Windows (robocopy)

Z katalogu repo na E::

```powershell
# Podgląd — ile plików by zsynchronizował (bez zapisu)
.\scripts\sync_dev_mirror.ps1 -DryRun

# Właściwa synchronizacja
.\scripts\sync_dev_mirror.ps1
```

Opcjonalnie:

```powershell
# Usuń z D: pliki, których nie ma już na E: (pełne lustro)
.\scripts\sync_dev_mirror.ps1 -Mirror

# Skopiuj też .git
.\scripts\sync_dev_mirror.ps1 -IncludeGit
```

Wynik dry-run: sekcja **Files** / **Dirs** w podsumowaniu robocopy — kolumna **Copied** = pliki/katalogi do skopiowania lub aktualizacji.

## WSL (rsync, opcjonalnie)

```bash
cd "/mnt/e/server wiedzy"
chmod +x scripts/sync_dev_mirror.sh
./scripts/sync_dev_mirror.sh --dry-run
./scripts/sync_dev_mirror.sh
```

## Czego skrypt nie robi

- Nie instaluje zależności (`pip`, venv)
- Nie konfiguruje systemd ani MCP (`mcp.json`)
- Nie synchronizuje ChromaDB — na WSL ustaw `CHROMA_PATH` osobno lub użyj pustej/testowej bazy

## Cursor MCP — prod vs dev

Dwa niezależne serwery MCP w `C:\Users\User\.cursor\mcp.json`:

| Entry | Rola | Uruchomienie | Chroma / CBMS |
|-------|------|--------------|---------------|
| **`aions-context`** | **Prod** (codzienna praca) | `E:\server wiedzy\venv\Scripts\python.exe` → `__main__.py stdio` | `E:\server wiedzy\data\chroma`, `E:\server wiedzy\aions_core` |
| **`aions-dev`** | **Dev** (WSL staging na D:) | `D:\AIONS_DEV\start_aions_dev.bat mcp` → WSL `start_aions_dev.sh mcp` | `D:\AIONS_DEV\data\chroma`, `AIONS_PATH=/mnt/d/AIONS_DEV/cbms` (junction → canonical) |

### Włączenie dev MCP

1. Upewnij się, że mirror jest zsynchronizowany: `.\scripts\sync_dev_mirror.ps1`
2. Smoke z Windows: `D:\AIONS_DEV\start_aions_dev.bat test-imports` (lub `test-server`)
3. W Cursor: **Settings → MCP** — oba entry widoczne; włącz `aions-dev` obok `aions-context`
4. Po każdej edycji `mcp.json`: **Reload MCP** (lub restart Cursor)

### Kiedy którego używać

- **`aions-context`** — domyślny: desktop_*, Everything, prod Chroma, pełne narzędzia Windows
- **`aions-dev`** — testy zmian przed prod, Linux/WSL ścieżki, osobna dev Chroma; bez desktop_* (WSL)

Prod entry **nie edytuj** przy pracy nad dev — dodawaj/zmieniaj tylko `aions-dev`.

Backup `mcp.json`: `C:\Users\User\.cursor\backups\mcp.json.<timestamp>.bak`

Szczegóły layoutu D: i zmiennych WSL: `D:\AIONS_DEV\README_DEV.md`

## Unified launcher Windows -> WSL

Do codziennej obsługi dev runtime z Windows używaj jednego launchera:

```powershell
.\start_aions_dev.bat status
```

Launcher:

- deleguje do WSL user `aions`
- odpala `D:\AIONS_DEV\start_aions_dev.sh`
- dla komend runtime woła centralny manager `./scripts/aions-ctl`
- nie dotyka prod `aions-context` ani Windows MCP

Najważniejsze komendy:

```powershell
.\start_aions_dev.bat up
.\start_aions_dev.bat down
.\start_aions_dev.bat restart
.\start_aions_dev.bat status
.\start_aions_dev.bat logs
.\start_aions_dev.bat logs mcp
.\start_aions_dev.bat logs health
.\start_aions_dev.bat mcp
```

Uwagi:

- `mcp` zostaje entrypointem stdio dla `aions-dev` MCP w Cursor
- `status` bez argumentu pokazuje stan całego runtime
- `logs` bez argumentu pokazuje health + mcp

## Runtime dev pod WSL

Minimalny runtime Etapu 2.5 działa jako user `aions` i obejmuje:

- `aions-health.timer` — okresowy health check
- `aions-health.service` — ręczne odpalenie health checka
- `aions-mcp.service` — MCP runtime w systemd user
- `aions-api.service` — localhost control plane (:8765)
- `aions-index.timer` — periodic index refresh

## Roadmap (AIONS OS v15)

**Aktywna faza:** Faza 2 — Deploy Anywhere. SSOT: [`.claude/specs/AIONS_OS_ROADMAP.md`](.claude/specs/AIONS_OS_ROADMAP.md)  
**Agenci:** [`AGENTS.md`](AGENTS.md) · Platform matrix: [`runtime/docs/PLATFORM_MATRIX.md`](runtime/docs/PLATFORM_MATRIX.md)

Faza 1 (Core Runtime) — **zamknięta**. VM test: `runtime/host/continue_milestone_c.ps1`

Typowy daily-use:

```powershell
.\scripts\sync_dev_mirror.ps1
.\start_aions_dev.bat up
.\start_aions_dev.bat status
.\start_aions_dev.bat logs mcp
.\start_aions_dev.bat restart
.\start_aions_dev.bat down
```

Najważniejsze komendy operacyjne:

```bash
./scripts/aions-ctl up
./scripts/aions-ctl down
./scripts/aions-ctl restart
./scripts/aions-ctl status
./scripts/aions-ctl logs
./scripts/aions-ctl logs mcp
./scripts/aions-ctl logs health
```

Uwagi:

- `up` instaluje unity do `~/.config/systemd/user`, włącza `aions-health.timer` i startuje `aions-mcp.service`
- `down` zatrzymuje MCP i wyłącza timer health, ale nie rusza Windows/prod MCP
- `status` pokazuje zbiorczy stan runtime
- logi są w `~/aions/logs/health.log` i `~/aions/logs/mcp.log`
- launcher Windows jest tylko wygodnym wrapperem nad WSL `start_aions_dev.sh` + `aions-ctl`

## Etap 3 slice: `aions-api.service`

Pierwszy bezpieczny slice control plane jest localhost-only i nie dotyka aktywnego flow MCP. Artefakty WSL/dev:

- `runtime/scripts/start_aions_api.sh`
- `runtime/systemd/user/aions-api.service`
- `runtime/systemd/user/aions-runtime.env`

Ręczny smoke test w WSL jako user `aions`:

```bash
mkdir -p ~/.config/systemd/user ~/aions/bin ~/aions/config ~/aions/logs
test -L /mnt/e/aions-repo || ln -s "/mnt/e/server wiedzy" /mnt/e/aions-repo
cp /mnt/e/server\ wiedzy/runtime/systemd/user/aions-api.service ~/.config/systemd/user/
cp /mnt/e/server\ wiedzy/runtime/scripts/start_aions_api.sh ~/aions/bin/
chmod +x ~/aions/bin/start_aions_api.sh
sed "s|@HOME@|$HOME|g" /mnt/e/server\ wiedzy/runtime/systemd/user/aions-runtime.env > ~/aions/config/aions-runtime.env
systemctl --user daemon-reload
systemctl --user start aions-api.service
curl -fsS http://127.0.0.1:8765/health
curl -fsS http://127.0.0.1:8765/status
systemctl --user stop aions-api.service
```

Ważne:

- unit nie jest dodawany do `aions-ctl` i nie robi `enable --now`
- port jest związany z `127.0.0.1`, więc slice nie wystawia API poza host WSL
- `aions-mcp.service` pozostaje niezależnym adapterem/tool-plane
