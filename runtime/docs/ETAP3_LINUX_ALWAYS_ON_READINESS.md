# Etap 3 Readiness Blueprint — Oracle Cloud / Linux always-on

Snapshot: 2026-07-02

Cel tego dokumentu: przygotowac bezpieczny most miedzy aktualnym torem `Windows primary + WSL dev` a docelowym `Linux always-on` na Oracle ARM, bez ruszania dzialajacego runtime.

## Zasady

- Nie zastępujemy Windows hosta. `desktop_*` i Everything zostaja po stronie Windows.
- Oracle/Linux to runtime platform dla uslug always-on, nie osobne distro AIONS.
- Etap 3 ma przygotowac Linux-native launch i topology, ale bez deploymentu cloud i bez zmian w aktywnych unitach WSL dev.

## Stan wyjsciowy

Na dzis jest juz gotowe:

- `runtime/scripts/start_aions_mcp.sh` jako Linux/WSL launcher MCP.
- `runtime/systemd/user/aions-mcp.service` i `aions-health.*` jako dzialajacy tor WSL staging.
- `server/app.py` jako lokalny control plane HTTP.
- `server/store_api.py` jako cienki klient do wybranych storage/session paths przez `aions-api.service`.
- `server/store_selector.py` i `server/store_http.py` jako baza pod tryb embedded albo HTTP dla Chroma.
- `runtime/systemd/templates/` jako naturalne miejsce na lekkie artefakty deployowe.

Najwazniejsze luki przed Linux always-on:

- `mcpServers/VS_CODE_MCP_CODEX/src/server.py` nadal niesie duzy surface, ale ma juz start odklejony od `venv/Scripts/python.exe`, profile env i fallback search provider.
- `.aions/python.env` wskazuje dzis WSL-dev path (`/mnt/d/AIONS_DEV/...`), a nie neutralny profil Linux/Oracle.
- `fast_search` ma teraz provider selection (`Everything` -> `fd` -> `locate`), ale Linux path-search nadal wymaga docelowego strojenia pod realne indeksowanie.
- `desktop_*` nie powinny byc traktowane jako capability Linux runtime.

## Matryca portability

### Portable 1:1

| Obszar | Status | Uwaga |
|---|---|---|
| `aions-health.service` + `aions-health.timer` | portable 1:1 | lekkie unity user-space, dobre tez na Oracle |
| `runtime/scripts/start_aions_mcp.sh` | portable 1:1 | dziala jako Linux launcher, o ile env i repo path sa Linux-native |
| `scripts/aions_healthcheck.sh` | portable 1:1 | opiera sie na `aions_python.sh` i `systemctl --user` |
| `server/app.py` | portable 1:1 | localhost-only API pod `uvicorn` |
| `server/store_selector.py` | portable 1:1 | juz umie wybrac Chroma embedded/HTTP |
| `runtime/systemd/templates/aions-api.service.example` | portable 1:1 | dobry kandydat na always-on control plane |

### Wymaga provider abstraction

| Obszar | Status | Co rozdzielic |
|---|---|---|
| `fast_search` / `fast_search_ext` | provider abstraction | Windows=`Everything`, Linux=`plocate` lub `fd` |
| Desktop layer | provider abstraction | Windows=`desktop_*`, Linux=`browser headless`, remote=`RDP/SSH` |
| Launch profiles | provider abstraction | osobny profil `wsl-dev` i `oracle-linux` dla env/path |
| Chroma access mode | provider abstraction | embedded na start, opcjonalnie HTTP po ustabilizowaniu topology |

### Wymaga fallbackow albo graceful degradation

| Obszar | Status | Fallback |
|---|---|---|
| `desktop_*` na Linux | fallback required | `DESKTOP_ENABLED=false`, jawny komunikat capability gap |
| Everything na Linux | fallback required | manualny brak lub przyszly provider `plocate/fd` |
| Chroma shared service | fallback required | gdy HTTP niedostepny, zostac przy embedded |
| GUI automation | fallback required | browser headless lub zdalny Windows jako osobna sciezka |

## Minimalny target service topology

Najmniejszy sensowny target na Oracle/Linux always-on:

1. `aions-api.service`
   - lokalny control plane na `127.0.0.1:${AIONS_API_PORT:-8765}`
   - wystawia `/health`, `/status`, `/search`, `/dashboard`
   - nie bierze odpowiedzialnosci za desktop ani ciezkie skany

2. `aions-health.timer` -> `aions-health.service`
   - watchdog venv, logow i Chroma path
   - zostaje lekki i user-space

3. `aions-mcp.service`
   - traktowany jako adapter integracyjny, nie glowny runtime plane
   - na pierwszym always-on deployu moze zostac sidecarem/stdio launcherem do testow operacyjnych
   - przejscie na SSE/HTTP dopiero po domknieciu providerow i policy transportu

4. `aions-scanner.service` / `aions-index.service`
   - tylko jobs albo low-frequency timery
   - nie robic z nich daemonow always-on

5. Dane
   - `CHROMA_PATH=/home/aions/aions/data/chroma`
   - `AIONS_PATH=/home/aions/aions/data/cbms`
   - jeden writer dla Chroma

## Profil `oracle-linux`

Docelowy profil operacyjny powinien miec:

- repo: `/home/aions/aions-repo`
- logi: `/home/aions/aions/logs`
- dane: `/home/aions/aions/data/{chroma,cbms}`
- `DESKTOP_ENABLED=false`
- `CHROMA_USE_HTTP=false` na pierwszy deployment
- Windows dalej pozostaje primary dla `desktop_*` i Everything

W repo jest do tego sample env:

- `runtime/systemd/templates/aions-runtime.oracle.env.example`

## Najkrotsza sciezka do pierwszego always-on deploymentu

1. Utrzymac obecny WSL staging bez zmian w aktywnych unitach.
2. Dolozyc neutralny profil `oracle-linux` dla sciezek i env.
3. Odciac `server.py` od twardych zaleznosci Windows:
   - interpreter path
   - Everything-only search
   - sciezki `D:/E:/`
4. Przepiac tylko wybrane paths MCP (memory/session/search) na `aions-api.service` przez jawny env `AIONS_VECTOR_BACKEND=api`.
5. Postawic `aions-api.service` jako pierwszy Linux-native always-on service.
6. Zostawic Chroma w embedded mode na start, z jednym writerem.
7. Dopiero potem decydowac, czy `aions-mcp.service` ma byc sidecarem, czy przejsc na transport sieciowy.

## Kryteria readiness przed wdrozeniem

- Linux profile env istnieje i nie wskazuje na `/mnt/d` ani `/mnt/e`
- `aions_python.sh` oraz launcher korzystaja z Linux-native repo i venv
- `server.py` nie zaklada Windows-only binarek jako warunku startu
- capability map jawnie rozdziela Windows-only od Linux runtime
- topology decyzja: `embedded Chroma first` albo `HTTP Chroma first`

## Czego nie robic w tym etapie

- Nie przepinac Cursor prod z Windows MCP na Linux MCP.
- Nie edytowac `aions-ctl`, `mcp.json`, dzialajacych unitow WSL dev ani `requirements-linux*`.
- Nie robic provisioningu Oracle ani ciezkiego deploymentu.
- Nie wprowadzac dual-write dla Chroma.
