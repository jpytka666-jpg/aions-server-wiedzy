# AIONS Runtime Service Map (Etap 2.5/3)

Cel tej notatki: rozdzielić runtime na małe komponenty usługowe bez ruszania działających unitów `aions-health.*` i `aions-mcp.service`.

## Stan obecny

Aktywne i sprawdzone:

- `aions-health.service` + `aions-health.timer` jako watchdog środowiska i logów.
- `aions-mcp.service` jako adapter stdio uruchamiany z wrappera Linux/WSL.

Naturalne granice już widoczne w kodzie:

- `server/app.py` to osobny HTTP control plane (`/health`, `/status`, `/search`, `/dashboard`).
- `server/store_selector.py` pozwala rozdzielić embedded Chroma od HTTP Chroma.
- `mcpServers/VS_CODE_MCP_CODEX/src/server.py` łączy dziś zbyt wiele ról: MCP, health, scan, pamięć i browser/desktop providers, ale search/desktop zaczęły już wychodzić do własnych providerów AIONS.
- `scripts/project_scanner.py`, `scripts/full_system_scan.py` i `scripts/sync_dev_mirror.sh` mają charakter jobów, nie daemonów.

## Minimalny podział usług

### 1. Core control plane

Rekomendowany unit: `aions-api.service`

Rola:

- wystawia lokalne API runtime/knowledge (`server.app:app`)
- stabilizuje granicę między runtime a adapterami
- pozwala w Etapie 3 przepinać MCP na HTTP zamiast bezpośrednio ładować cały stos w jednym procesie

Nie wkładać tutaj:

- desktop tools
- Everything search
- długich skanów
- synchronizacji repo

### 2. MCP api/tool plane

Aktualny unit: `aions-mcp.service` (bez zmian)

Rola:

- adapter narzędziowy dla Cursor/Claude Desktop
- warstwa integracyjna, nie centrum architektury
- może zostać hybrydowy: Windows-primary dla `desktop_*` i Everything, Linux-primary dla tool bus / knowledge access

Rekomendacja:

- nie dokładać do `aions-mcp.service` nowych odpowiedzialności runtime
- długofalowo ograniczyć MCP do adaptera/proxy do `aions-api.service` i wybranych providerów

### 3. Health / monitoring plane

Aktualne unity: `aions-health.service`, `aions-health.timer` (bez zmian)

Rola:

- sprawdzenie Python/venv/Chroma path/logów
- lekki watchdog dla runtime

Rozszerzenie dopiero później:

- opcjonalny health probe dla `aions-api.service`
- opcjonalny probe dla HTTP Chroma, jeśli pojawi się osobny serwis

### 4. Scan / index jobs

Rekomendowane unity:

- `aions-scanner.service` + `aions-scanner.timer`
- `aions-index.service` + `aions-index.timer`

Podział odpowiedzialności:

- `aions-scanner.*` = repo/project scan, zależności, duplikaty, analiza kodu (`project_scanner.py`)
- `aions-index.*` = odświeżenie własnego indeksu Linux (`scripts/aions_indexer.py`) używanego przez `aions-linux-index`

Ważne:

- to mają być `Type=oneshot` jobs, nie always-on services
- indeksacja powinna być rzadsza niż scanner
- `full_system_scan.py` zostaje ciężkim inventory/manual scanem; nie mieszać go z lekkim providerem wyszukiwania

### 5. Optional sync / background jobs

Rekomendowany unit: `aions-sync.service`

Rola:

- synchronizacja repo WSL mirror (`sync_dev_mirror.sh`)
- job uruchamiany ręcznie lub timerem tylko wtedy, gdy mirror naprawdę jest częścią flow

## Dodatkowe, ale nie na siłę

Te usługi warto dodać dopiero wtedy, gdy staną się realną potrzebą runtime:

- `aions-chroma.service` - dopiero gdy Chroma ma działać jako współdzielony HTTP data plane
- `aions-cbms.service` - dopiero gdy CBMS będzie mieć własny preload/daemon lifecycle

Na dziś lepiej traktować je jako data providers niż obowiązkowe procesy Etapu 2.5.

## Rekomendowane zależności

Minimalne zależności na teraz:

```text
aions-health.timer
  -> aions-health.service

aions-api.service
  -> optional After/Wants=aions-chroma.service

aions-mcp.service
  -> działa samodzielnie dziś
  -> w Etapie 3 może mieć After=aions-api.service, jeśli zacznie korzystać z control plane

aions-scanner.timer
  -> aions-scanner.service

aions-index.timer
  -> aions-index.service

aions-sync.service
  -> niezależny job pomocniczy
```

Najważniejsza zasada: tylko health i MCP pozostają always-on w obecnym etapie. Scanner, index i sync to jobs/timery.

## Rekomendowane nazwy unitów

- `aions-api.service`
- `aions-mcp.service` (istniejący)
- `aions-health.service` (istniejący)
- `aions-health.timer` (istniejący)
- `aions-scanner.service`
- `aions-scanner.timer`
- `aions-index.service`
- `aions-index.timer`
- `aions-sync.service`
- opcjonalnie: `aions-chroma.service`, `aions-cbms.service`

## Co wdrażać dalej

1. Uruchomić `aions-api.service` jako osobny localhost-only control plane i nie mieszać go z `aions-mcp.service`.
2. Dodać `aions-scanner.*` jako pierwszy job/timer, a `aions-index.*` oprzeć na `scripts/aions_indexer.py` jako bezpiecznym refreshu własnego indeksu Linux.
3. Host install / first-boot prowadzić przez skrypty stagingowe `runtime/host/install_aions_host.sh` i `runtime/host/first_boot_setup.sh`, zanim pojawi się pełny obraz hosta.
