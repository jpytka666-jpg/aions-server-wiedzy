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
| **M3-a** | bloby jako kolumna `BLOB` w SQLite, **nie** osobny katalog plikow | PLAN v2 zakladal „SQLite + blobbing", czyli dwa silniki. ADR-002 §5.4 ostrzega, ze silniki bez wspolnej transakcji wymagaja dwufazowego zapisu albo jednego magazynu, a I4 zada atomowej widocznosci. Osobny katalog obok bazy to podrecznikowy dual-write |
| **M3-b** | skala `trust_tier` = `T0 > T1 > T2 > T3` | **To jest WYBOR ACAE, nie cytat.** ADR-002 nie definiuje wartosci — podaje tylko przyklady `T1` i `T3` oraz to, ze tiery sa uporzadkowane. Plan przypisywal dokumentowi ksztalt `{source_uri, job_id, tool, trust_tier}`, ktorego tam nie ma; nazwy podpol tez sa wyborem ACAE |
| **M3-c** | czas wstrzykiwany przez `observed_at`, nigdy brany w srodku | bez tego `id` bloku zalezy od zegara i testy przestaja byc powtarzalne. Domyslnie czas systemowy, ale zawsze na brzegu wywolania |
| **M3-d** | `forget` nie usuwa tresci fizycznie | I8 gwarantuje tombstone i wpis w journalu, nie skasowanie bajtow. Nie obiecujemy wiecej niz kontrakt |

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

## Zmierzone i odrzucone

Moduly, ktore ZOSTAJA w repo, ale **nie sa podpiete**. Wynik negatywny z dzialajaca
implementacja da sie zmierzyc ponownie; wynik negatywny bez implementacji jest opinia.
Tabela istnieje po to, zeby nikt — lacznie ze mna za miesiac — nie podpial ich ponownie,
nie wiedzac, ze juz przegraly.

Kryterium przyjecia bylo to samo dla wszystkich osmiu, ustalone przed pierwszym pomiarem:
`recall@10` >= **34,6%** ORAZ `MRR` >= **0,172** ORAZ `neg/poz` <= **85,2%**.
Baseline: recall@10 **26,6%**, recall@25 **36,6%**, MRR **0,172**, neg/poz **85,2%**.
Wszystkie liczby ze zbioru roboczego 30+/6-; held-out **nietkniety**.

| Modul (etap) | recall@10 | recall@25 | MRR | neg/poz | Na czym poleglo |
|---|---|---|---|---|---|
| `bm25f.py` (M4.1) | 23,3% | 33,3% | 0,156 | **97,0%** | wszystko naraz; implementacja poprawna (zapytanie z doslowna nazwa trafia #1), wiec to wynik, nie blad |
| `expand.py` (M4.2, PRF okno w kodzie) | **30,0%** | 40,0% | **0,139** | 80,7% | recall w gore, MRR w dol |
| `expand.py` (M4.2b, LLR Dunninga) | **33,3%** | 36,6% | **0,153** | 80,4% | najlepszy recall@10 z osmiu, wciaz ponizej progu, MRR nadal zbity |
| `expand.py` (M4.3, most z prozy) | 26,6% | 36,6% | 0,172 | 84,9% | zero ruchu — proza nie wnosi terminow, ktorych ranking uzyje |
| `graph.py` (M4.4, propagacja po grafie) | 26,6% | **40,0%** | 0,172 | 85,2% | najlepszy recall@25 z osmiu, ale top-10 bez zmian |
| (M4.6, korpus zewnetrzny) | 20,0% | 36,6% | 0,169 | 86,7% | najgorszy recall@10; obcy slownik szkodzi |
| `concepts.py` (M5, codebook reczny) | 26,6% | 33,3% | 0,163 | 86,8% | wiedza jawna nie pomogla bardziej niz statystyka |
| `scope.py` (M6, bramka zakresowa) | 23,3% | 33,3% | **0,138** | 88,0% | bramka **nie bramkowala** — mediana 140 ze 169 plikow; patrz STATE.md 2026-08-12T03:10 |

**Warunek ponownego rozpatrzenia — wspolny:** tylko wobec NOWEJ prerejestracji i tylko
jesli zmieni sie inna czesc pipeline'u. Sam fakt, ze „tym razem lepiej dostroje", nie jest
warunkiem — to jest definicja przeuczenia na 30 pytaniach.

**Wyjatek — `scope.py` (M6).** Jako jedyny nie zostal falsyfikowany merytorycznie: pomiar
pokazal wade konstrukcyjna (punktacja routingu nie normalizowana przez rozmiar zakresu,
spojne skladowe grafu zlepione w jedna kluche na 139 plikow), przez ktora dzwignia nie
zostala pociagnieta. Zdanie „ograniczanie przestrzeni nie dziala" **nie ma pokrycia
w zadnym pomiarze**. Wady sa przypiete testami `test_wada_*` w `tests/test_scope.py`.

### Dwa wnioski, ktore te osiem pomiarow uprawnia

1. **Fundament nie byl waskim gardlem** (M4.1). Ranker ad-hoc i BM25F z dwudziestoma laty
   teorii za soba daja ~25% `recall@10` na pytaniach opisowych. Waskim gardlem jest brak
   mostu slownikowego.
2. **Kazdy mechanizm, ktory DODAJE terminy, kupuje recall za cene MRR.** Dwa najlepsze
   `recall@10` (30,0% i 33,3%) to oba warianty PRF — i oba maja najgorsze MRR (0,139
   i 0,153). Dodany termin sciaga symbole pasujace tylko do niego i te wypychaja wlasciwa
   odpowiedz w dol. To nie jest wada implementacji, to powtorzylo sie siedem razy.

## Znane luki

| Luka | Skutek | Kiedy rozstrzygnac |
|---|---|---|
| `LANGS` nie ma gramatyki dla `.ps1` — w rootach lezy **26** takich plikow | ACAE jest slepy na PowerShell; wypada i z baseline'u, i z packa, wiec bramka pozostaje uczciwa, ale pokrycie repo jest niepelne | otwarte |
| ranking jest **wylacznie leksykalny** | pytanie zadane slowami, ktorych w kodzie nie ma (synonim, polski termin, opis zamiast nazwy), nie znajdzie niczego. Zamrozone zapytania sa po angielsku i uzywaja slownictwa z kodu, wiec bramka M2 tej slabosci NIE mierzy | przed uznaniem ACAE za gotowe do codziennego uzycia |
| `manifest["root"]` to nazwa katalogu | ten sam kod spakowany z katalogu o innej nazwie da inny `pack_hash` | przed M3, jesli pack ma byc porownywany miedzy klonami |
| ~~M0 i M1 moga sie rozjechac w regule wyznaczania zakresu~~ | **ZAMKNIETE.** Oba licza 169 plikow ta sama sciezka kodu (`collect_entries`) | — |
