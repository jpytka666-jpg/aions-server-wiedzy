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
| — | zakres = pliki z rozszerzeniem obecnym w `LANGS` | `LANGS` jest importowane z `aions_core/server/ts_symbols.py`, nie kopiowane. Pack obejmuje pliki z gramatyka, wiec `B_ceiling` musi obejmowac ten sam zbior — inaczej bramka „<= 0,5 x B_ceiling" porownuje polowe jednej rzeczy z caloscia innej |
| — | submoduly poza zakresem | osobne repozytorium; `tools/ChromaFlowStudio` ma gitlink `160000`, ale `.gitmodules` nie istnieje, wiec tresc nie jest odtwarzalna z tego repo. 13798 z 13828 plikow `.py` to wendorowany venv |
| — | brak pola z czasem uruchomienia w artefakcie baseline'u | bramka M0 wymaga plikow identycznych co do bajta; zegar scienny czyni ja nieprzechodnia z definicji. Provenancje niesie `head_committed_at` (czas commita HEAD, deterministyczny dla danego SHA) |
| **M1-a** | `content_hash` liczony z bajtow **ZNORMALIZOWANYCH** (CRLF/CR -> LF, BOM sciety), a nie doslownie surowych jak w PLAN v2 §6.3 | repo ma `core.autocrlf=true`, wiec ten sam commit lezy na dysku z CRLF na Windowsie i z LF na Linuksie. Hash z doslownie surowych bajtow byłby wlasnoscia systemu operacyjnego, a nie tresci kodu, i bramka „ten sam `pack_hash` miedzy maszynami" bylaby nie do spelnienia. Normalizacja zachodzi RAZ, w porcie `Reader` — rdzen widzi juz tylko LF |
| **M1-b** | `symbols.py` sklada `SymbolIndex` z bajtow, uzywajac **prywatnej** metody `_walk` | `SymbolIndex.from_file()` sam otwiera plik (`ts_symbols.py:131-132`), co lamie bramke „rdzen przechodzi testy bez dotykania dysku". Alternatywy odrzucone: dopisanie `from_bytes()` lamie ADDITIVE ONLY, plik tymczasowy wnosi I/O do rdzenia |
| **M1-c** | liczba tokenow **nie wchodzi** do manifestu, tylko na stdout | inaczej `pack_hash` zalezalby od wersji `tiktoken`, czyli od czegos, co nie ma zwiazku z trescia repo |
| **M1-d** | pakowanie jednowatkowe | drzewa tree-sittera nie sa thread-safe (dokumentacja wymaga jawnej kopii drzewa do uzycia w wielu watkach). Determinizm i tak wymaga stabilnej kolejnosci |

## Zamrozone razem z `tests/queries.json`

Zmiana ktoregokolwiek z ponizszych uniewaznia baseline i wymaga przeliczenia `B_query` od nowa:

- tresc dziesieciu zapytan,
- `STOPWORDS` w `scripts/measure_baseline.py`,
- `top_k`, `min_term_len`, `tokenizer` w `config/acae.toml`,
- regula dopasowania: literal, bez rozroznienia wielkosci liter, liczone **linie** trafione na termin,
- rozstrzyganie remisow: sciezka POSIX rosnaco.

## Sprzezenia do pilnowania

| Sprzezenie | Co pekniе, gdy sie zmieni | Gdzie sprawdzic |
|---|---|---|
| `SymbolIndex._walk` jest prywatna | zmiana sygnatury albo nazwy w `ts_symbols.py` wywroci `outline_from_bytes` | `tests/test_symbols.py` — czerwony natychmiast |
| `LANGS` importowane, nie kopiowane | dodanie gramatyki zmienia zakres packa I baseline'u naraz, czyli spojnie | `scripts/measure_baseline.py`, `src/acae/symbols.py` |
| piny `tree-sitter` / `tree-sitter-language-pack` | zmiana wersji gramatyki zmienia outline, wiec `pack_hash` (ryzyko R9) | `requirements.txt`, `pyproject.toml`, `.now/CONTRACT.md` |
| `core.autocrlf=true` w repo | bez `normalize_source` na brzegu `pack_hash` rozjezdza sie miedzy systemami | `tests/test_determinism.py` |

## Znane luki

| Luka | Skutek | Kiedy rozstrzygnac |
|---|---|---|
| `LANGS` nie ma gramatyki dla `.ps1` — w rootach lezy **26** takich plikow | ACAE jest slepy na PowerShell; wypada i z baseline'u, i z packa, wiec bramka M1 pozostaje uczciwa, ale pokrycie repo jest niepelne | otwarte |
| ~~M0 i M1 moga sie rozjechac w regule wyznaczania zakresu~~ | **ZAMKNIETE w M1.** Oba licza 169 plikow: prune katalogow, submoduly, `git check-ignore`, rozmiar, `LANGS` — w tej samej kolejnosci | — |
| `manifest["root"]` to nazwa katalogu | ten sam kod spakowany z katalogu o innej nazwie da inny `pack_hash` | przed M3, jesli pack ma byc porownywany miedzy klonami o roznych nazwach |
