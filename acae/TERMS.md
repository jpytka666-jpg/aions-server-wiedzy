# TERMS — acae

Kontrakt terminologiczny. Powstal, bo ryzyko R6 planu (rozjazd terminologii po raz czwarty)
zmaterializowalo sie juz w PLAN v2: `§4.2` zamiast `§4.1`, „85 narzedzi" zamiast 69,
`tools/cbms_doctor.py` zamiast `aions_core/server/`. Jedno miejsce, jedna pisownia.

## Pojecia

| Termin | Znaczenie w ACAE | Czym NIE jest |
|---|---|---|
| `pack` | jeden deterministyczny artefakt opisujacy repo w danym SHA | nie jest chunkiem CBMS ani wpisem pamieci |
| `outline` | szkielet pliku: sygnatury bez cial funkcji | nie jest streszczeniem ani embeddingiem |
| `drill` | dociagniecie ciala pojedynczego symbolu po `name_path` | nie jest ponownym parsowaniem calego drzewa |
| `name_path` | adres logiczny symbolu, np. `CRLACore/evaluate` | nie jest numerem linii — linie sie przesuwaja, adres nie |
| `B_ceiling` | suma tokenow wszystkich plikow w zakresie; koszt zrzutu calosci | nie jest kosztem zadnego realnego zapytania |
| `B_query(q)` | koszt dzisiejszego wejscia w kod dla zapytania `q`: top-K plikow z rankingu grepowego, czytanych w calosci | nie jest kosztem packa |
| `content_hash` | `blake2b256` z surowych bajtow pliku | nigdy z mtime, nigdy ze sciezki absolutnej |
| `pack_hash` | hash kanonicznego manifestu packa | nie jest suma hashy plikow |
| `skipped[]` | pliki poza packiem z jawnym powodem | nie jest cichym pominieciem — brak wpisu to blad |

## Powody w `skipped[]`

`ignored` · `binary` · `too_large` · `secret` · `no_grammar` · `submodule` · `unreadable`

Zamkniete wyliczenie. Plik nie moze wypasc z zakresu bez jednego z tych powodow.
`scan_dir()` w `ts_symbols.py` (`:282-283`) lyka `ValueError` i plik znika bez sladu —
to jest dokladnie ta wlasnosc, ktorej ACAE nie powtarza.

## Decyzje zamkniete

| # | Decyzja | Uzasadnienie |
|---|---|---|
| D2 | `content_hash` = **BLAKE2b-256 ze stdlib**, zapis `"blake2b256:<64 hex>"` | ADR-002 §4.1 wymaga tylko „funkcji czystej od content". BLAKE3 nie pada w ADR-002 ani razu i nie ma go w zadnym venv. Prefiks nazwany wprost, zeby zmiana algorytmu byla widoczna w danych, a nie cicha |
| D3 | licznik tokenow = `tiktoken` / `cl100k_base` | **Zalozenie: to proxy tokenizera Claude'a, nie sam tokenizer.** Poprawne, bo obie bramki (M1, M2) sa STOSUNKAMI — spojne proxy skraca sie w ulamku |
| — | zakres = pliki z rozszerzeniem obecnym w `LANGS` | `LANGS` jest importowane z `aions_core/server/ts_symbols.py`, nie kopiowane. Pack obejmuje pliki z gramatyka, wiec `B_ceiling` musi obejmowac ten sam zbior — inaczej bramka „<= 0,5 x B_ceiling" porownuje polowe jednej rzeczy z caloscia innej |
| — | submoduly poza zakresem | osobne repozytorium; `tools/ChromaFlowStudio` ma gitlink `160000`, ale `.gitmodules` nie istnieje, wiec tresc nie jest odtwarzalna z tego repo. 13798 z 13828 plikow `.py` to wendorowany venv |
| — | brak pola z czasem uruchomienia w artefakcie baseline'u | bramka M0 wymaga plikow identycznych co do bajta; zegar scienny czyni ja nieprzechodnia z definicji. Provenancje niesie `head_committed_at` (czas commita HEAD, deterministyczny dla danego SHA) |

## Zamrozone razem z `tests/queries.json`

Zmiana ktoregokolwiek z ponizszych uniewaznia baseline i wymaga przeliczenia `B_query` od nowa:

- tresc dziesieciu zapytan,
- `STOPWORDS` w `scripts/measure_baseline.py`,
- `top_k`, `min_term_len`, `tokenizer` w `config/acae.toml`,
- regula dopasowania: literal, bez rozroznienia wielkosci liter, liczone **linie** trafione na termin,
- rozstrzyganie remisow: sciezka POSIX rosnaco.

## Znane luki

| Luka | Skutek | Kiedy rozstrzygnac |
|---|---|---|
| `LANGS` nie ma gramatyki dla `.ps1` — w rootach lezy **26** takich plikow | ACAE jest slepy na PowerShell; wypada i z baseline'u, i z packa, wiec bramka M1 pozostaje uczciwa, ale pokrycie repo jest niepelne | M1 |
| M0 wyznacza zakres chodzeniem po drzewie + `git check-ignore`; M1 ma to robic w porcie Locator | jesli reguly sie rozjada, `B_ceiling` przestanie opisywac zbior, ktory pakuje M1 | wejscie w M1 |
