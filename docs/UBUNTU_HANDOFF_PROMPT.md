# Handoff prompt — paste into Claude Code CLI on the Ubuntu laptop

Instance-to-instance briefing. Everything the remote Claude needs to attach to
AIONS-Context over the LAN and actually use it. Verified 2026-08-07 from the Windows side.

---

Jesteś Claude Code na moim laptopie z Ubuntu. Twoja bliźniacza instancja siedzi na moim
drugim laptopie (Windows, DESKTOP-UDI6M9F) i przed chwilą przygotowała dla ciebie dostęp
do mojego serwera wiedzy. Poniżej masz wszystko — nie musisz niczego zgadywać ani odkrywać.

## Co to jest AIONS-Context

Mój prywatny serwer wiedzy. Python, FastMCP, żyje na `E:\server wiedzy` na Windowsie.
Trzyma pamięć długoterminową (ChromaDB, 30 sesji), chunki CBMS (159), indeks projektów,
bibliotekę skilli i sterowanie tamtą maszyną. 69 narzędzi.

Do tej pory gadał tylko przez stdio, czyli lokalnie. Dostał drugi transport
(streamable-http) po to, żebyś ty się wpiął przez sieć. Ten sam obiekt serwera,
te same 69 narzędzi — inny kabel.

## Fakty (zweryfikowane, nie sprawdzaj od zera)

| co | wartość |
|---|---|
| endpoint | `http://172.20.10.5:8787/mcp` |
| transport | `http` (streamable-http; NIE sse, NIE stdio) |
| auth | brak, brak TLS — prywatna sieć, świadoma decyzja |
| serverInfo.name | `aions_context_server` |
| liczba narzędzi | 69 |
| firewall | reguła "AIONS MCP HTTP 8787" aktywna, profil Private |
| autostart | Task Scheduler "AIONS MCP HTTP", przy logowaniu |
| IP | DHCP — może uciec, wtedy config się sypie |

## Krok 1 — sonda, zanim cokolwiek dodasz

```bash
curl -sS -i --max-time 10 -X POST http://172.20.10.5:8787/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"probe","version":"1"}}}'
```

Oczekiwane: HTTP 200 i w treści SSE `"name":"aions_context_server"`.

Diagnoza, gdy nie 200 — nie obchodź, zdiagnozuj i powiedz mi który to przypadek:

| objaw | przyczyna | co mam zrobić |
|---|---|---|
| timeout / no route | izolacja klientów na routerze SMC.LTD.GB (firewall JEST ustawiony) | wyłączyć AP isolation |
| connection refused | serwer nie stoi | odpalić `start_aions_http.bat` na Windows |
| HTTP 421 | stary proces bez `AIONS_HTTP_ALLOWED_HOSTS=*` | zrestartować serwer |
| HTTP 404 | zła ścieżka | endpoint to `/mcp` |

Gdy host milczy, sprawdź czy IP nie uciekło:
`ping -c1 DESKTOP-UDI6M9F ; ip neigh ; nmap -sn 172.20.10.0/28`

## Krok 2 — podłączenie (dopiero po 200)

```bash
claude mcp add --transport http -s user aions http://172.20.10.5:8787/mcp
claude mcp list
```

`-s user` = dostępny w każdym projekcie na tej maszynie, nie tylko w bieżącym katalogu.

## Krok 3 — dowód, nie deklaracja

1. `claude mcp list` → `aions` musi być **connected**
2. Zawołaj `system_health`
3. Zawołaj `cbms_search` z query `"AIONS"`
4. Zawołaj `memory_recall` z `query="AIONS"` **i** `session_id="claude_marcin_main"`

## Jak to faktycznie działa — pułapki, na które wpadła instancja z Windows

**Offload.** Duże odpowiedzi nie wracają w całości. Dostajesz:
`{"status":"ok","offloaded":"OFF_25444907","size":8869,"summary":"..."}`
To nie jest błąd i nie jest to cała odpowiedź. Musisz zawołać `offload_get`
z `ref_id="OFF_25444907"`, żeby dostać treść. Prawie każde bogatsze narzędzie tak robi.

**memory_recall wymaga session_id.** Schema sugeruje że jest opcjonalny — nie jest,
poleci błąd walidacji. Zawsze podawaj `session_id="claude_marcin_main"`.

**session_bootstrap bywa wolny.** Potrafi wywalić timeout. Daj mu jedną próbę,
zgłoś jedną linią że nie wyszło, jedź dalej z `system_health` + `memory_recall`.
Nie udawaj że sprawdziłeś coś, czego nie sprawdziłeś.

**desktop_shell bywa kapryśny.** Zdarza się `"Desktop unavailable"` — ponów raz.
Gubi się na `$` i na ścieżkach ze spacjami (`E:\server wiedzy` to pole minowe).
Do plików używaj raczej narzędzi filesystemowych niż shella.

**Auto-logging.** Serwer sam loguje wywołania do bufora. `conv_status` pokazuje stan,
`conv_dump` wymusza zapis. Nic nie musisz robić ręcznie.

## Co masz pod ręką (grupy narzędzi)

| grupa | narzędzia | do czego |
|---|---|---|
| wiedza | `cbms_search`, `cbms_get_chunk`, `memory_recall`, `memory_store` | pamięć długoterminowa, chunki |
| szukanie | `fast_search`, `fast_search_ext`, `project_search`, `project_scan_turbo` | Everything, indeks projektów |
| skille | `skill_list`, `skill_search`, `skill_run`, `forge_request`, `forge_promote` | biblioteka gotowych bloków |
| myślenie | `think_start`, `think_step`, `think_branch`, `think_finish` | ustrukturyzowane rozumowanie |
| plan | `aions_plan`, `aions_execute_step`, `aions_execution_status` | control plane |
| system | `system_health`, `git_status`, `git_log`, `docker_ps`, `wsl_run` | diagnostyka hosta |
| pulpit | `desktop_shell`, `desktop_click`, `desktop_type`, `desktop_snapshot` | zdalne ręce na Windowsie |
| przeglądarka | `browser_navigate`, `browser_click`, `browser_get_text` | automatyzacja www |

**Świadomie:** `desktop_*`, `wsl_*` i `fast_search` wykonują się **na Windowsie**, nie na
Ubuntu. `fast_search` przeszuka dyski C/E/F tamtej maszyny, nie twój filesystem. To zdalne
ręce na maszynie z wiedzą — tak ma być. Nie "naprawiaj" tego, gdy zwróci windowsowe ścieżki.

## Zasady pracy ze mną

- Sprawdzaj AIONS zanim zaczniesz budować — `fast_search` i `memory_recall` najpierw.
  Reuse > extend > new. Najdroższy błąd to zbudowanie czwartej kopii czegoś, co już leży na dysku.
- Nie mów "gotowe" bez wykonanej komendy i wyniku. Nie da się wykonać — napisz
  `NIEZWERYFIKOWANE: <dokładny ręczny sprawdzian>`. To jest OK. Ściemnianie nie jest.
- Narzędzie, które padło, dostaje jedną linię raportu — nigdy ciche pominięcie.
- Odpowiadaj po polsku. Kod, nazwy plików, commity po angielsku.

## Na koniec

Powiedz mi w jednym zdaniu: podłączone czy nie, ile narzędzi widzisz, i co było blokerem
jeśli coś nie zagrało. Potem czekaj — nic nie buduj, dopóki nie powiem co robimy.
