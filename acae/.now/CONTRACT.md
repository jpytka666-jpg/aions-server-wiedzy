# CONTRACT — acae
Mode: FULL

## Goal
Spakowac to repo w jeden deterministyczny artefakt, w ktorym zamiast cial funkcji stoja
sygnatury, zeby wprowadzenie modelu w kod kosztowalo ulamek dzisiejszego kontekstu.
M0 dostarczyl liczbe, wzgledem ktorej kolejne milestone'y sa rozstrzygalne. M1 dostarcza
pack, ktory te liczbe bije o rzad wielkosci.

## Done means
- [x] `../venv/Scripts/python.exe -m pip show tiktoken tree-sitter tree-sitter-language-pack` exits 0 — 0.13.0 / 0.26.0 / 1.14.3
- [x] `../venv/Scripts/python.exe scripts/measure_baseline.py --out _baseline/run1.json` exits 0
- [x] `diff _baseline/run1.json _baseline/run2.json` exits 0 — dwa uruchomienia identyczne co do bajta
- [x] `_baseline/baseline_2e2e260.json` istnieje, zawiera `b_ceiling` oraz 10 wartosci `b_query`
- [x] `tests/queries.json` zamrozony — 10 zapytan, `frozen_at_head` wpisany
- [x] `python -m acae pack --root . --budget 174883` exits 0 — 36492 tokenow, 20,9% budzetu
- [x] `diff _out/p1/content.txt _out/p2/content.txt` exits 0 — pack identyczny co do bajta
- [x] `python -m pytest` exits 0 — 51 testow, w tym cztery testy determinizmu
- [x] rdzen przechodzi testy na Readerze w pamieci, bez pliku i bez serwera (`tests/test_core_pure.py`)
- [x] podlozony klucz konczy w `skipped[]` z `reason: secret`, a jego tresc nie trafia do manifestu
- [x] pack calego zakresu ponizej 60 s — zmierzone 9,4 s na przebieg
- [x] `python -m acae pack --root .` dziala bez uruchomionego serwera MCP
- [x] `python scripts/measure_m2.py` exits 0 — **10/10** zapytan taniej niz `B_query(q)` przy wymaganych 8
- [x] wycinki mieszcza sie w 2,7-7,4% kosztu dzisiejszego Grep+Read (`_baseline/m2_c8344eb.json`)
- [x] `diff _out/m2_run1.json _out/m2_run2.json` exits 0 — pomiar M2 deterministyczny
- [x] `python -m acae ask --query "..."` zwraca wycinek szkieletu plus ciala symboli
- [x] SZLIFOWANIE: pytanie **9490 ms -> ~1250 ms** (cieple), pack **9581 -> 3354 ms**.
      Przyczyna byla jedna linijka: `rglob` wchodzil do `venv`/`node_modules` i wyliczal
      dziesiatki tysiecy plikow, zeby je odrzucic. Plus cache outline'ow i sekretow
      (`parsecache.py`). `pack_hash` NIEZMIENIONY, 225 testow.
- [x] UZYTECZNOSC zmierzona na pytaniach zadanych po ludzku (306 pytan, zbior `wide`):
      `recall@10` **62,0%**, `recall@25` 76,7%, `MRR` 0,451, `neg/poz` 74,3%.
      Samo szukanie po slowach: 25,1%. **Wynik zawyzony** (pytania z opisow) —
      sluzy do znajdowania dziur, NIE do porownan z `dev`/`heldout`.
- [x] JEZYK: narzedzie dziala po angielsku. Te same pytania po polsku: `recall@10` 20,0%,
      po angielsku **70,0%**. Warunek uzycia, nie wada do naprawy — model wolajacy
      narzedzie tlumaczy za darmo.
- [ ] M1-F: integracja z MCP AIONS — **PRZEDEFINIOWANA 2026-08-16**. Nie osobny serwer
      (decyzja Marcina: druga instalacja, drugi punkt awarii, sztuczna sciana wobec CBMS).
      Zakres: **`acae_ask`** jako glowne narzedzie, nie `acae_pack`. Do rozstrzygniecia
      PRZED kodem: (a) jak `project_scan_*` trzyma stan zadania, `server.py:957-1049`;
      (b) `server.py` LEZY W PACKU, wiec jego edycja zmienia `pack_hash` i uniewaznia
      korpus opisow — przemrozic korpus czy przypiac pomiary do `6442322d`;
      (c) zapisac tlumaczenie na angielski jako warunek uzycia.
- [x] M3: `python -m pytest tests/test_store.py` exits 0 — 16 testow, niezmienniki I2/I5/I6/I7/I8/I9 i test C4
- [x] M3: `store.py` nie importuje `aions_core`, `cbms` ani `chroma` — sprawdzane przez AST, nie przez grep po tekscie
- [x] M4: zbior testowy ISTNIEJE i jest zamrozony — `tests/heldout_questions.json`, 14 pytan,
      `blake2b256:e5d8e5b4...`, NIETKNIETY. Zbior roboczy osobno: `tests/dev_questions.json` (30+/6-)
