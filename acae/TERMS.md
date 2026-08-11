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
| `slice` (`acae.slice.v1`) | wycinek szkieletu pod JEDNO pytanie plus ciala kilku symboli | nie jest packiem; nie jest zapisywany jako artefakt trwaly |
| `name_path` | adres logiczny symbolu, np. `CRLACore/evaluate` | nie jest numerem linii — linie sie przesuwaja, adres nie |
| `B_ceiling` | suma tokenow wszystkich plikow w zakresie; koszt zrzutu calosci | nie jest kosztem zadnego realnego zapytania |
| `B_query(q)` | koszt dzisiejszego wejscia w kod dla zapytania `q`: top-K plikow z rankingu grepowego, czytanych w calosci | nie jest kosztem packa |
| `content_hash` | `blake2b256` z bajtow znormalizowanych | nigdy z mtime, nigdy ze sciezki absolutnej |
| `pack_hash` | hash kanonicznego manifestu **bez pola `pack_hash`** | nie jest suma hashy plikow |
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
| — | zakres = pliki z rozszerzeniem obecnym w `LANGS` | `LANGS` jest importowane z `aions_core/server/ts_symbols.py`, nie kopiowane. Pack obejmuje pliki z gramatyka, wiec `B_ceiling` musi obejmowac ten sam zbior |
| — | submoduly poza zakresem | osobne repozytorium; `tools/ChromaFlowStudio` ma gitlink `160000`, ale `.gitmodules` nie istnieje. 13798 z 13828 plikow `.py` to wendorowany venv |
| — | brak pola z czasem uruchomienia w artefaktach pomiarowych | bramki wymagaja plikow identycznych co do bajta; zegar scienny czyni je nieprzechodnimi z definicji |
| M1-a | `content_hash` z bajtow **ZNORMALIZOWANYCH** (CRLF/CR -> LF, BOM sciety) | repo ma `core.autocrlf=true`, wiec hash z doslownie surowych bajtow bylby wlasnoscia systemu operacyjnego, a nie tresci kodu. Normalizacja zachodzi RAZ, w porcie `Reader` |
| M1-b | `symbols.py` sklada `SymbolIndex` z bajtow przez **prywatna** `_walk` | `SymbolIndex.from_file()` sam otwiera plik (`ts_symbols.py:131-132`), co lamie bramke „rdzen bez dysku". Dotykamy `_walk` w JEDNYM miejscu (`index_from_bytes`), zeby sprzezenie mialo jeden punkt pekniecia |
| M1-c | liczba tokenow **nie wchodzi** do manifestu, tylko na stdout | inaczej `pack_hash` zalezalby od wersji `tiktoken` |
| M1-d | pakowanie jednowatkowe | drzewa tree-sittera nie sa thread-safe; determinizm i tak wymaga stabilnej kolejnosci |
| **M2-a** | ranking wazy terminy **rzadkoscia** w repo (`term_rarity`, waga calkowita, sufit `RARITY_CAP=64`) | bez tego wygrywa termin CZESTY, nie ISTOTNY. Zmierzone: dla pytania o provenance `CBMSMemory` mial 6 pkt (czeste „memory" w nazwie, sygnaturze i sciezce), a `provenance()` tylko 5 — odpowiedz przegrywala z tlem. Sufit chroni przed literowka, ktora pada raz i przewraca ranking |
| **M2-b** | wagi pol: `name_path` 3, sygnatura 2, sciezka 1 | nazwa symbolu jest mocniejszym sygnalem niz nazwa katalogu; bez zroznicowania kazdy symbol w `memory.py` dziedziczy trafienie po sciezce |
| **M2-c** | parametry wycinka (`outline_limit`, `drill`, `max_body_lines`) **NIE sa zamrozone** | zamrozony jest baseline, bo to punkt odniesienia. Parametry wycinka wolno stroic — kazdy przebieg `measure_m2.py` zapisuje je w artefakcie, wiec wynik zawsze wiadomo z czym porownywac |
| **M2-d** | uciete cialo jest oznaczone w tresci wycinka | ciche ucinanie zamienialoby oszczednosc tokenow w gubienie kodu |

## Zamrozone razem z `tests/queries.json`

Zmiana ktoregokolwiek z ponizszych uniewaznia baseline i wymaga przeliczenia `B_query` od nowa:

- tresc dziesieciu zapytan,
- `STOPWORDS` (w `scripts/measure_baseline.py` **i** w `src/acae/retrieve.py` — musza byc identyczne),
- `top_k`, `min_term_len`, `tokenizer` w `config/acae.toml`,
- regula dopasowania w baseline: literal, bez rozroznienia wielkosci liter, liczone **linie** trafione na termin,
- rozstrzyganie remisow: sciezka POSIX rosnaco.

## Sprzezenia do pilnowania

| Sprzezenie | Co peknie, gdy sie zmieni | Gdzie sprawdzic |
|---|---|---|
| `SymbolIndex._walk` jest prywatna | zmiana sygnatury albo nazwy w `ts_symbols.py` wywroci `index_from_bytes` | `tests/test_symbols.py` — czerwony natychmiast |
| `query_terms` i `STOPWORDS` istnieja w DWOCH miejscach | rozjazd oznacza, ze M2 porownuje wycinek z baseline'em policzonym na innych slowach, czyli z niczym | `tests/test_retrieve.py::test_terminy_zgadzaja_sie_z_baselinem_na_wszystkich_zamrozonych_zapytaniach` |
| `collect_entries` wspolne dla M1 i M2 | druga kopia regul odrzucania rozjechalaby zakresy i bramka M2 przestalaby byc porownywalna z M1 | `pack_hash` niezmieniony po refaktorze |
| `LANGS` importowane, nie kopiowane | dodanie gramatyki zmienia zakres packa I baseline'u naraz, czyli spojnie | `scripts/measure_baseline.py`, `src/acae/symbols.py` |
| piny `tree-sitter` / `tree-sitter-language-pack` | zmiana wersji gramatyki zmienia outline, wiec `pack_hash` (ryzyko R9) | `requirements.txt`, `pyproject.toml`, `.now/CONTRACT.md` |
| `core.autocrlf=true` w repo | bez `normalize_source` na brzegu `pack_hash` rozjezdza sie miedzy systemami | `tests/test_determinism.py` |

## Znane luki

| Luka | Skutek | Kiedy rozstrzygnac |
|---|---|---|
| `LANGS` nie ma gramatyki dla `.ps1` — w rootach lezy **26** takich plikow | ACAE jest slepy na PowerShell; wypada i z baseline'u, i z packa, wiec bramka pozostaje uczciwa, ale pokrycie repo jest niepelne | otwarte |
| ranking jest **wylacznie leksykalny** | pytanie zadane slowami, ktorych w kodzie nie ma (synonim, polski termin, opis zamiast nazwy), nie znajdzie niczego. Zamrozone zapytania sa po angielsku i uzywaja slownictwa z kodu, wiec bramka M2 tej slabosci NIE mierzy | przed uznaniem ACAE za gotowe do codziennego uzycia |
| `manifest["root"]` to nazwa katalogu | ten sam kod spakowany z katalogu o innej nazwie da inny `pack_hash` | przed M3, jesli pack ma byc porownywany miedzy klonami |
| ~~M0 i M1 moga sie rozjechac w regule wyznaczania zakresu~~ | **ZAMKNIETE.** Oba licza 169 plikow ta sama sciezka kodu (`collect_entries`) | — |
