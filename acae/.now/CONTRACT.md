# CONTRACT — acae
Mode: FULL

## Goal
Spakowac to repo w jeden deterministyczny artefakt, w ktorym zamiast cial funkcji stoja
sygnatury, zeby wprowadzenie modelu w kod kosztowalo ulamek dzisiejszego kontekstu.
M0 dostarcza liczbe, wzgledem ktorej kolejne milestone'y sa rozstrzygalne: bez `B_ceiling`
bramka „redukcja o polowe" jest kwestia wiary.

## Done means
- [x] `../venv/Scripts/python.exe -m pip show tiktoken tree-sitter tree-sitter-language-pack` exits 0 — 0.13.0 / 0.26.0 / 1.14.3
- [x] `../venv/Scripts/python.exe scripts/measure_baseline.py --out _baseline/run1.json` exits 0
- [x] `diff _baseline/run1.json _baseline/run2.json` exits 0 — dwa uruchomienia identyczne co do bajta
- [x] `_baseline/baseline_2e2e260.json` istnieje, zawiera `b_ceiling` oraz 10 wartosci `b_query`
- [x] `tests/queries.json` zamrozony — 10 zapytan, `frozen_at_head` wpisany
- [ ] M1: `python -m acae pack --root .` daje `content.txt` <= 174883 tokenow
- [ ] M1: cztery testy determinizmu (powtorzenie, odwrocona kolejnosc FS, `touch`, inne cwd) — ten sam `pack_hash`

## Constraints
Root: E:\server wiedzy (istniejace repo, rozszerzane a nie forkowane)
Interpreter: E:\server wiedzy\venv\Scripts\python.exe — Python 3.11.9
Piny determinizmu: tree-sitter==0.26.0 · tree-sitter-language-pack==1.14.3 · tiktoken==0.13.0
  Zmiana wersji gramatyki zmienia outline, wiec zmienia pack_hash miedzy maszynami (ryzyko R9).
Reads: aions_core/server/ts_symbols.py — TYLKO import (LANGS, SymbolIndex.from_file, outline, get).
  Plik nie jest ruszany. Regula ADDITIVE ONLY.
Touches: nic poza acae/ do konca M1. Pierwsza i jedyna edycja istniejacego pliku to M1-F.
Sciezki: zadnej absolutnej w .py/.toml — guard_write.py blokuje. Rooty sa wzgledne wobec repo.
Zakres pomiaru: 169 plikow o rozszerzeniu z LANGS, po odjeciu .gitignore i submodulow.
Baseline przypiety do: 2e2e260 (2026-08-11T05:26:41+01:00)
  result_hash blake2b256:89766585a330aa72bc57dda154ad4cc602bb03d65e23fa57bb8522d183db5641

## Out of scope
- Jakikolwiek kontakt z aions_core/memory/ — magazyn ACAE bedzie wlasny (acae/store/).
  To jest operacyjna tresc „zeby sie kociol nie robil z innymi blokami".
- Zwracanie tresci packa przez MCP. Narzedzie zwraca sciezke. Transport offloaduje wszystko
  powyzej progu — `fast_search` zwrocil `OFF_7abfddf1` zamiast wyniku. Plik na dysku nie wygasa, ref OFF_* tak.
- Submodul tools/ChromaFlowStudio — osobne repo, brak .gitmodules, 13798 z 13828 plikow .py to venv.
- PowerShell (.ps1, 26 plikow w rootach) — brak gramatyki w LANGS. Do rozstrzygniecia w M1.
- Migracja czegokolwiek istniejacego. TERMS.md powstaje na zielonym polu, w repo nie bylo go wczesniej.

## Open questions
- Jak `project_scan_*` trzyma stan zadania (pamiec / plik / SQLite)? Do przeczytania w server.py:957-1049
  jako pierwszy krok M1-F. Decyduje o tym, czy `acae_pack_status` przezyje restart serwera.
- Czy `beforeWrite`/`afterWrite` w .claude/settings.json:75-102 w ogole sie uruchamiaja? Nazwy nie pasuja
  do schematu PreToolUse/Stop. Nie zakladac, ze py_compile odpala automatycznie.
- Jezyk komunikatow commitow: historia repo jest po polsku, globalny CLAUDE.md kaze po angielsku.
  Nierozstrzygniete — ACAE nie ma jeszcze wlasnego commita.
- Czy `.ps1` ma dostac gramatyke w M1, czy zostac trwale poza zakresem packa.