- [x] M4-M7: dziewiec mechanizmow zmierzonych i ODRZUCONYCH, kazdy wobec kryterium zapisanego
      przed jego pomiarem — BM25F, PRF stosunek, PRF+LLR, proza repo, graf Suade, docstringi
      zewnetrzne, codebook, scope gate, embedding statyczny (3 warianty). Tabela w STATE.md i TERMS.md
- [x] M8: `_desc/descriptions.json` — 169 opisow po ludzku, pelne pokrycie packa,
      `blake2b256:cc54efc7d4d27f1917bf46dbb966288b4c89cee1d5c5ae515d54980b4e5319aa`, ZAMROZONY
- [x] M8: `python scripts/measure_m4.py --variant desc` exits 0 — recall@10 26,6% · recall@25 46,6%
      · MRR 0,156 · neg/poz 25,0%. **ODRZUCONY** wobec kryterium (2 z 3 warunkow niespelnione)
- [x] M8: warunek diagnostyczny — **11 z 11** pytan grupy zerowej ma teraz wynik NIEZEROWY
      (przewidywane >= 7). Zero z nich nie siega top-25, mediana rangi 200 z ~1372
- [x] M8: `python -m pytest` exits 0 — **215 testow**; `rank_all` z pusta mapa opisow odtwarza
      `retrieve.select` bit w bit na 30 pytaniach roboczych (zero rozjazdow)

## Constraints
Root: E:\server wiedzy (istniejace repo, rozszerzane a nie forkowane)
Interpreter: E:\server wiedzy\venv\Scripts\python.exe — Python 3.11.9
Piny determinizmu: tree-sitter==0.26.0 · tree-sitter-language-pack==1.14.3 · tiktoken==0.13.0
  Zmiana wersji gramatyki zmienia outline, wiec zmienia pack_hash miedzy maszynami (ryzyko R9).
Doinstalowane w M0/M1: tiktoken, pytest, wheel, oraz `pip install -e ./acae` (editable).
  Rollback: `pip uninstall acae pytest wheel tiktoken`. Instalacja szla z TMPDIR na E:,
  bo na C: bylo malo miejsca; cache pipa i tak lezy poza C:.
Reads: aions_core/server/ts_symbols.py — TYLKO import (LANGS, SymbolIndex, _walk).
  Plik nie jest ruszany. Regula ADDITIVE ONLY. Zaleznosc od prywatnej `_walk` jest
  swiadoma i opisana w TERMS.md (decyzja M1-b) — `tests/test_symbols.py` ja pilnuje.
Touches: nic poza acae/ przez caly M0 i M1. Pierwsza edycja istniejacego pliku AIONS
  nastapi dopiero w M1-F i bedzie ograniczona do dwoch dekoratorow w server.py.
Sciezki: zadnej absolutnej w .py/.toml — guard_write.py blokuje. Rooty sa wzgledne wobec repo.
Konce linii: acae/.gitattributes wymusza LF w calym poddrzewie, bo repo ma core.autocrlf=true.
Zakres: 169 plikow o rozszerzeniu z LANGS, po odjeciu submodulow, .gitignore i przycietych katalogow.
  Ta sama regula w M0 i M1 — inaczej bramka „<= 0,5 x B_ceiling" porownywalaby rozne zbiory.
Baseline przypiety do: 2e2e260 (2026-08-11T05:26:41+01:00)
  result_hash blake2b256:89766585a330aa72bc57dda154ad4cc602bb03d65e23fa57bb8522d183db5641
Pack M1: pack_hash blake2b256:6442322d5d5a011411b7cdb1b50e1fa4673d2b3984399b2dd8c9d02af2bf72db
  169 plikow · 1598 symboli · 869 pominietych · 36492 tokeny

## Out of scope
- Jakikolwiek kontakt z aions_core/memory/ — magazyn ACAE bedzie wlasny (acae/store/).
  To jest operacyjna tresc „zeby sie kociol nie robil z innymi blokami".
- Zwracanie tresci packa przez MCP. Narzedzie zwraca sciezke. Transport offloaduje wszystko
  powyzej progu — `fast_search` zwrocil `OFF_7abfddf1` zamiast wyniku. Plik na dysku nie wygasa, ref OFF_* tak.
- Submodul tools/ChromaFlowStudio — osobne repo, brak .gitmodules, 13798 z 13828 plikow .py to venv.
- PowerShell (.ps1, 26 plikow w rootach) — brak gramatyki w LANGS.
- Migracja czegokolwiek istniejacego. TERMS.md powstal na zielonym polu.

## Open questions
- Jak `project_scan_*` trzyma stan zadania (pamiec / plik / SQLite)? Do przeczytania w server.py:957-1049
  jako pierwszy krok M1-F. Decyduje o tym, czy `acae_pack_status` przezyje restart serwera.
- Czy `beforeWrite`/`afterWrite` w .claude/settings.json:75-102 w ogole sie uruchamiaja? Nazwy nie pasuja
  do schematu PreToolUse/Stop. Nie zakladac, ze py_compile odpala automatycznie.
- Czy `.ps1` ma dostac gramatyke, czy zostac trwale poza zakresem packa.
- Czy `manifest["root"]` ma zostac nazwa katalogu. Dzis ten sam kod spakowany z klonu
  o innej nazwie da inny pack_hash. Bez znaczenia dopoki jest jeden klon.
