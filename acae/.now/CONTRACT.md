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
- [ ] M1-F: dwa narzedzia MCP (`acae_pack`, `acae_pack_status`) — NIE ROZPOCZETE
- [ ] M2: dla >=8 z 10 zapytan wycinek outline + drill taniej niz `B_query(q)`

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
