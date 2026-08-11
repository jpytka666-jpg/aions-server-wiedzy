# STATE — acae

## 2026-08-11T05:28 — M0 zamkniety, baseline zmierzony i deterministyczny
Done: powstal modul `acae/` — `config/acae.toml` (rooty wzgledne), `requirements.txt` (piny R9),
`tests/queries.json` (10 zamrozonych zapytan), `scripts/measure_baseline.py`, `TERMS.md`,
`.now/CONTRACT.md`, `.now/STATE.md`. Do venv 3.11.9 doinstalowany `tiktoken==0.13.0` —
jedyna mutacja srodowiska w M0, rollback `pip uninstall tiktoken`.
`LANGS` jest **importowane** z `aions_core/server/ts_symbols.py`, nie kopiowane: zakres baseline'u
musi byc tym samym zbiorem, ktory spakuje M1, inaczej bramka „<= 0,5 x B_ceiling" porownuje
polowe jednej rzeczy z caloscia innej.

Proven:
- `../venv/Scripts/python.exe scripts/measure_baseline.py --out _baseline/run1.json` -> exit 0
- `diff _baseline/run1.json _baseline/run2.json` -> exit 0, zero roznic, oba po 12556 bajtow
- trzeci przebieg (`_baseline/baseline_2e2e260.json`) bajt w bajt identyczny z run1.json
- `result_hash` = blake2b256:89766585a330aa72bc57dda154ad4cc602bb03d65e23fa57bb8522d183db5641
- `B_ceiling` = 349766 tokenow w 169 plikach -> bramka M1: `content.txt` <= 174883 tokenow
- `B_query` od 25237 (q03-tree-sitter) do 52406 (q10-hooks), suma 437697
- kontrola zakresu: niezalezny `find` daje 171 plikow, skrypt bierze 169; roznica to dokladnie
  dwa pliki wykluczone przez .gitignore (`aions_core/memory/blends/blend_lib.py`,
  `mcpServers/.../backups/server_backup_20260128_172535.py`). Zero rozjazdu.

Next: M1 — `acae/src/acae/` (canon, ports, symbols, secrets, core, pack, cli). Wejscie w M1 zaczyna
sie od uzgodnienia reguly wyznaczania zakresu w porcie Locator z ta, ktorej uzyl M0.

Uwaga: suma `B_query` (437697) jest wieksza od `B_ceiling` (349766) i tak ma byc — zapytania
nachodza na siebie, ten sam plik wpada do top-5 kilku z nich. To dwie rozne miary, nie skladowe.

## Gotcha — checkpoint.py nie rozroznia „istnial przed sesja" od „powstal przed chwila"
Plan ostrzegal (R8), zeby M0 tworzyl wylacznie NOWE pliki, bo edycja istniejacego robi
`git add -A` + commit calego drzewa. Pilnowalem tego przy tworzeniu i przegapilem przy
poprawianiu: `measure_baseline.py` byl trzykrotnie edytowany po utworzeniu, a dla hooka
plik lezacy na dysku jest po prostu plikiem istniejacym. Pierwszy `Edit` wciagnal 44 brudne
pliki repo w commit `f57cd5c` (52 pliki, 14766 insertions) pod komunikatem
„checkpoint: before edit of measure_baseline.py". Powstalo 5 takich commitow, HEAD przeszedl
z `06fdfe2` na `2e2e260`.

Tresc plikow nie ucierpiala — commit nie zmienia working tree, zadna z 44 zmian nie zniknela.
Decyzja Marcina: historie zostawiamy, baseline przypiety do `2e2e260`.

Regula na przyszlosc, ostrzejsza niz w planie: **zadnej edycji pliku, ktory juz lezy na dysku**,
niezaleznie od tego, kto i kiedy go tam polozyl. Nowy plik pisz raz, w calosci, poprawnie.

## Gotcha — git check-ignore wywraca sie na submodulach
`git check-ignore --stdin -z` zwraca 128 z `fatal: Pathspec '...' is in submodule` dla
kazdej sciezki wewnatrz submodulu. Wykrywanie submodulow idzie po `git ls-files --stage`
i trybie `160000` (gitlink), nie po `.gitmodules` — tego pliku w repo NIE MA, mimo ze
`tools/ChromaFlowStudio` jest w indeksie jako submodul. Wpis-sierota: git wie, ze tam jest
cudze repo, ale nie wie, skad je wziac.
