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

## 2026-08-11T06:05 — M1 zamkniety, pack outline deterministyczny
Done: `acae/src/acae/` — canon, ports, symbols, secrets, core, pack, cli, __main__.
Rdzen (`core.py`) nie dotyka dysku: cale I/O siedzi za trzema protokolami z `ports.py`,
a adaptery dyskowe zyja w `pack.py`. Pakiet zainstalowany editable (`pip install -e ./acae`),
wiec `python -m acae pack --root .` dziala z korzenia repo dokladnie tak, jak zaklada §8 planu.
Doinstalowane: pytest, wheel. TMPDIR ustawiony na E: na czas instalacji, bo na C: bylo malo miejsca.

Trzy rzeczy, ktore odbiegly od PLAN v2 i sa opisane w TERMS.md jako decyzje M1-a..M1-d:
hash liczony z bajtow znormalizowanych zamiast doslownie surowych; `symbols.py` sklada
`SymbolIndex` z bajtow przez prywatna `_walk`, bo `from_file()` sam otwiera plik i lamalby
bramke „rdzen bez dysku"; liczba tokenow nie wchodzi do manifestu, zeby `pack_hash` nie
zalezal od wersji tiktokena.

Proven:
- `python -m pytest` -> exit 0, **51 testow**, 2,79 s
- `python -m acae pack --root . --budget 174883` -> exit 0, **36492 tokeny** wobec budzetu 174883
- dwa przebiegi -> `diff content.txt` i `diff manifest.json` exit 0, ten sam
  `pack_hash blake2b256:6442322d5d5a011411b7cdb1b50e1fa4673d2b3984399b2dd8c9d02af2bf72db`
- 169 plikow, 1598 symboli, 869 pominietych — zakres identyczny z M0, wiec bramka jest porownywalna
- czas: 9,4 s na przebieg, bramka byla 60 s
- cztery testy determinizmu zielone: powtorzenie, Locator zwracajacy liste odwrocona,
  zmiana mtime, inny katalog roboczy. Piaty dolozony: podmiana koncow linii na dysku
- redukcja wobec B_ceiling: 349766 -> 36492, czyli **10,4% sufitu** przy bramce 50%

Next: M2 (drill) albo M1-F (dwa narzedzia MCP). M1-F wymaga najpierw przeczytania
`server.py:957-1049`, bo mechanizm trzymania stanu zadania jest nadal nieznany.

## Gotcha — core.autocrlf=true jest cichym wrogiem determinizmu
Git w tym repo konwertuje konce linii przy kazdym `add` („LF will be replaced by CRLF").
Dla ACAE to nie kosmetyka: `content_hash` bierze bajty, wiec ten sam commit dalby inny
hash na Windowsie i na Linuksie, a `pack_hash` przestalby byc porownywalny miedzy maszynami.
Dwa zabezpieczenia: `acae/.gitattributes` wymusza LF w calym poddrzewie, a `canon.normalize_source`
sprowadza CRLF/CR do LF i scina BOM na brzegu, w porcie Reader. Kolejnosc podmian ma znaczenie —
najpierw CRLF, potem samotne CR, inaczej CRLF rozpadlby sie na dwie linie.
Pilnuje tego `test_konce_linii_na_dysku_nie_zmieniaja_pack_hash`.

## Gotcha — `pip install -e` bez `wheel` przy --no-build-isolation
Editable install padal na `error: invalid command 'bdist_wheel'`. Przyczyna nie jest
w pyproject.toml, tylko w tym, ze `--no-build-isolation` kaze setuptools uzyc pakietow
z venv, a `wheel` tam nie bylo. Instalacja `wheel` rozwiazala sprawe. Bez `--no-build-isolation`
pip zbudowalby tymczasowe srodowisko — szybciej, ale z pobieraniem i z zapisem do TEMP.

## Nie-gotcha, warta zapisania, zeby nikt sie nie przestraszyl
Katalog projektu `acae/` w korzeniu repo wyglada jak pakiet przestrzeni nazw i mozna sie
obawiac, ze przesloni zainstalowany pakiet `acae` przy `python -m acae` z korzenia repo.
Nie przeslania: editable install rejestruje finder w `sys.meta_path`, a te maja pierwszenstwo
przed wyszukiwaniem po `sys.path`. Sprawdzone: `import acae` z korzenia repo wskazuje
na `acae/src/acae/__init__.py`.

## 2026-08-11T07:10 — M2 zamkniety, outline-then-drill 10/10
Done: `src/acae/retrieve.py` — ranking symboli pod zapytanie, wycinek szkieletu, drill cial.
Nowa komenda `acae ask --query "..." --drill N --outline-limit M`.
`scripts/measure_m2.py` liczy bramke D4 na dziesieciu zamrozonych zapytaniach.
Z `core.py` wydzielone `collect_entries`, z `symbols.py` — `index_from_bytes` i `body_of`,
zeby M1 i M2 liczyly na TYM SAMYM zbiorze plikow i dotykaly prywatnej `_walk` w jednym miejscu.
`pack_hash` po obu refaktorach niezmieniony — dowod, ze przenoszenie logiki nic nie zmienilo.

Proven:
- `python scripts/measure_m2.py` -> exit 0, **10/10** przy wymaganych 8
- wycinki: 1174-3428 tokenow wobec `B_query` 25237-52406, czyli **2,7-7,4% kosztu**
- `diff _out/m2_run1.json _out/m2_run2.json` -> exit 0, pomiar deterministyczny
- `python -m pytest` -> exit 0, **67 testow**
- baseline z M0 nadal wazny przy przesunietym HEAD: `B_ceiling` 349766 i wszystkie `B_query`
  bit w bit takie same, bo `acae/` nie lezy w rootach z configu. Porownanie jest uczciwe.

Next: M1-F (dwa narzedzia MCP, wymaga dotkniecia server.py) albo M3 (magazyn `acae/store/`).

## Gotcha — zielona bramka nie znaczy dzialajaca funkcja
Bramka M2 mierzy KOSZT, nie UZYTECZNOSC. Przeszla 10/10 zanim ranking w ogole trafial
w odpowiedz. Sprawdzenie recznie, na pytaniu „how is provenance recorded on memory writes",
pokazalo ze wycinek podaje `CBMSMemory` i `MemoryGraph`, a MILCZY o `provenance()`
i `with_provenance()` — mimo ze oba sa w packu (content.txt:1442-1443).

Przyczyna: kazdy termin wazyl tyle samo. `CBMSMemory` dostawal 6 pkt za czeste „memory"
(nazwa + sygnatura + sciezka), `provenance()` tylko 5 za rzadkie „provenance"
(nazwa + sygnatura, bo sciezka to server.py). Czyli tlo bilo odpowiedz.

Naprawione wazeniem rzadkoscia (`term_rarity`, decyzja M2-a). Efekt uboczny: wycinki
ZMALALY, bo mniej nietrafionych symboli wchodzi do szkieletu — q10-hooks 4095 -> 2362.
Lekcja: gdybym oddal M2 po samym odczytaniu bramki, oddalbym tanszy sposob na nietrafianie.

## Gotcha — checkpoint sprzata przy KAZDEJ edycji istniejacego pliku
Regula z M0 („tylko nowe pliki") nie skaluje sie na M1/M2, bo wlasny kod trzeba poprawiac.
Dzialajacy wzorzec: commituj `acae/` do czysta PRZED kazda seria edycji. Wtedy
`git status --porcelain` pokazuje juz tylko brudny submodul, `git add -A` nie ma czego
zestage'owac, `git commit` konczy sie „nothing to commit" i hook jest faktycznym no-opem.
Gdy drzewo jest brudne, kazda edycja produkuje commit „checkpoint: before edit of X"
o mylacej etykiecie — nieszkodliwy, bo obejmuje tylko `acae/`, ale zasmieca historie.

## 2026-08-11T08:30 — M3 zamkniety, magazyn blokow
Done: `src/acae/store.py` + `tests/test_store.py`. Jeden silnik SQLite, tresc w kolumnie BLOB.
Niezmienniki ADR-002 §4.2 w postaci wykonywalnej: I2 (rewizja tworzy nowy blok, stary dostaje
`valid_to`), I5 (idempotencja po `content_hash`+`scope`), I6 (prowenancja sumowana), I7
(trust_tier spada do najnizszego ze zrodel), I8 (`forget` = tombstone + journal), I9 (`stats`
liczone skanem), C4 (skasowanie indeksow nie zmienia odpowiedzi).

Proven: `python -m pytest` -> exit 0, **84 testy** (16 nowych).

Odstepstwo od PLAN v2: plan mowil „SQLite + blobbing", czyli dwa silniki. ADR-002 §5.4
zabrania dual-write bez wspolnej transakcji, a I4 zada atomowej widocznosci — wiec bloby
ida do kolumny BLOB. Decyzja M3-a w TERMS.md.

Next: M4. **Blokada: zbior testowy nie istnieje** — agent generujacy 14 pytan opisowych
padl na limicie sesji Anthropic. Bez niego M4 nie ma na czym byc oceniony, a pisanie go
wczesniej znaczy projektowanie pod jedyny przyklad, ktory widzialem (q08/provenance).

## Gotcha — ADR-002 nie mowi tego, co plan mu przypisuje
PLAN v2 podawal prowenancje jako `{source_uri, job_id, tool, trust_tier}` „w ksztalcie
ADR-002 §4.1". W dokumencie tych nazw NIE MA — jest jedno pole `provenance` opisane jako
„zrodlo, job, narzedzie, trust tier", bez nazw podpol i bez typow. Dozwolonych wartosci
`trust_tier` tez nie ma, sa tylko przyklady `T1` i `T3`. Ksztalt uzyty w `store.py` jest
wiec WYBOREM ACAE i tak jest opisany w TERMS.md — to znowu ryzyko R6 (plan cytuje jako
kontrakt cos, co jest interpretacja).

## 2026-08-11T09:15 — zbior testowy M4 ZAMROZONY (przed napisaniem M4)
`acae/tests/heldout_questions.json` — 14 pytan opisowych (q101-q114) z prawda podstawowa.
Wygenerowane przez OSOBNEGO agenta, ktory nie widzial algorytmu ani tej rozmowy i mial
kategoryczny zakaz zagladania do `acae/`. Pytania opisuja zachowanie, nie nazywaja symboli.

**Hasz zamrozony: `blake2b256:e5d8e5b4dc9e3aec6b0e178170564ea7adeaea0d6fa2bd0903b2962f507f3cea`**
(9318 bajtow, 14 pozycji)

Ten wpis powstaje ZANIM istnieje jakikolwiek kod M4. Kolejnosc jest widoczna w historii
gita i to jest cala gwarancja: commit ze zbiorem poprzedza commit z algorytmem.

Weryfikacja strukturalna (skrypt widzial tresc, ja nie):
- 14/14 pozycji ma prawde podstawowa wskazujaca na symbole ISTNIEJACE w packu
- 12/14 czyste w kontroli wycieku; pozostale 2 to falszywy alarm — kontroler rozbil
  `to_dict` na `to`+`dict` i trafil w angielskie „to" w pytaniu. Realnie 14/14.

Regula na czas M4: **nie otwieram tego pliku.** Po ewaluacji wolno mi zmienic diagnoze,
nie wolno stroic wag ani progow — strojenie po odsloniecie zbioru zamienia go z powrotem
w zbior treningowy i cala ta ostroznosc idzie do kosza.

## 2026-08-11T10:40 — PREREJESTRACJA M4.1-M4.5 (przed jakimkolwiek pomiarem)

Marcin postawil warunek: kazdy mechanizm mierzony OSOBNO, zeby bylo wiadomo co faktycznie
placi. To jest ablacja i jest sluszne. Ale piec etapow mierzonych na tym samym zbiorze 14
pytan SPALILOBY ten zbior: kazde spojrzenie na wynik i decyzja „zostawiam/wyrzucam"
przecieka informacje o zbiorze. Po pieciu takich decyzjach holdout jest treningowy, tylko
wolniej — adaptacyjne przeuczenie na holdoucie.

**Trzy zabezpieczenia:**

1. **Zbior ROBOCZY, osobny.** Etapy M4.1-M4.5 mierze na `acae/tests/dev_questions.json`
   (30 pozytywnych + 6 negatywnych, inny agent, ten sam protokol). Zamrozone 14 z
   `heldout_questions.json` zostaje NIETKNIETE i otwierane DOKLADNIE RAZ, na koncu.
2. **Kryteria zapisane TUTAJ, przed pomiarem** — patrz tabela nizej. Wtedy pomiar nie
   wymaga ode mnie osadu, wiec nie przecieka.
3. **Regresja identyczna na kazdym etapie:** pelny pytest zielony · bramka M2 nadal 10/10 ·
   `pack_hash` NIEZMIENIONY. To ostatnie jest twardym strażnikiem — zaden mechanizm M4 nie
   ma prawa ruszyc artefaktu, tylko ranking. Gdyby ruszyl, porownywalnosc z M0/M1/M2 pada.

| etap | co dokłada | KRYTERIUM PRZYJECIA (zapisane przed pomiarem) |
|---|---|---|
| M4.1 BM25F | zamiana ad-hoc wag i `RARITY_CAP` na model z osobna normalizacja per pole | `recall@10` >= obecnego ORAZ `MRR` > obecnego. To wymiana fundamentu, nie funkcja — ma nie pogorszyc niczego |
| M4.2 PRF, okno w kodzie | most z sasiedztwa pozycyjnego w zrodlach | `recall@10` **+8 pkt proc.** ponad M4.1 i kontrole negatywne bez pogorszenia |
| M4.3 most z prozy | commity i `.md` jako drugi korpus | `recall@10` **+5 pkt proc.** PONAD M4.2. Jesli proza nie dokłada nic ponad kod — wypada |
| M4.4 propagacja po grafie | `specificity` + `reinforcement` na `refs` | `MRR` **+0,05** ORAZ `recall@25` bez utraty precyzji na kontrolach negatywnych |
| M4.5 AMAP | rozwijanie skrotow z repo | uruchamiam TYLKO jesli diagnoza M4.1-M4.4 wskaze skroty jako przyczyne chybien |

Kontrola negatywna „bez pogorszenia" znaczy: dla 6 pytan o rzeczy, ktorych w repo NIE MA,
sredni najwyzszy wynik rankingu nie rosnie. Bez tego kryterium „semantic retrieval"
i „rozszerzam agresywnie, wiec cos zawsze trafie" wygladaja identycznie.

Uzasadnienie kolejnosci: BM25F pierwszy, bo obecny scoring PEKL DWA RAZY w jednej sesji
(rowne wagi, potem `RARITY_CAP=64`) — jest wymyslonym od nowa IDF-em bez teorii, wiec
mierzenie czegokolwiek na nim mierzy szum. Graf ostatni, bo ZMIERZONE: propagacja wzmacnia
to co ranker mowi, wiec na zlym rankerze wzmacnia bledy (`DifferentiableMemory/write`
urosl z 873 na 1489).

Stan: `src/acae/expand.py` napisany, ale **NIEPODPIETY** — nie zmienia niczego do M4.2.
Przyjmuje korpus i nazwe reguly jako parametry, wiec M4.2 i M4.3 dadza sie zmierzyc osobno.

## 2026-08-11T11:20 — M4.1 BM25F: ZMIERZONY I ODRZUCONY

Kryterium z prerejestracji: `recall@10 >= obecnego` ORAZ `MRR > obecnego`, kontrole
negatywne bez pogorszenia. Wynik na zbiorze roboczym (30 pozytywnych, 6 negatywnych):

| miara | baseline (M2) | BM25F | werdykt |
|---|---|---|---|
| recall@10 | 26,6% | 23,3% | gorzej |
| recall@25 | 36,6% | 33,3% | gorzej |
| MRR | 0,172 | 0,156 | gorzej |
| negatywy/pozytywy | 85,2% | 97,0% | gorzej |

**ODRZUCONY.** Zgodnie z prerejestracja nie stroje `k1`, `b` ani wag pol — to byloby
strojenie pod pomiar, po ktorym uwierzylbym we wlasny wynik.

Sprawdzone, ze to NIE jest blad implementacji: na zapytaniach z doslowna nazwa BM25F
stawia cel na pierwszym miejscu tak samo jak baseline (`provenance`, `normalize_metadata`,
`_client_identity`). Tokenizacja dziala (`CBMSMemory/get_memory_stats` ->
`cbms|memory|get|memory|stats`), nasycenie dziala, IDF maleje z czestoscia — 12 testow.

**Wniosek wazniejszy niz sam werdykt:** oba rankery daja ~25% recall@10 na pytaniach
opisowych, mimo ze jeden jest ad-hoc, a drugi ma dwadziescia lat teorii. Czyli
**fundament nie byl waskim gardlem**. Gdyby BM25F wygral, uwierzylbym ze problemem bylo
wazenie — a problemem jest brak mostu slownikowego. To przesuwa ciezar dowodu na M4.2/M4.3.

Konsekwencja proceduralna: M4.2 mierzony wobec **baseline (M4.0)**, nie wobec BM25F.
Kryterium bez zmian: `recall@10` **+8 pkt proc.** ponad 26,6%, czyli **>= 34,6%**.

Regresja: 96 testow zielonych, M2 nadal 10/10, `pack_hash` niezmieniony `6442322d...`.
Modul zostaje w repo NIEPODPIETY — wynik negatywny z dzialajaca implementacja da sie
zmierzyc ponownie, gdy zmieni sie reszta pipeline'u. Ale tylko wobec nowej prerejestracji.

## 2026-08-11T12:05 — M4.2 PRF z oknem w kodzie: ZMIERZONY I ODRZUCONY

Kryterium: `recall@10 >= 34,6%` (baseline 26,6% + 8 pkt proc.), kontrole negatywne
bez pogorszenia. Wynik na zbiorze roboczym:

| miara | baseline | M4.2 | werdykt |
|---|---|---|---|
| recall@10 | 26,6% | 30,0% | +3,4 zamiast +8 — **za malo** |
| recall@25 | 36,6% | 40,0% | +3,4 |
| MRR | 0,172 | 0,139 | **gorzej** |
| negatywy/pozytywy | 85,2% | 80,7% | lepiej |

**ODRZUCONY.** Sprzecznosc wewnetrzna jest diagnostyczna: recall rosnie, MRR spada.
Rozszerzenie wciaga poprawne symbole do top-25, ale wpycha je NIZEJ — dokłada trafnych
i szumu jednoczesnie.

**Przyczyna, odczytana z paragonow (po to sa):**
```
file -> sha12       co=3  df=3   ratio=1000 promili
rows -> is_refusal  co=2  df=2   ratio=1000 promili
read -> post_chat   co=2  df=4   ratio= 500 promili
```
Filtr `stosunek >= 250 promili` jest TRYWIALNIE spelniony przy malym `df`. Termin
wystepujacy w calym repo dwa razy, oba razy obok terminu z pytania, dostaje 1000 promili
i przechodzi — mimo ze dowodu nie ma zadnego. `MIN_COOCCURRENCE=2` tego nie broni,
bo to ta sama dwojka. Klasyczny problem malej proby: wysoki stosunek, zerowe wsparcie.

To JEST ta sama klasa bledu co `RARITY_CAP` w M2: statystyka bez progu wsparcia.
Trzeci raz w tym projekcie. Wniosek do zapamietania: **kazda miara oparta na stosunku
potrzebuje osobnego progu na mianownik**, inaczej maly mianownik produkuje pewnosc
z niczego.

Czego NIE robie: nie podnosze `MIN_COOCCURRENCE` ani `MIN_RATIO_PERMILLE`, zeby to
przeszlo. To byloby strojenie po zobaczeniu wyniku — dokladnie to, przed czym chronila
prerejestracja. Ewentualna poprawka wymaga NOWEJ prerejestracji i jest DRUGIM podejsciem,
co samo w sobie oslabia sile dowodu i musi byc odnotowane.

## 2026-08-11T12:20 — PREREJESTRACJA M4.2b (PODEJSCIE #2, przed implementacja)

Marcin zgodzil sie na JEDNO poprawione podejscie. Odnotowuje jawnie: **to jest druga
proba po zobaczeniu wyniku pierwszej i to oslabia sile dowodu.** Trzeciej nie bedzie —
jesli M4.2b przegra, most z okna w kodzie jest odrzucony definitywnie.

**Zmienia sie DOKLADNIE JEDNA RZECZ:** filtr wyboru krawedzi. Wszystko inne zostaje
bez ruchu (`MIN_TERMS_COVERED=2`, `MAX_PER_TERM=3`, `MAX_TOTAL=12`, waga rozszerzenia
1/2, okno 12 linii, ten sam korpus, ten sam ranker bazowy). Jedna zmienna na pomiar,
inaczej nie da sie powiedziec, co zadzialalo.

**Bylo:** `stosunek = co/df >= 250 promili` — trywialnie spelnialny przy df=2.
**Bedzie:** **log-likelihood ratio Dunninga (G^2)** na tablicy 2x2 (term x kandydat).
To jest statystyka zaprojektowana dokladnie pod ten tryb awarii: karze rzadkie zdarzenia
za brak wsparcia, zamiast nagradzac je za wysoki stosunek. Standard w wydobywaniu
kolokacji od 1993 r. wlasnie dlatego, ze surowe proporcje przeuczaja sie na malej probie.

**Prog: `G^2 >= 10.83`.** To NIE jest liczba dobrana, zeby cos przeszlo — to wartosc
krytyczna chi-kwadrat dla 1 stopnia swobody przy p < 0.001. Bierze sie z rozkladu,
nie z danych. Gdybym dobral prog patrzac na wynik, cala ta ostroznosc byla by teatrem.

**KRYTERIUM PRZYJECIA M4.2b (wobec baseline, nie wobec M4.2):**
- `recall@10` >= **34,6%** (26,6% + 8 pkt proc.), ORAZ
- `MRR` >= **0,172** (bez pogorszenia wobec baseline), ORAZ
- `negatywy/pozytywy` <= **85,2%** (bez pogorszenia).

Wszystkie trzy naraz. M4.2 spelnil tylko trzeci i to nie wystarczylo.

**Kontrargument, ktory zapisuje ZANIM zobacze wynik:** „zasada zamiast wymyslu" nie
gwarantuje poprawy — BM25F byl dokladnie takim zabiegiem i przegral. Jesli LLR tez
przegra, wniosek brzmi: problemem nie jest statystyka doboru krawedzi, tylko to,
ze okno pozycyjne w kodzie nie niesie mostu miedzy opisem a nazwa.

## 2026-08-11T12:45 — M4.2b: ZMIERZONY I ODRZUCONY. Most z okna w kodzie zamkniety.

| miara | baseline | M4.2 (stosunek) | M4.2b (LLR) | wymagane | werdykt |
|---|---|---|---|---|---|
| recall@10 | 26,6% | 30,0% | **33,3%** | >= 34,6% | NIE, brakło 1,3 pkt |
| recall@25 | 36,6% | 40,0% | 36,6% | — | — |
| MRR | 0,172 | 0,139 | **0,153** | >= 0,172 | NIE |
| negatywy/pozytywy | 85,2% | 80,7% | **80,4%** | <= 85,2% | TAK |

LLR zrobil to, co mial: dobor krawedzi wyraznie lepszy niz surowy stosunek, `recall@10`
w gore o 3,3 pkt wobec M4.2, kontrola negatywna najlepsza z dotychczasowych. Ale kryterium
wymagalo TRZECH warunkow naraz.

**Nie obnizam progu.** 34,6% ustalilem, gdy nie wiedzialem, ze wynik wyjdzie 33,3%.
Obnizenie go teraz uczyniloby cala prerejestracje teatrem. Zgodnie z zapisem — trzeciej
proby nie ma. **Most z okna pozycyjnego w kodzie: ODRZUCONY DEFINITYWNIE.**

**Obserwacja przekrojowa, wazniejsza od werdyktu:** MRR spadl w OBU podejsciach
(0,139 i 0,153 wobec 0,172). Rozszerzanie zapytania konsekwentnie spycha poprawne symbole
NIZEJ, nawet gdy podnosi recall. To wlasnosc mechanizmu, nie doboru krawedzi: dodane
terminy rozcienczaja sygnal terminow oryginalnych. Hipoteza na przyszlosc, ktorej NIE
testuje teraz (bo to byloby strojenie): waga rozszerzenia 1/2 moze byc za wysoka.

## 2026-08-11T12:50 — PREREJESTRACJA M4.3 (przed pomiarem)

Korpus prozy: komunikaty commitow + akapity `.md`. **Jedno podejscie.** M4.2 odrzucony,
wiec proza jest mierzona SAMODZIELNIE wobec baseline, nie jako dodatek do okna w kodzie.

Zmienia sie DOKLADNIE JEDNA RZECZ wobec M4.2b: korpus. Wszystkie filtry i wagi bez ruchu
(G^2 >= 10.83, pokrycie >= 2, maks 3 na termin, maks 12 razem, waga 1/2, ten sam ranker).

**KRYTERIUM PRZYJECIA — identyczne jak M4.2b, zeby wyniki byly porownywalne:**
- `recall@10` >= **34,6%**, ORAZ
- `MRR` >= **0,172**, ORAZ
- `negatywy/pozytywy` <= **85,2%**.

Zapisuje przewidywanie, zeby nie moc go pozniej przemilczec: w prototypie na jednym
pytaniu proza wypadla LEPIEJ niz okno w kodzie (to ona wyciagnela `with_provenance`
na pierwsze miejsce). Ale prototyp byl wewnatrzprobkowy, wiec ta przeslanka jest slaba.
Jesli proza tez przegra, wniosek brzmi: **deterministyczny most leksykalny nie zamyka
luki miedzy opisem a nazwa** — i to jest wynik wart raportu, a nie porazka wymagajaca
dokladania kolejnych warstw.

## 2026-08-11T13:10 — M4.3 most z prozy: ZMIERZONY I ODRZUCONY

| miara | baseline | M4.3 (proza) | wymagane | werdykt |
|---|---|---|---|---|
| recall@10 | 26,6% | **26,6%** | >= 34,6% | NIE |
| recall@25 | 36,6% | 36,6% | — | bez zmiany |
| MRR | 0,172 | 0,172 | >= 0,172 | TAK (rowno) |
| negatywy/pozytywy | 85,2% | 84,9% | <= 85,2% | TAK |

Liczby IDENTYCZNE z baseline, mimo ze most wyprodukowal **427 terminow** na 36 pytan
(limit 12 na pytanie osiagniety wszedzie). Nie jest to blad — sprawdzone: korpus ma
13 878 dokumentow, 14 116 unikalnych tokenow, `df(machine)=26`, `df(provenance)=13`.

**Diagnoza — druga strona LLR.** Najwyzsze G^2 w prozie maja generyczne pary
z dokumentacji:
```
styling -> conversation  G2=786.8  co=92   df=190
memory  -> facts         G2=639.4  co=141  df=212
chat    -> post          G2=405.3  co=84   df=160
```
G^2 nagradza WYSOKIE WSPARCIE — o to prosilem, zeby odciac mala probe. Ale w prozie
wysokie wsparcie maja slowa czeste i puste. Krawedz `machine -> provenance` (co=2, df=13)
przegrywa z nimi i wypada poza limit trzech na termin. A `conversation`, `facts`, `post`
sa w KODZIE czeste, wiec `term_rarity` daje im niska wage i po podzieleniu przez dwa
nie ruszaja rankingu w ogole.

**LLR naprawil jeden tryb awarii i wprowadzil przeciwny:** przedtem wygrywaly krawedzie
rzadkie bez wsparcia, teraz czeste bez tresci. To nie jest argument za trzecim progiem —
to jest argument, ze pojedyncza statystyka wspolwystepowania nie rozdziela „czeste"
od „istotne" w tym korpusie.

**Ta sama klasa bledu po raz CZWARTY** (rowne wagi -> RARITY_CAP -> stosunek bez wsparcia
-> LLR bez kontroli pospolitosci). Cztery razy w jednym projekcie to nie pech, tylko
sygnal o problemie, a nie o parametrze.

## 2026-08-11T20:30 — M4.4 propagacja po grafie: ZMIERZONY I ODRZUCONY. ABLACJA ZAMKNIETA.

| miara | baseline | M4.4 | wymagane | werdykt |
|---|---|---|---|---|
| recall@10 | 26,6% | 26,6% | — | bez zmiany |
| recall@25 | 36,6% | **40,0%** | >= 36,6% | TAK |
| MRR | 0,172 | 0,172 | >= 0,222 | **NIE** |
| negatywy/pozytywy | 85,2% | 85,2% | <= 85,2% | TAK (rowno) |

Profil jest diagnostyczny: propagacja dokłada trafienia w pasmie 11-25, ale **nie promuje
niczego do pierwszej dziesiatki**. Sasiad trafionego symbolu jest sasiadem, nie odpowiedzia.

Implementacja sprawdzona przed zaufaniem wynikowi: arytmetyka calkowita w promilach,
`NodeKey` zawiera sciezke, laczenie Suade nasycajace, `refs` czytane osobnym przebiegiem
zeby nie dopisac pola do `outline_rows` i nie ruszyc `pack_hash`. 15 testow zielonych,
w tym te, ktore pilnuja sedna: `specificity` karze huby, `reinforcement` nagradza
wielokrotne wskazania, cykle nie zawieszaja.

### PELNA ABLACJA M4 — cztery mechanizmy, cztery odrzucenia

| wariant | recall@10 | recall@25 | MRR | neg/poz |
|---|---|---|---|---|
| baseline (M2) | 26,6% | 36,6% | 0,172 | 85,2% |
| M4.1 BM25F | 23,3% | 33,3% | 0,156 | 97,0% |
| M4.2 PRF stosunek | 30,0% | 40,0% | 0,139 | 80,7% |
| M4.2b PRF + LLR | **33,3%** | 36,6% | 0,153 | **80,4%** |
| M4.3 proza + LLR | 26,6% | 36,6% | 0,172 | 84,9% |
| M4.4 graf Suade | 26,6% | **40,0%** | 0,172 | 85,2% |

**MRR nie wzrosl ANI RAZU.** Zaden z czterech mechanizmow nie postawil poprawnego symbolu
wyzej, niz stawial go goły ranker leksykalny. Trzy podnosily recall kosztem MRR, czwarty
podniosl recall@25 nie ruszajac MRR. To jest jeden i ten sam wynik widziany z czterech stron.

### Wniosek, na ktory pozwalaja te pomiary

Trzy z czterech mechanizmow to warianty **wspolwystepowania slow**, wiec licza sie jako
jeden dowod, nie trzy. Czwarty jest strukturalny i tez nie ruszyl MRR — a to jest wazne,
bo nie zalezy od slow w ogole.

Rozpoznanie CBMS domyka diagnoze: `cbms_search` dziala nie przez semantyke, tylko dlatego,
ze **jego korpus JEST proza w tym samym rejestrze co pytania**, a kod wisi obok jako
`references`. Blok CBMS to opis z doczepionymi sciezkami. W ACAE korpusem sa identyfikatory.
Zadna statystyka nie wyprodukuje wiedzy, ktorej w repo nie ma.

**Problem nie lezy w scorerze. Lezy w tym, ze repo nie zawiera warstwy prozy przypietej
do symboli.** Cztery mechanizmy proboowaly wyliczyc to, co w CBMS jest wpisane recznie.

### Zmierzone poza ablacja (eksploracja, zbior roboczy NIETKNIETY)

Tabela skojarzen identyfikator <-> slowo z 50 663 par (symbol, docstring) ze stdlib
i site-packages: `remove -> pop, clear, clean, strip` dziala swietnie, ale
`machine -> host` NIE POWSTAJE, a `computer` nie daje nic. Przyczyna: stdlib to proza
o strukturach danych, nie o maszynach i infrastrukturze. Mechanizm dziala, brakuje
wlasciwego rozkladu dziedzinowego korpusu.

**Held-out (14 pytan, `blake2b256:e5d8e5b4...`) pozostaje NIETKNIETY.** Nie ma sensu go
otwierac, dopoki nie ma kandydata, ktory przeszedl na zbiorze roboczym.

## 2026-08-11T21:00 — PREREJESTRACJA M4.6: most z ZEWNETRZNEGO korpusu docstringow

**Hipoteza:** brakujaca warstwa skojarzen „identyfikator <-> slowo opisu" nie da sie
wyprowadzic z tego repo (M4.2, M4.3 pokazaly to pomiarem), ale da sie ja wziac
z ZEWNETRZNEGO korpusu par (symbol, docstring). Jesli tak, most powstanie z cudzych
opisow, a wskaze NASZE identyfikatory.

**Korpus:** biblioteka standardowa Pythona + `venv/Lib/site-packages`. Zmierzone:
**50 663 par (symbol, docstring)**, ~3,05 mln slow opisu, 7 099 unikalnych tokenow
identyfikatorow. Lokalny, licencyjnie czysty, bez pobierania czegokolwiek.

**Zmienia sie DOKLADNIE JEDNA RZECZ wobec M4.3: zrodlo korpusu.** Wszystko inne bez ruchu:
`G^2 >= 10.83`, pokrycie LCA >= 2, maks 3 rozszerzenia na termin, maks 12 razem,
waga rozszerzenia 1/2, ten sam ranker bazowy, ten sam `expand()`.
Slownik docelowy to nadal `symbol_vocabulary(entries)` — czyli most moze wskazac
WYLACZNIE identyfikator, ktory naprawde istnieje w naszym packu.

**KRYTERIUM PRZYJECIA — identyczne jak M4.2b i M4.3, zeby wyniki byly porownywalne:**
- `recall@10` >= **34,6%**, ORAZ
- `MRR` >= **0,172**, ORAZ
- `negatywy/pozytywy` <= **85,2%**.
Wszystkie trzy naraz. **Jedno podejscie.**

**PRZEWIDYWANIE ZAPISANE PRZED POMIAREM (zeby nie dalo sie go potem przemilczec):**
spodziewam sie PORAZKI. Eksploracja tej samej tabeli pokazala, ze `remove -> pop, clear,
clean, strip` powstaje swietnie, ale `machine -> host` NIE POWSTAJE, a `computer` nie daje
nic — bo stdlib to proza o strukturach danych, nie o maszynach i infrastrukturze.

**Co z tego wynika dla decyzji o CodeSearchNet:**
- wynik POZYTYWNY -> mechanizm dziala i warto sprawdzic wiekszy korpus o innym rozkladzie,
- wynik NEGATYWNY -> **zamykamy kierunek**. Nie dorabiam teorii, ze „wiekszy korpus by pomogl".
  Jesli 50 tysiecy par z wlasciwym mechanizmem nie ruszy ani jednej z trzech miar, to
  twierdzenie „dwa miliony ruszyloby" bedzie hipoteza bez pokrycia, a nie wnioskiem.

## 2026-08-11T21:25 — M4.6: HIPOTEZA ODRZUCONA. Kierunek zamkniety.

| miara | baseline | M4.6 | wymagane | werdykt |
|---|---|---|---|---|
| recall@10 | 26,6% | **20,0%** | >= 34,6% | NIE |
| recall@25 | 36,6% | 36,6% | — | bez zmiany |
| MRR | 0,172 | 0,169 | >= 0,172 | NIE |
| negatywy/pozytywy | 85,2% | 86,7% | <= 85,2% | NIE |

Wszystkie trzy warunki niespelnione. Zewnetrzny korpus nie tylko nie pomogl —
**pogorszyl `recall@10` o 6,6 punktu**, dajac najgorszy wynik ze wszystkich szesciu
wariantow M4. Przewidywanie zapisane przed pomiarem sie potwierdzilo.

**Zgodnie z prerejestracja kierunek jest ZAMKNIETY.** Bez CodeSearchNet, bez The Stack v2,
bez architektury produkcyjnej dla tego pomyslu. Nie dorabiam teorii, dlaczego wiekszy
korpus by pomogl — pomiar mowi, ze ten mechanizm na tym zadaniu szkodzi.

### Bilans koncowy ablacji M4 — szesc wariantow, szesc odrzucen

| wariant | recall@10 | recall@25 | MRR | neg/poz |
|---|---|---|---|---|
| baseline (M2) | 26,6% | 36,6% | **0,172** | 85,2% |
| M4.1 BM25F | 23,3% | 33,3% | 0,156 | 97,0% |
| M4.2 PRF stosunek | 30,0% | 40,0% | 0,139 | 80,7% |
| M4.2b PRF + LLR | **33,3%** | 36,6% | 0,153 | **80,4%** |
| M4.3 proza repo | 26,6% | 36,6% | 0,172 | 84,9% |
| M4.4 graf Suade | 26,6% | **40,0%** | 0,172 | 85,2% |
| M4.6 docstringi zewnetrzne | 20,0% | 36,6% | 0,169 | 86,7% |

`MRR` nie przekroczyl 0,172 ani razu. Najlepszy `recall@10` (33,3%) nie siegnal progu 34,6%.
Zaden wariant nie spelnil kryterium, ktore bylo zapisane przed jego pomiarem.

Held-out (`blake2b256:e5d8e5b4...`) **NIETKNIETY** — nie ma kandydata do sprawdzenia.

## 2026-08-12T00:40 — PREREJESTRACJA M5: semantyczny codebook (WIEDZA JAWNA, nie statystyka)

**To NIE jest siodmy sposob liczenia podobienstwa.** Szesc poprzednich mechanizmow probowalo
WYLICZYC zwiazek „slowo z pytania -> identyfikator w kodzie" z danych. M5 go **ZAPISUJE**.
Roznica jest zasadnicza: tam gdzie tamte szacowaly, ten stwierdza.

**Skad sie bierze:** `CODEBOOK_CBMS_ES.jsonl` Marcina (457 hasel esperanto -> znak, kompresja).
Lewa kolumna to gotowa lista pojec. Dopisujemy dwie: **formy powierzchniowe** (slowa, ktorymi
czlowiek moze o tym zapytac) i **rdzenie kodu** (tokeny do szukania w identyfikatorach).
Trzecia kolumna — konkretne symbole — liczy sie sama z packa przy kazdym uruchomieniu.

**Uczciwosc konstrukcji:** codebook pisze ze slownictwa KODU i z wiedzy o dziedzinie.
**NIE zagladam do `dev_questions.json`.** Napisanie go pod pytania byloby napisaniem sobie
odpowiedzi. Kolejnosc widoczna w historii gita: prerejestracja, potem codebook, potem pomiar.

**Poprawka jakosci pomiaru** (zgloszona wczesniej jako wada): dopasowanie idzie po TOKENACH
identyfikatora, nie po podciagu. Inaczej `form` trafia w `Performance` i 31 „trafien" jest
zmyslonych. Uzywam `split_identifier` z `bm25f.py` — to narzedzie tokenizujace, NIE ranker
BM25F, ktory zostal odrzucony i pozostaje odrzucony.

**KRYTERIUM PRZYJECIA — identyczne jak M4.2b, M4.3, M4.6, zeby wyniki byly porownywalne:**
- `recall@10` >= **34,6%**, ORAZ
- `MRR` >= **0,172**, ORAZ
- `negatywy/pozytywy` <= **85,2%**.
Wszystkie trzy naraz. **Jedno podejscie.**

**Przewidywanie zapisane przed pomiarem:** tym razem spodziewam sie POPRAWY recall,
bo demonstracja pokazala, ze `maŝino -> host -> _default_host` powstaje natychmiast.
Ale nie mam pewnosci co do `MRR` — wszystkie szesc poprzednich mechanizmow go obnizylo
albo zostawilo bez zmian, a rozszerzanie zapytania rozciencza sygnal terminow oryginalnych.
Jesli `recall@10` przekroczy prog, a `MRR` spadnie — to jest PORAZKA wg kryterium
i tak ja zaraportuje, bez tlumaczenia, ze „prawie sie udalo".

## 2026-08-12T01:15 — M5: ZMIERZONY I ODRZUCONY. Siedem mechanizmow, siedem odrzucen.

| miara | baseline | M5 | wymagane | werdykt |
|---|---|---|---|---|
| recall@10 | 26,6% | 26,6% | >= 34,6% | NIE |
| recall@25 | 36,6% | **33,3%** | — | gorzej |
| MRR | 0,172 | **0,163** | >= 0,172 | NIE |
| negatywy/pozytywy | 85,2% | **86,8%** | <= 85,2% | NIE |

**Moje przewidywanie zapisane przed pomiarem bylo BLEDNE.** Napisalem, ze spodziewam sie
poprawy recall. Nie nastapila. Odnotowuje to, bo prerejestracja dziala w obie strony —
nie sluzy tylko do chwalenia sie trafnymi przeczuciami.

**Diagnoza z paragonow, mocniejsza niz sam werdykt:** codebook dopasowal pojecie
w **26 z 30 pytan**, srednio 2 pojecia na pytanie. Odpalaly sie `server`, `graph`, `error`,
`name`, `file`, `context`, `tool`, `web`, `user`, `machine`. To NIE jest problem pokrycia
slownictwa — mechanizm mial swoja szanse na 87% pytan i jej nie wykorzystal.
Trafienia@10: z dopasowaniem 6/26, bez dopasowania 2/4.

### BILANS: siedem mechanizmow, siedem odrzucen

| wariant | rodzaj | recall@10 | recall@25 | MRR | neg/poz |
|---|---|---|---|---|---|
| baseline (M2) | leksykalny | 26,6% | 36,6% | **0,172** | 85,2% |
| M4.1 BM25F | model wazenia | 23,3% | 33,3% | 0,156 | 97,0% |
| M4.2 PRF stosunek | statystyka z kodu | 30,0% | 40,0% | 0,139 | 80,7% |
| M4.2b PRF + LLR | statystyka z kodu | **33,3%** | 36,6% | 0,153 | **80,4%** |
| M4.3 proza repo | statystyka z prozy | 26,6% | 36,6% | 0,172 | 84,9% |
| M4.4 graf Suade | struktura | 26,6% | **40,0%** | 0,172 | 85,2% |
| M4.6 docstringi zewn. | korpus zewnetrzny | 20,0% | 36,6% | 0,169 | 86,7% |
| M5 codebook | **wiedza jawna** | 26,6% | 33,3% | 0,163 | 86,8% |

### Wniosek, na ktory pozwala osiem pomiarow

**`MRR` nie przekroczyl 0,172 ANI RAZU.** Ani statystyka, ani struktura, ani cudzy korpus,
ani recznie wpisana wiedza. Siedem mechanizmow z czterech roznych rodzin — i zaden nie
postawil poprawnego symbolu wyzej, niz stawial go goły ranker leksykalny.

Wspolna cecha wszystkich siedmiu: **DODAJA terminy do zapytania.** I to jest jedyna rzecz,
ktora je laczy ponad podzialem na statystyke i wiedze. Dodanie terminu rozciencza sygnal
terminow oryginalnych: symbol trafiony przez slowo z pytania konkuruje teraz z symbolami
trafionymi przez tokeny dodane — a te dodane sa z natury czestsze i liczniejsze.

M5 obala hipoteze, ktora wydawala sie najmocniejsza: **„wystarczy to zapisac recznie".**
Nie wystarczy. Zapisane recznie dziala tak samo zle jak wyliczone.

To NIE znaczy, ze wiedza jawna jest bezuzyteczna. Znaczy, ze **rozszerzanie zapytania jest
zlym dzwignia**, niezaleznie od zrodla rozszerzenia. Inne dzwignie (ograniczanie zakresu
zamiast dodawania terminow, routowanie pytania do podzbioru plikow) NIE BYLY testowane
i nie twierdze nic o nich.

Held-out (`blake2b256:e5d8e5b4...`) **NIETKNIETY**. Nadal nie ma kandydata.

## 2026-08-12T02:00 — POMIAR DIAGNOSTYCZNY: gdzie naprawde umiera system

Zanim zaprojektowalem M6, zmierzylem warunek konieczny dla calej rodziny „ograniczania":
czy wlasciwy symbol w ogole dostaje niezerowy wynik leksykalny? Bo bramka moze tylko
USUWAC konkurencje — nie wciagnie symbolu, ktorego w rankingu nie ma.

| gdzie lezy wlasciwy symbol (pelny ranking, 30 pytan) | ile |
|---|---|
| pozycja 1-10 | 8 (26%) |
| **pozycja 11-100+** | **11 (37%)** — osiagalne przez zawezanie |
| **wynik 0, poza rankingiem** | **11 (36%)** — NIEosiagalne przez zawezanie |

Mediana pozycji wsrod obecnych: **16**.

**Problem rozpada sie na dwa, mniej wiecej rowne.** 37% to zla KOLEJNOSC, 36% to brak
KANDYDATA. Optymalizowalismy je dotad jako jedno i dlatego kazdy mechanizm poprawial
jedno psujac drugie. Sufit dla samego ograniczania: **63,3%**.

## 2026-08-12T02:05 — PREREJESTRACJA M6: Scope Gate (zawezanie zamiast rozszerzania)

Szesc niezaleznych propozycji (GPT, Gemini, Copilot, Meta, Grok, DeepSeek) zbieglo sie
do tej samej dzwigni. Buduje **minimalna wersje Groka z pojeciami Mety** — najczystsze
sformulowanie plus zrodla zakresow pokrywajace 100% plikow.

**Konstrukcja — trzy warstwy zakresu, liczone offline, przypiete do `pack_hash`:**
- **A. Wspolzmiennosc commitow** — pary plikow `.py` w >= 3 wspolnych commitach, spojne
  skladowe grafu. Pokrywa pliki, ktorych CBMS nie dotyka (pokrycie CBMS to tylko 13%).
- **B. Spojne skladowe grafu wywolan** — nieskierowany graf `refs` z tree-sittera.
  Bez detekcji spolecznosci z ziarnem — spojne skladowe sa deterministyczne z definicji.
- **C. Katalogi** — kazdy katalog to zakres.

**Routowanie (czas zapytania):** odwrocony indeks LUDZKIEJ PROZY (chunki CBMS + komunikaty
commitow) -> pliki, ktore wskazuje. Pytanie dopasowywane **wylacznie po stronie prozy**,
nigdy do kodu. Top-3 zakresy. Kandydaci = symbole z plikow tych zakresow.

**Fallback:** zaden zakres nie trafil -> pelna przestrzen. Chroni recall.

**Ranking:** NIEZMIENIONY baseline, wylacznie wewnatrz bramki. **Zero dodanych terminow.**

**Pokretla — tylko dwa, ustalone przed pomiarem:** `MIN_COCHANGE=3`, `TOP_SCOPES=3`.
Odrzucam wersje Copilota mimo poprawnosci: kilkanascie wag na 30 pytaniach to zaproszenie
do przeuczenia, nie do pomiaru.

**KRYTERIUM PRZYJECIA — bez zmian, dla porownywalnosci z siedmioma poprzednimi:**
- `recall@10` >= **34,6%**, ORAZ `MRR` >= **0,172**, ORAZ `neg/poz` <= **85,2%**.

**WARUNEK DIAGNOSTYCZNY (pomiar, NIE kryterium)** — propozycja GPT, punkt 9:
ile razy bramka **wycieła** wlasciwy symbol, ktory mial niezerowy wynik. To rozdziela
„bramka za agresywna" od „ranking za slaby".

**PRZEWIDYWANIE zapisane przed pomiarem, tym razem oparte na liczbie:** zeby przekroczyc
34,6%, bramka musi wypchnac do pierwszej dziesiatki **2-3 symbole z tych jedenastu**
lezacych na pozycji 11+, przy medianie 16. Spodziewam sie, ze `recall@10` wzrosnie ORAZ
ze `MRR` tez wzrosnie — bo w odroznieniu od siedmiu poprzednich mechanizmow ten
**nic nie dodaje**, tylko usuwa konkurencje sponad wlasciwego symbolu. Jesli MRR mimo to
spadnie, znaczy to, ze bramka tnie wlasciwe symbole — i pokaze to warunek diagnostyczny.

## 2026-08-12T03:10 — M6 Scope Gate: ZMIERZONY I ODRZUCONY. Przewidywanie bledne.

Pomiar: `acae/_baseline/m4_gate_dev_5c5426f.json`, head `5c5426f`, zbior roboczy,
held-out NIETKNIETY.

| metryka | baseline | M6 gate | kryterium | werdykt |
|---|---|---|---|---|
| recall@10 | 26,6% | **23,3%** | >= 34,6% | NIE |
| recall@25 | 36,6% | 33,3% | — | spadek |
| MRR | 0,172 | **0,138** | >= 0,172 | NIE |
| neg/poz | 85,2% | **88,0%** | <= 85,2% | NIE |

**Trzy kryteria na trzy nietrafione. Moje przewidywanie („recall@10 wzrosnie ORAZ MRR
wzrosnie") jest falszywe.** Osmy mechanizm, osme odrzucenie.

### Warunek diagnostyczny odpowiedzial — i odpowiedz jest inna, niz zakladalem

| pomiar | wartosc | co znaczy |
|---|---|---|
| `gate_cut` | **2 z 30** | bramka prawie nigdy nie wyciela wlasciwego symbolu |
| `gate_fallback` | 2 z 36 | routowanie po prozie prawie zawsze cos wskazuje |
| `gate_size_median` | **140 z 169 plikow** | bramka zostawia 83% repo |
| wybrane zakresy | callgraph 33, dir 61, **cochange 0** | wspolzmiennosc nie wybrana ANI RAZ |

Zakladalem dwie mozliwosci: bramka za agresywna (wysokie `gate_cut`) albo ranking za
slaby. Zaszla trzecia, ktorej nie przewidzialem: **bramka nie bramkuje**. Mediana 140/169
to nie zawezenie, to no-op z szumem, ktory psuje wynik przez te nieliczne przypadki,
w ktorych jednak cos utnie.

### Dwie wady konstrukcyjne, obie moje, obie widoczne w paragonie

Paragon z pierwszego pytania:

```
callgraph:aions_core/AIONS_ULTIMATE_UNIFIED.py  score 7  files_in_scope 139
dir:aions_core/server                           score 6  files_in_scope 22
dir:control_plane/operator                      score 1  files_in_scope 3
```

1. **Spojne skladowe grafu wywolan zlepiaja sie w jedna kluche na 139 plikow.**
   W monolicie kazdy plik importujacy wspolne narzedzie wpada do tej samej skladowej.
   Ryzyko bylo do przewidzenia i NIE sprawdzilem go przed pomiarem — prerejestracja mowi
   „spojne skladowe sa deterministyczne z definicji", co jest prawda i zarazem nie ma nic
   wspolnego z tym, czy sa uzyteczne.
2. **Punktacja routingu nie jest normalizowana przez rozmiar zakresu.** Wynik to suma
   trafien prozy po plikach zakresu, wiec zakres na 139 plikow zbiera wiecej trafien niz
   zakres na 22 pliki **z definicji**, niezaleznie od trafnosci. W paragonie wyzej 139
   plikow wygrywa 7:6 z 22 plikami — po normalizacji kolejnosc bylaby odwrotna.
   To dlatego `cochange` (male, precyzyjne zakresy) nie zostalo wybrane ani razu.

### Co ten pomiar rozstrzyga, a czego nie

**Rozstrzyga:** ta konkretna konstrukcja zakresow jest odrzucona. Nie stroje `MIN_COCHANGE`
ani `TOP_SCOPES` po zobaczeniu wyniku.

**NIE rozstrzyga:** czy ograniczanie przestrzeni pomaga. Przy medianie 140/169 dzwignia
nie zostala pociagnieta. Twierdzenie „ograniczanie nie dziala" NIE ma pokrycia w tym
pomiarze i nie wolno go zapisac jako wniosku.

### Stan bilansu

Osiem mechanizmow, osiem odrzucen. Siedem pierwszych DODAWALO terminy: piec obnizylo MRR,
dwa (M4.3, M4.4) zostawily je dokladnie na 0,172 i polegly na recall@10. Zadne nie
podnioslo MRR ani o promil. Osmy mial nic nie dodawac — ale nie zadzialal na tyle, zeby
cokolwiek o tej klasie powiedziec.

Sprostowanie do pierwszej wersji tego akapitu: napisalem „wszystkie obnizaly MRR", co jest
nieprawda dla M4.3 i M4.4. Pelna tabela liczb w `TERMS.md`.

### Dlug do splacenia (stan na chwile zapisu)

- `acae/src/acae/scope.py` lezy w repo **bez testow**. Do napisania: `test_scope.py`.
- Regresja po M6 nieuruchomiona: `pytest`, `acae pack` (oczekiwany `pack_hash 6442322d...`),
  `measure_m2.py` (oczekiwane 10/10).
- Wpis do tabeli „Zmierzone i odrzucone" w `TERMS.md` — niedopisany.

**SPLACONY 2026-08-12T19:50:** testy napisane (145 zielonych), regresja czysta
(`pack_hash` bez zmian, brama M2 10/10), tabela w `TERMS.md` uzupelniona o wszystkie osiem.

## 2026-08-12T20:10 — ZMIANA REGULY: zakaz LLM/embeddingow COFNIETY przez Marcina

Prerejestracja M4.1-M4.5 zawierala jego wlasna regule: **„Nie uzywac LLM"**. Marcin ja dzis
cofnal, z warunkiem doslownym: *„trzymaj sie tego zeby to bylo maximum determistyczne
i auditowalne zeby tam nie bylo chalucynacji kod bite w bite"*.

Zakaz strojenia pod held-out **pozostaje w mocy**. Zbior held-out pozostaje nietkniety.

## 2026-08-12T20:15 — PREREJESTRACJA M7: statyczny embedding (most slownikowy)

**DLACZEGO TO NIE JEST DZIEWIATY WARIANT TEGO SAMEGO.** Pomiar diagnostyczny rozbil problem
na dwa: 37% to zla KOLEJNOSC (symbol obecny, nisko), 36% to brak KANDYDATA (symbol ma wynik
leksykalny **zero**). Osiem mechanizmow atakowalo kolejnosc. Zadne przeliczanie nie ruszy
zera — `0 * cokolwiek = 0`. Embedding daje kazdemu symbolowi wynik niezerowy, wiec jako
pierwszy w ogole **moze dotknac tych 36%**.

### Artefakt — przypiety, nie pobierany przy zapytaniu

`minishlab/potion-base-8M` (Model2Vec/POTION): **statyczna tablica token -> wektor**,
29 528 x 256, bez sieci neuronowej przy wnioskowaniu. Zdanie = **srednia wektorow tokenow**.

Eksport jednorazowy do `acae/_model/`: macierz int16, tokenizer BPE, karta modelu
z `blake2b256` obu plikow. Przy zapytaniu **nie ma `model2vec`, nie ma `torch`** — tylko
`numpy` i `tokenizers`. Model nie jest pobierany ani aktualizowany w locie.

### Determinizm — warunek Marcina „bit w bit", rozwiazany arytmetyka calkowita

Zmiennoprzecinkowy iloczyn skalarny NIE jest deterministyczny miedzy maszynami: BLAS
zmienia kolejnosc sumowania zaleznie od liczby watkow, a dodawanie floatow nie jest
laczne. Dlatego **przy zapytaniu nie ma ani jednego floata**:

1. **Kwantyzacja raz, przy eksporcie.** Jedna globalna skala `32767 / max|E|`,
   zaokraglenie do parzystego. Globalna, nie per-wiersz — per-wiersz zniszczylby
   proporcje miedzy wektorami.
2. **Iloczyn skalarny w `int64`.** Dodawanie liczb calkowitych JEST laczne i dokladne,
   wiec kolejnosc sumowania nie ma znaczenia. Zakres: 256 * 32767^2 = 2,7e11, miesci sie
   w int64 z zapasem czterech rzedow wielkosci.
3. **Normalizacja przez `math.isqrt`** — dokladny pierwiastek calkowity. Wynik podawany
   jako **promile w `int`**, zgodnie z kanonicznym JSON, ktory zabrania floatow.

Ten sam wynik na kazdej maszynie, przy kazdej liczbie watkow, w kazdej wersji BLAS.

### Audytowalnosc — dokladny rozklad, nie przyblizenie

Wektor dokumentu jest **srednia** wektorow tokenow, wiec podobienstwo rozklada sie
liniowo i **dokladnie**:

```
sim(q, d) = <q, mean_i(t_i)> = mean_i( <q, t_i> )
```

Kazdy token dokumentu wnosi policzalny udzial. Paragon poda pary token-token o najwiekszym
wkladzie, np. `machine <-> host: 340 z 610 promili`. To nie jest heurystyka wyjasniajaca
po fakcie — to jest ta sama arytmetyka, ktora dala wynik. **Transformer tego nie potrafi**;
wybieram model statyczny wlasnie dlatego, a nie dla rozmiaru.

### Tekst dokumentu i zapytania — regula ustalona teraz

- **Dokument (symbol):** `split_identifier` (z `bm25f.py`, jako narzedzie tokenizujace —
  precedens z `concepts.py`) na sciezce bez rozszerzenia, na `name_path`, plus slowa
  z `signature` i `doc`. Male litery, zlaczone spacja.
- **Zapytanie:** surowe pytanie, bez zmian. **Zero dodanych terminow.**

### Trzy warianty — WSZYSTKIE zadeklarowane teraz, wszystkie beda zaraportowane

- **M7a `embed`** — ranking wylacznie po podobienstwie.
- **M7b `embed_tie`** — leksyka glowna, embedding **tylko jako rozstrzygniecie remisow**
  przy rownym wyniku leksykalnym. Z konstrukcji nie moze zaszkodzic tym 8 pytaniom,
  ktore juz dzialaja, bo nie zmienia kolejnosci miedzy roznymi wynikami leksykalnymi.
- **M7c `embed_borda`** — suma rang z obu list. Fuzja **bez ani jednego pokretla**;
  odrzucam wazenie `a*leksyka + b*embedding`, bo `a` i `b` byly by strojeniem.

Skale nie sa porownywalne (`score_symbol` to nieograniczona suma wag pol, podobienstwo
to promile), dlatego fuzja idzie po RANGACH, nie po wartosciach.

### KRYTERIUM PRZYJECIA — bez zmian, dla porownywalnosci z osmioma poprzednimi

`recall@10` >= **34,6%** ORAZ `MRR` >= **0,172** ORAZ `neg/poz` <= **85,2%**.
Wariant „przechodzi" tylko przy spelnieniu wszystkich trzech. Zbior roboczy 30+/6-.

### WARUNEK DIAGNOSTYCZNY (pomiar, NIE kryterium) — najwazniejsza liczba tego etapu

**Z tych 11 pytan, gdzie wlasciwy symbol ma leksykalne ZERO — ile trafia do top-25
po samym embeddingu?** To odpowiada na pytanie, na ktore osiem pomiarow nie odpowiedzialo:
czy most slownikowy w ogole istnieje. Niezaleznie od werdyktu pass/fail.

### PRZEWIDYWANIE, zapisane przed pomiarem

- **M7b nie moze pogorszyc** `recall@10` ponizej 26,6% — to wynika z konstrukcji, nie
  z nadziei. Ale spodziewam sie malego zysku i **nie sadze, ze dobije do 34,6%**.
- **M7a pogorszy** wynik. Czysty embedding zgubi te 8 pytan, gdzie doslowna nazwa
  z kodu wystepuje w pytaniu — a tam leksyka jest nie do pobicia.
- **Diagnostyka: spodziewam sie, ze >= 4 z 11 zerowych trafi do top-25.** Jesli trafi
  0-1, to znaczy, ze mostu nie ma nawet przy semantyce, i **caly kierunek jest zamkniety**,
  niezaleznie od tego, co pokaza trzy warianty.

Po osmiu bledych przewidywaniach zaznaczam: moja skutecznosc w przewidywaniu tych
pomiarow wynosi **0 z 8**. Ten zapis istnieje po to, zeby wynik mnie mogl skorygowac,
a nie zebym ja tlumaczyl wynik po fakcie.

## 2026-08-12T21:05 — M7: ODRZUCONY wobec kryterium. Ale wynik jest inny niz osiem poprzednich.

Pomiary: `_baseline/m4_embed_dev_3495229.json`, `m4_embed_tie_dev_3495229.json`,
`m4_embed_borda_dev_3495229.json`. Head `3495229`. Zbior roboczy. Held-out NIETKNIETY.

| wariant | recall@10 | recall@25 | MRR | neg/poz | werdykt |
|---|---|---|---|---|---|
| baseline | 26,6% | 36,6% | 0,172 | 85,2% | — |
| **M7a `embed`** | **33,3%** | **40,0%** | **0,222** | **103,7%** | ODRZUCONY |
| **M7b `embed_tie`** | 26,6% | **40,0%** | 0,173 | 85,2% | ODRZUCONY |
| **M7c `embed_borda`** | **33,3%** | **40,0%** | **0,249** | niemierzalne | ODRZUCONY |

Kryterium (`recall@10` >= 34,6% ORAZ `MRR` >= 0,172 ORAZ `neg/poz` <= 85,2%) nie spelnia
zaden. **Dziewiec mechanizmow, dziewiec odrzucen.**

### Co jest tu NOWE i czego osiem poprzednich nie pokazalo

**Pierwszy raz MRR przekroczylo baseline.** Osiem poprzednich mechanizmow nie podnioslo
`MRR` ani o promil — piec obnizylo, dwa wyrownaly, jeden obnizyl mocno. M7c daje
**0,249 wobec 0,172, czyli +45%**. To nie jest szum na 30 pytaniach tej samej skali,
w ktorej wszystkie poprzednie stały w miejscu albo spadaly.

`recall@10` 33,3% wyrownuje najlepszy wynik w calej ablacji (M4.2b), a `recall@25` 40,0%
wyrownuje najlepszy (M4.4).

### WARUNEK DIAGNOSTYCZNY — obalil hipoteze, dla ktorej ten etap powstal

| pomiar | wartosc |
|---|---|
| pytan, gdzie wlasciwy symbol ma leksykalne ZERO | **11** (zgodne z pomiarem z 02:00) |
| z tego embedding wciaga do top-25 | **1** |
| mediana rangi w tej grupie | **336** |

Prerejestracja mowila: *„spodziewam sie, ze >= 4 z 11 trafi do top-25. Jesli trafi 0-1,
to znaczy, ze mostu nie ma nawet przy semantyce, i caly kierunek jest zamkniety"*.

Trafil **dokladnie 1**. Zgodnie z wlasnym zapisem: **most slownikowy dla grupy zerowej
NIE ISTNIEJE i ten kierunek jest zamkniety.** Mediana 336 nie jest „blisko" — to jest
poza jakimkolwiek realnym oknem.

### Wniosek, ktorego prerejestracja nie przewidziala

Skoro grupa zerowa nie drgnela, a `recall@10` i `MRR` wyraznie wzrosly, poprawa moze
pochodzic wylacznie z **przestawienia kolejnosci w grupie „obecny, ale nisko"** (37%
z pomiaru diagnostycznego). Czyli embedding pomaga **tam, gdzie leksyka juz cos widzi**,
i nie pomaga tam, gdzie leksyka milczy.

To jest **odwrotnosc powodu, dla ktorego go wybralem**. Zapisuje to jako obserwacje
POHOC, nie jako wynik: nie byla przewidziana, wiec nie ma sily dowodu. Gdyby miala byc
scigana, wymaga wlasnej prerejestracji i wlasnego pomiaru.

### Sciana: embedding nie umie powiedziec „nie wiem"

`mean_top1` dla M7a: **pozytywy 452, negatywy 469**. Negatywy dostaja wynik WYZSZY.
Cosinus zawsze znajdzie „cos podobnego" — pytanie spoza zakresu dostaje pelnowartosciowy
wynik. To nie jest do wyregulowania progiem, bo prog bylby pokretlem strojonym na 6
negatywach.

M7b to potwierdza od drugiej strony: leksyka jako glowna trzyma `neg/poz` dokladnie
na 85,2% i `recall@10` dokladnie na 26,6% — **konstrukcja obiecywala, ze nie zaszkodzi,
i nie zaszkodzila**. Zysk: `recall@25` 36,6% -> 40,0%, przy `MRR` praktycznie bez zmian.

### Wada mojej prerejestracji, ktora ten pomiar ujawnil

Zadeklarowalem **jedno kryterium dla trzech wariantow, nie sprawdzajac, czy skala wyniku
kazdego z nich to kryterium udzwignie.** M7c punktuje ujemna suma rang, wiec kontrola
`neg/poz` liczy `(-4 * 1000) // max(1, -13)` i daje bezsens (-400%). To **nie jest wynik
wariantu** — to dziura w moim planie pomiaru.

Glebsza wersja tej samej obserwacji: fuzja rang **z konstrukcji nie potrafi wyrazic
„nic nie pasuje"**, bo kazdy symbol ma range zawsze. Kontrola negatywow jest dla niej
strukturalnie niedefiniowalna, nie tylko zle policzona.

### Bilans przewidywan

Przewidywalem: M7a **pogorszy** wynik (poprawil, mocno), diagnostyka da **>= 4 z 11**
(dala 1). **0 z 9.** Zapisuje to z ta sama waga co liczby: mechanizm, ktory dziewiaty raz
z rzedu zaprzecza mojej intuicji, jest wazniejszym ustaleniem niz ktorykolwiek pojedynczy
wariant.

## 2026-08-12T21:40 — BLAD w `similarity_permille`, znaleziony przez test, pomiary przeliczone

Pisanie testow do `embed.py` wywrocilo dwie rzeczy, obie moje.

**1. Cosinus potrafil przekroczyc 1000 promili.** Liczylem `math.isqrt` osobno dla kazdej
normy i mnozyl je przez siebie. Kazde `isqrt` obcina w dol, wiec mianownik wychodzil za
maly. Zmierzone: `[1,2,3]` wobec `[2,1,1]` dawalo **1166** przy prawdziwej wartosci **764**.
Poprawka — pierwiastek brany RAZ, na koncu, na kwadratach:

    promile = isqrt( 10^6 * licznik^2 // (|a|^2 * |b|^2) )

Blad ograniczony do 1 promila z definicji `isqrt`. Ten sam blad byl w `receipt`
i w `EmbedIndex.scores` w mierniku — poprawiony w trzech miejscach.

**2. Paragon nie sumowal sie do wyniku.** Pomijalem pary o ujemnym wkladzie, wiec suma
czolowki przekraczala calosc (zmierzone: 535 wobec 440). Rozklad jest dokladny **tylko
ze wszystkimi skladnikami**. `receipt` zwraca teraz wszystkie pary; sortowanie malejaco
i tak stawia dodatnie na gorze, wiec czolowka wyglada tak samo, a suma przestala klamac.

To bylo twierdzenie, ktore zdazylem powiedziec Marcinowi jako „rozklad dokladny".
Bylo nieprawdziwe w tej wersji kodu.

### Pomiary przeliczone od nowa — wynik BEZ ZMIAN

Nie zalozylem, ze blad byl nieistotny — uruchomilem wszystkie trzy warianty ponownie
na poprawionym kodzie (`head f4ab3b6`):

| wariant | recall@10 | recall@25 | MRR | neg/poz | wobec pomiaru na wadliwym kodzie |
|---|---|---|---|---|---|
| `embed` | 33,3% | 40,0% | 0,222 | 103,7% | identycznie |
| `embed_tie` | 26,6% | 40,0% | 0,173 | 85,2% | identycznie |
| `embed_borda` | 33,3% | 40,0% | 0,249 | niemierzalne | identycznie |

Powod, dla ktorego nie drgnelo: przy prawdziwych danych normy sa rzedu `1e5`-`1e6`,
wiec wzgledny blad obciecia jest rzedu `1e-6` i nie przestawia rankingu. Blad ujawnial sie
tylko na malych wektorach — czyli **wylacznie w tescie jednostkowym**. Gdyby nie test
na malych liczbach, siedzialby w kodzie do momentu, w ktorym zaczalby szkodzic.

Straznik dopisany: `test_podobienstwo_nigdy_nie_przekracza_tysiaca` na 25 ziarnach malych
wektorow plus `test_znany_przypadek_z_regresji` na dokladnie tej parze, ktora to wywrocila.

## 2026-08-12T22:10 — POMIAR SUFITU: czy da sie wytrenowac WLASNE embeddingi na naszym korpusie

Pytanie Marcina: zbudowac wlasny zbior „slowo ludzkie -> nazwa funkcji", zeby ACAE nie
potrzebowalo obcego modelu. Zamiast dyskutowac — pomiar sufitu.
Skrypt: `scripts/measure_prose_ceiling.py`. Nic nie buduje, tylko liczy.

### Rozmiar calego korpusu ludzkiej prozy w tym repo

| | |
|---|---|
| dokumentow (komunikaty commitow + chunki CBMS) | **22** |
| znakow | **26 298** |
| unikalnych slow | **1 484** |
| ile potrzebuje sensowny word2vec / fastText | rzad **1e8** znakow |

Mamy **0,026%** tego, co potrzebne. To nie jest „malo danych do dostrojenia" — to jest
brak danych.

### Gorsza liczba: informacji nie ma nawet w formie surowej

Dla 11 pytan z grupy zerowej:

| sufit | ile z 11 |
|---|---|
| A — slowo z pytania wspolwystepuje w prozie wskazujacej wlasciwy plik | **1** |
| B — jakakolwiek proza w ogole opisuje wlasciwy plik | **2** |
| **zero prozy o tych plikach — nie ma czego uczyc** | **9** |

Nieosiagalne: `d001 d002 d003 d007 d008 d009 d023 d024 d030`.

**Wniosek, ktory zamyka kierunek:** nie da sie nauczyc odwzorowania z danych, ktorych nie
ma. Dla 9 z 11 pytan nie istnieje w repo ANI JEDEN ludzki tekst opisujacy wlasciwe pliki.
Zaden algorytm — embedding, wspolwystepowanie, siec — tego nie wyciagnie.

To rowniez tlumaczy wstecz M4.3 i M5: nie przegraly przez slaby algorytm, tylko przez
pusty korpus. Osiem pomiarow probowalo wycisnac sygnal ze zbioru, ktory go nie zawiera.

### Co ten pomiar NIE zamyka

Sufit dotyczy uczenia sie z tego, co JEST. Nie dotyczy sytuacji, w ktorej opis zostanie
**napisany**. 26 KB to malo, bo repo prawie nie ma dokumentacji przypietej do plikow —
pokrycie CBMS to 23 ze 169 plikow (13%). Gdyby kazdy plik mial akapit opisu po ludzku,
korpus mialby wlasciwa wielkosc I doskonale przypiecie do plikow.

Wtedy jednak embedding jest zbedny: slowa z pytania trafialyby w opis **leksykalnie**,
przez istniejace pole `doc` w rankingu bazowym. Most nie wymaga modelu, wymaga tresci.

## 2026-08-12T22:40 — PREREJESTRACJA M8: opis kazdego pliku po ludzku (korpus TWORZONY, nie szukany)

Decyzja Marcina: generujemy opisy Haiku, budzet do 1 mln tokenow, „zeby to repo bylo
naprawde ogarniete". Osiem mechanizmow wyciskalo sygnal z korpusu, ktory go nie zawiera
(pomiar sufitu 22:10: 9 z 11 pytan bez ANI JEDNEGO ludzkiego tekstu o wlasciwych plikach).
M8 nie szuka sygnalu — **wytwarza go**.

### Co powstaje

Dla **wszystkich 169 plikow**, nie dla podzbioru potrzebnego pytaniom ze zbioru roboczego.
Wersja skrocona bylaby trenowaniem na tescie i uniewaznila dziewiec pomiarow porownawczych.

Wejscie generatora: **pelna tresc pliku** (348 486 tokenow lacznie, mediana 983 na plik),
nie sam outline. Budzet na to pozwala, a im wiecej model widzi, tym mniej zmysla.

Wyjscie: `acae/_desc/descriptions.json` — mapa `sciezka -> opis`, plus zapis pochodzenia
(model, data, `pack_hash` zrodla). Tresc statyczna i zacommitowana: generowanie jest
niedeterministyczne, ale UZYWANIE opisu juz nie. Ta sama granica co przy modelu M7 —
`export_model.py` wolno zalezec od `torch`, warstwie zapytania nie wolno.

### Regula punktowania — ustalona TERAZ, zeby nie byla pokretlem

Opis pliku wchodzi do rankingu **z waga pola `path`, czyli `W_PATH = 1`** — najnizsza
z istniejacych. Nie wprowadzam nowej wagi, bo nowa waga byloby pokretlem strojonym
po zobaczeniu wyniku. Opis jest wspolny dla wszystkich symboli z danego pliku:
wskazuje PLIK, nie symbol, i punktowanie ma to odzwierciedlac.

### KRYTERIUM PRZYJECIA — bez zmian, dziesiaty raz to samo

`recall@10` >= **34,6%** ORAZ `MRR` >= **0,172** ORAZ `neg/poz` <= **85,2%**.
Zbior roboczy 30+/6-. Held-out NIETKNIETY.

### WARUNEK DIAGNOSTYCZNY — wykrywacz halucynacji, ktory juz mamy

`neg/poz` pelni tu druga role. Zmyslony opis pasuje do wszystkiego, wiec **podnosi wynik
pytan spoza zakresu**. Dokladnie tak wysypal sie M7a (103,7%). Jesli Haiku bedzie
konfabulowac, ta liczba to pokaze, zanim uznamy cokolwiek za dzialajace.

Drugi pomiar: **ile z 11 pytan grupy zerowej przestaje miec zero** po dodaniu opisow.
To mowi wprost, czy most zostal zbudowany, niezaleznie od werdyktu pass/fail.

### PRZEWIDYWANIE, zapisane przed pomiarem

Grupa zerowa: spodziewam sie, ze **>= 7 z 11** przestanie miec wynik zero — bo opis
z definicji zawiera slowa, ktorymi czlowiek pyta. Ale spodziewam sie tez **wzrostu
`neg/poz`**, bo opisy dodaja duzo tekstu pasujacego do wszystkiego.

Moj bilans przewidywan to **0 z 9**. Zapisuje to ponownie, zeby wynik mial czym mnie
poprawic.

## 2026-08-12T23:22 — M8: ODRZUCONY wobec kryterium. Ale most ZOSTAL zbudowany.

Pomiar: `_baseline/m4_desc_dev_9e6c082.json`, head `9e6c082`, zbior roboczy, held-out NIETKNIETY.
Korpus: `_desc/descriptions.json` — 169 opisow, `claude-haiku-4-5-20251001`,
pack_hash zrodla `6442322d...` (zgodny, weryfikowany przy starcie pomiaru).

| miara | baseline | M8 desc | wymagane | werdykt |
|---|---|---|---|---|
| recall@10 | 26,6% | 26,6% | >= 34,6% | NIE |
| recall@25 | 36,6% | **46,6%** | — | najlepszy w calej ablacji |
| MRR | 0,172 | 0,156 | >= 0,172 | NIE |
| neg/poz | 85,2% | **25,0%** | <= 85,2% | TAK, z ogromnym zapasem |

**Dziesiaty mechanizm, dziesiate odrzucenie.** Dwa z trzech warunkow niespelnione.

### WARUNEK DIAGNOSTYCZNY — pierwsze trafne przewidywanie w tym projekcie

| pomiar | wartosc |
|---|---|
| pytan, gdzie wlasciwy symbol ma leksykalne ZERO | **11** |
| z tego opis daje wynik NIEZEROWY | **11 z 11** |
| z tego wchodzi do top-25 | **0** |
| mediana rangi w tej grupie | **200** |

Prerejestracja mowila: *„spodziewam sie, ze >= 7 z 11 przestanie miec zero"*. Wyszlo
11 z 11. **To jest pierwsze trafne przewidywanie po dziewieciu chybionych** i pierwszy
raz, gdy grupa zerowa w ogole drgnela — M7 (embedding) wciagnal do top-25 dokladnie
jeden symbol przy medianie rangi 336.

Ale drugie zdanie tej samej tabeli jest twarde: **zero z jedenastu dochodzi do top-25**,
mediana rangi 200. Most istnieje i prowadzi we wlasciwa strone, tylko konczy sie
dwiescie pozycji za daleko. Opis daje wlasciwemu plikowi punkty — i daje je rowniez
kilkuset niewlasciwym.

To rozdziela dwie rzeczy, ktore dziewiec poprzednich pomiarow mylilo: **„czy da sie
zbudowac most" (TAK, zmierzone) i „czy ten most wystarczy do rankingu" (NIE, zmierzone).**

### neg/poz spadl z 85,2% na 25,0% — i to NIE bylo przewidziane

Prerejestracja stawiala `neg/poz` w roli wykrywacza halucynacji i przewidywala WZROST:
*„opisy dodaja duzo tekstu pasujacego do wszystkiego"*. Spadl o 60 punktow, do wartosci
trzy razy lepszej niz najlepsza z dziewieciu poprzednich (80,4% w M4.2b).

Surowe liczby, bo sam stosunek tu nie wystarcza:

| | baseline | M8 |
|---|---|---|
| sredni top1 na POZYTYWACH | 2661 | 980 |
| sredni top1 na NEGATYWACH | 2268 | **245** |

Oba spadly, bo decyzja M8-a (nizej) obniza wagi globalnie. Ale negatywy spadly
**dziesieciokrotnie**, a pozytywy niecale trzykrotnie. Pytanie o rzecz, ktorej w repo
nie ma, straciło znacznie wiecej niz pytanie o rzecz, ktora jest.

### DECYZJA M8-a — opisy wchodza do `term_rarity`

Prerejestracja ustalila wage opisu (`W_PATH = 1`) i **przemilczala**, czy tekst opisu ma
liczyc sie do `df` przy wazeniu rzadkoscia. Milczenie nie bylo neutralne: `term_rarity`
daje terminowi wage `total // (1 + df)` z sufitem 512, wiec termin o `df = 0` dostaje
wage MAKSYMALNA. Slowa „machine", „password", „computer" po dodaniu opisow wystepuja
w repo wylacznie w opisach — bez wliczenia opisow do `df` mialyby wage 512 zamiast ~7.

Siedemdziesiat razy wiecej, niz wynika z „najnizszej wagi". M8 wygladalby swietnie
z powodu, ktorego nikt nie zapisal. **To ta sama klasa bledu po raz piaty**
(rowne wagi -> RARITY_CAP -> stosunek bez wsparcia -> LLR bez kontroli pospolitosci -> to).

Decyzja podjeta i zakomunikowana Marcinowi PRZED pomiarem: opis wchodzi do `df` na rowni
z pozostalymi polami. Wariant przeciwny NIE jest mierzony — bylby darmowym drugim strzalem.

### Czego ten pomiar NIE rozstrzyga — ograniczenie, ktore z niego wynika

Nie da sie na jego podstawie rozdzielic dwoch wyjasnien spadku `neg/poz`:
1. opisy niosa realna tresc, wiec pytania spoza zakresu maja sie w co nie trafic, albo
2. samo wliczenie opisow do `df` przekalibrowalo wagi pospolitych slow ludzkich.

Rozdzielilby je wariant „opis punktuje, ale nie wchodzi do `df`" — czyli dokladnie ten,
ktory decyzja M8-a odrzucila a priori. Odnotowuje to jako granice tego pomiaru, a nie
jako powod do dolozenia trzeciego wariantu po zobaczeniu wyniku.

Diagnostyka grupy zerowej jest wolna od tej watpliwosci: 11 z 11 symboli, ktore wczesniej
mialy zero, ma teraz wynik dodatni. Zero nie zamienia sie w liczbe dodatnia przez
przewazenie — tylko przez pojawienie sie trafienia. Opisy tresc niosa.

### Bilans przewidywan: 1 z 10

Trafione: grupa zerowa >= 7 z 11 (wyszlo 11 z 11).
Chybione: `neg/poz` wzrosnie (spadl o 60 punktow).

### Regresja po M8 — czysta

- `python -m pytest` -> **190 testow zielonych**
- `scripts/measure_m2.py` -> **10/10** przy wymaganych 8
- `python -m acae pack --root .` -> `pack_hash 6442322d5d5a...` **NIEZMIENIONY**,
  169 plikow, 1598 symboli, 36492 tokeny
- `--variant baseline` przeliczony po wszystkich edycjach -> 26,6% / 36,6% / 0,172 / 85,2%,
  czyli punkt odniesienia dla dziesieciu pomiarow odtworzony co do cyfry

### Dlug do splacenia

- `src/acae/describe.py` lezy w repo **bez testow**. Do napisania: `test_describe.py`.
  Ten sam dlug co po M6 przy `scope.py` — odnotowany, zeby nie zniknal.

**SPLACONY 2026-08-12T23:48:** `tests/test_describe.py` — 25 testow, pelny pakiet
**215 zielonych**. Tym razem testy NIE znalazly bledu, w odroznieniu od `embed.py`,
gdzie wywrocily cosinus. Odnotowuje to jako slabszy wynik niz tam: brak znalezionego
bledu nie jest dowodem poprawnosci.

Mocniejszy od testow jednostkowych okazal sie pomiar neutralnosci toru na PRAWDZIWYCH
danych: `rank_all` z PUSTA mapa opisow, na wszystkich 30 pytaniach pozytywnych zbioru
roboczego, dal **zero rozjazdow** z `retrieve.select` — identyczne wyniki, identyczna
kolejnosc, identyczne recall@10 26,6% / recall@25 36,6% / MRR 0,172.

To zamyka watpliwosc, ktora inaczej wisialaby nad calym M8: **roznica miedzy M8
a baseline'em pochodzi z opisow, nie z implementacji.** Bez tego sprawdzenia kazda
liczba z tego etapu byla by nieodroznialna od bledu w moim wlasnym kodzie.

## 2026-08-12T23:50 — korpus opisow ZAMROZONY

**Hasz zamrozony: `blake2b256:cc54efc7d4d27f1917bf46dbb966288b4c89cee1d5c5ae515d54980b4e5319aa`**
(`_desc/descriptions.json`, 165 928 bajtow, 169 opisow, `claude-haiku-4-5-20251001`,
pack_hash zrodla `6442322d...`)

Ta sama regula co przy `heldout_questions.json` i z tego samego powodu. Opisy sa dowodem
WYLACZNIE dlatego, ze powstaly na slepo: agenty mialy kategoryczny zakaz zagladania do
`acae/tests/` i go dotrzymaly (zero sciezek ze zbioru testowego w artefakcie, sprawdzane
przez `build_descriptions.py`).

W chwili, gdy przegeneruje je PO zobaczeniu wyniku pomiaru, moje decyzje o tym, co
poprawic, przeciekna do korpusu — i zbior roboczy zamieni sie w treningowy dokladnie
tak, jak stalo by sie z held-outem. Wtedy porownanie z dziesiecioma poprzednimi pomiarami
przestaje cokolwiek znaczyc.

**Wolno:** mierzyc na tym korpusie nowe mechanizmy rankingu.
**Nie wolno:** poprawiac opisow, zeby ktorykolwiek pomiar wyszedl lepiej.
Zmiana korpusu wymaga nowej prerejestracji i jest DRUGIM podejsciem ze wszystkimi
konsekwencjami, ktore to niesie (precedens M4.2b).

Wersja odrzucona przed pomiarem (mediana 59 slow, jeden wpis zepsuty) lezy
w `_desc/v1_rejected/` i NIE byla mierzona — odrzucona na podstawie samej jakosci
korpusu, zanim istnialy jakiekolwiek liczby.

## 2026-08-12T23:53 — PREREJESTRACJA M9: cztery odrzucone mechanizmy, powtorzone na korpusie opisow

### Dlaczego to NIE jest druga proba w sensie M4.2b

M4.2b bylo: **ten sam korpus, zmieniony mechanizm po zobaczeniu wyniku**. Dlatego oslabialo
dowod i dlatego zapisalem wtedy, ze trzeciej proby nie bedzie.

M9 jest: **ten sam mechanizm, nietkniety, na innym wejsciu**. Zaden prog, zadna waga,
zaden limit nie zmienia sie wobec pierwotnego pomiaru. Zmienia sie WYLACZNIE zrodlo
tekstu pisanego po ludzku — bo pomiar sufitu z 22:10 wykazal, ze tego tekstu w repo
NIE BYLO (9 z 11 pytan bez ani jednego zdania o wlasciwych plikach), a M8 go wytworzyl.

Regula, na ktora sie powoluje, zostala zapisana przeze mnie przy odrzuceniu BM25F,
zanim ta sytuacja zaistniala:

> *„Modul zostaje w repo NIEPODPIETY — wynik negatywny z dzialajaca implementacja da sie
> zmierzyc ponownie, gdy zmieni sie reszta pipeline'u. Ale tylko wobec nowej prerejestracji."*

To jest ta nowa prerejestracja.

### Dobor: tylko te, ktorych DIAGNOZA wskazywala pusty korpus

Powtarzam cztery z osmiu. Pozostale cztery odpadaja, bo opisy ich nie dotykaja i powtorka
zmierzylaby to samo drugi raz, placac za to zuzyciem zbioru roboczego:

| pominiety | dlaczego powtorka nic nie da |
|---|---|
| M4.1 BM25F | wejscie te samo; wpuszczenie opisu jako nowego pola wymaga NOWEJ WAGI, czyli pokretla |
| M4.2 / M4.2b PRF | okna w kodzie — opisy nie zmieniaja zrodel |
| M4.6 docstringi zewnetrzne | korpus stdlib — nasze opisy go nie ruszaja |
| M5 codebook | reczna mapa slowo -> identyfikator; opisy robia to samo i lepiej. Zbedny |

### Cztery warianty — WSZYSTKIE zadeklarowane teraz, wszystkie beda zaraportowane

**M9a `prf_desc`** — most z prozy, korpusem opisy zamiast commitow i `.md`.
Dokument = **opis pliku PLUS identyfikatory tego pliku**. Uzasadnienie ksztaltu, zapisane
przed pomiarem: `expand()` szuka wspolwystapien miedzy slowem z pytania a slownikiem
identyfikatorow WEWNATRZ dokumentu. Sam opis z zalozenia identyfikatorow unika (instrukcja
generatora kazala tlumaczyc `host_id` na „ktora maszyna"), wiec dokument z samego opisu
nie zawieralby po prostu drugiej strony mostu i mierzylby nic. Ksztalt „opis z doczepionymi
nazwami" jest dokladnie tym, co STATE z 20:30 zdiagnozowal jako powod, dla ktorego
`cbms_search` w ogole dziala: *„blok CBMS to opis z doczepionymi sciezkami"*.
Bez ruchu: `G^2 >= 10.83`, pokrycie >= 2, maks 3 na termin, maks 12 razem, waga 1/2.

**M9b `embed_desc`, `embed_desc_tie`, `embed_desc_borda`** — embedding, w ktorym tekst
symbolu to `symbol_text()` PLUS opis jego pliku. Bez ruchu: ten sam artefakt modelu, ta sama
kwantyzacja, ta sama arytmetyka calkowita, te same trzy sposoby laczenia.
**`embed_desc_borda` NIE JEST uprawniony do zaliczenia** — kontrola negatywow jest dla fuzji
rang strukturalnie niedefiniowalna (wada mojej prerejestracji M7, wykryta pomiarem).
Mierze go jako diagnostyke i tak raportuje.

**M9c `gate_desc`** — bramka zakresu, w ktorej routing idzie po opisach zamiast po commitach
i chunkach CBMS. Bez ruchu: zrodla zakresow A/B/C, `MIN_COCHANGE=3`, `TOP_SCOPES=3`,
fallback na pelna przestrzen. **Dwie wady konstrukcyjne wykryte w M6** (zlepiony graf wywolan
na 139 plikow, brak normalizacji punktacji przez rozmiar zakresu) **NIE sa naprawiane** —
ich naprawa uczynilaby z tego nowy mechanizm, a nie powtorke.

**M9d `graph_desc`** — propagacja po grafie, ziarnem ranking z opisami zamiast golego
baseline'u. Bez ruchu: `SEED_K`, `HOPS`, `DAMP_PERMILLE`, `BOOST_PERMILLE=500`.

### KRYTERIUM PRZYJECIA — bez zmian, jedenasty raz to samo

`recall@10` >= **34,6%** ORAZ `MRR` >= **0,172** ORAZ `neg/poz` <= **85,2%**.
Wszystkie trzy naraz. Zbior roboczy 30+/6-.

### WARUNEK WARTOSCI DODANEJ — nowy, zapisany teraz

Wariant, ktory przejdzie kryterium glowne, musi **dodatkowo pobic sam M8**:
`recall@10` > 26,6% ALBO `MRR` > 0,156. Bez tego zasluga nalezy do opisow, nie do
mechanizmu — a caly sens tego etapu to rozdzielenie tych dwoch rzeczy.

### REGULA OSTRZEGAWCZA — zapisana, zeby nie dalo sie jej pozniej przemilczec

Jesli kryterium przejdzie **wiecej niz jeden** wariant, traktuje to jako **sygnal
ostrzegawczy, nie sukces**. Cztery warianty nie sa niezalezne — wszystkie mierza te same
169 opisow na tych samych 30 pytaniach. `recall@10` skacze tu co 3,3 punktu, wiec przy
dostatecznej liczbie spojrzen cos przekroczy prog przypadkiem. To jest jedenasty do
czternastego pomiar na tym zbiorze i zapisuje ten koszt jawnie.

**Held-out (`blake2b256:e5d8e5b4...`) pozostaje NIETKNIETY.** Otwierany DOKLADNIE RAZ
i tylko wtedy, gdy ktorys wariant spelni oba warunki naraz.

### DIAGNOSTYKA WSPOLNA dla wszystkich czterech

Ile z **11 pytan grupy zerowej** wchodzi do top-25. Punkt odniesienia: M8 dal **0 z 11**
przy medianie rangi 200 z ~1372. Ta liczba mowi, czy mechanizm potrafi wylowic to,
co opisy juz uwidocznily — niezaleznie od werdyktu pass/fail.

Dla `gate_desc` dodatkowo, jak w M6: `gate_cut`, `gate_fallback`, `gate_size_median`.
Punkt odniesienia: mediana **140 ze 169 plikow**, czyli bramka, ktora nie bramkowala.

### PRZEWIDYWANIA, zapisane przed pomiarem. Bilans dotychczas: 1 z 10

- **`prf_desc` — PORAZKA.** Rodzina „dodaje terminy do zapytania" obnizyla `MRR`
  osiem razy na osiem, wliczajac sam M8. Spodziewam sie wzrostu recall i spadku MRR.
- **`embed_desc` — najmocniejszy kandydat.** Jedyna rzecz, ktora zabila M7a, to `neg/poz`
  103,7%, a M8 pokazal, ze opisy zbijaja te kontrole z 85,2% na 25,0%. Spodziewam sie,
  ze `embed_desc` po raz pierwszy spelni warunek negatywny. Co do `recall@10` nie mam
  pewnosci. `embed_desc_tie` z konstrukcji nie moze zaszkodzic.
- **`gate_desc` — PORAZKA wobec kryterium, ale mediana bramki spadnie ponizej 140/169**,
  bo routing wreszcie ma po czym rozrozniac pliki. Zlepiony graf wywolan zostaje i to on
  bedzie ograniczeniem.
- **`graph_desc` — recall@25 w gore, MRR bez zmian**, czyli ten sam profil co M4.4.

Zapisuje te przewidywania z ta sama waga co liczby. Dziewiec razy na dziesiec mylilem sie
co do wlasnego projektu i to jest ustalenie mocniejsze niz ktorykolwiek pojedynczy wynik.

## 2026-08-13T00:09 — M9: SZESC PRZEBIEGOW, ZERO PRZEJSC. Ale dwie rzeczy sa nowe.

Pomiary: `_baseline/m4_*_dev_c10ad34.json`, head `c10ad34`, zbior roboczy 30+/6-,
held-out NIETKNIETY. Korpus opisow `blake2b256:cc54efc7...`, niezmieniony.

### Regresja PRZED pomiarem — stare warianty nietkniete

`baseline` 26,6/36,6/0,172/85,2 · `graph` 26,6/40,0/0,172/85,2 · `embed_tie` 26,6/40,0/0,173/85,2
— co do cyfry zgodne z tabela ablacji sprzed M8. `pytest` 215 zielonych. Powtorka porownuje
sie z tymi samymi liczbami co pierwotne pomiary, a nie z ich przybizeniem.

### Wyniki

| wariant | recall@10 | recall@25 | MRR | neg/poz | zero->top25 | werdykt |
|---|---|---|---|---|---|---|
| baseline (M2) | 26,6% | 36,6% | 0,172 | 85,2% | 0/11 | — |
| M8 `desc` | 26,6% | **46,6%** | 0,156 | **25,0%** | 0/11 | ODRZUCONY |
| M9a `prf_desc` | **20,0%** | 33,3% | 0,166 | 83,4% | 0/11 | ODRZUCONY |
| M9b `embed_desc` | 30,0% | 36,6% | **0,243** | **97,7%** | **2/11** | ODRZUCONY |
| M9b `embed_desc_tie` | 26,6% | 40,0% | 0,173 | 85,2% | 0/11 | ODRZUCONY |
| M9b `embed_desc_borda` | 33,3% | 46,6% | 0,194 | niemierzalne | 0/11 | NIEUPRAWNIONY |
| M9c `gate_desc` | 26,6% | 36,6% | 0,172 | 85,2% | 0/11 | ODRZUCONY |
| M9d `graph_desc` | 20,0% | 43,3% | 0,147 | **24,9%** | 0/11 | ODRZUCONY |

Kryterium (`recall@10` >= 34,6% ORAZ `MRR` >= 0,172 ORAZ `neg/poz` <= 85,2%) nie spelnil
zaden. **Czternasty pomiar na zbiorze roboczym, czternaste odrzucenie.**
Regula ostrzegawcza nie musiala byc uzyta — nie przeszedl ani jeden, wiec nie ma ryzyka,
ze wybieram zwyciezce z szumu.

### NOWE #1 — `embed_desc` jako pierwszy wylawia to, co opisy uwidocznily

`zero->top25` = **2 z 11**. Punkt odniesienia: M7 (embedding bez opisow) dal 1 z 11
przy medianie rangi 336, M8 (opisy bez embeddingu) dal **0 z 11** przy medianie 200.
Dopiero polaczenie obu wciaga cokolwiek z grupy zerowej do zasiegu.

`MRR` 0,243 to drugi wynik w historii projektu (M7c mial 0,249) i drugi raz, gdy
`MRR` przekroczylo baseline. Warunek wartosci dodanej spelniony z zapasem:
`recall@10` 30,0% > 26,6% M8 ORAZ `MRR` 0,243 > 0,156 M8.

Zabija go **kontrola negatywna: 97,7%**. To jest ta sama sciana co przy M7a (103,7%)
i opisy jej NIE zdjely — mimo ze w samym M8 zbily te liczbe z 85,2% na 25,0%.

### NOWE #2 — bramka pogorszyla sie od LEPSZEJ prozy. To izoluje przyczyne M6.

| pomiar | M6 (commity + CBMS) | M9c (opisy) |
|---|---|---|
| `gate_size_median` | 140 ze 169 | **157 ze 169** |
| `gate_cut` | 2 | 0 |
| `gate_fallback` | 2 | 0 |

Przewidywalem, ze mediana SPADNIE ponizej 140, bo routing wreszcie ma po czym rozrozniac
pliki. Wzrosla do 157, a wynik jest **identyczny z baseline** — bramka przestala ciac
cokolwiek. Mechanizm dzialania jest czytelny: gdy KAZDY plik ma opis, kazdy termin trafia
w wiele plikow, wiec kazdy zakres zbiera trafienia — a punktacja nie jest normalizowana
przez rozmiar zakresu, wiec zlepiona skladowa grafu na 139 plikow wygrywa zawsze.

**To jest czysta izolacja przyczyny.** Zmienilem WYLACZNIE korpus i bylo gorzej, wiec
korpus nie byl ograniczeniem M6 — ograniczeniem sa dwie wady konstrukcyjne opisane
2026-08-12T03:10 (zlepiony graf wywolan, brak normalizacji). Swiadomie ich nie naprawialem,
bo naprawa czynilaby z tego nowy mechanizm. Teraz wiadomo, ze to one sa waskim gardlem —
i to jest ustalenie, ktorego M6 sam nie mogl dac.

### NOWE #3 — rozszerzanie zapytania szkodzi takze na dobrym korpusie

`prf_desc` dal `recall@10` **20,0%**, czyli o 6,6 punktu PONIZEJ baseline'u i najgorzej
ze wszystkiego, co probowalismy poza M4.6. Korpus byl tym razem gesty, przypiety do plikow
i pisany jezykiem pytan — czyli wszystkim, czego brakowalo M4.3. Nie pomoglo.

Dziewiaty mechanizm z rodziny „dodaje terminy do zapytania" i dziewiaty raz to samo.
Wniosek z 2026-08-12T01:15 („rozszerzanie zapytania jest zla dzwignia, niezaleznie od
zrodla rozszerzenia") dostal wlasnie najmocniejsze potwierdzenie: zrodlo bylo najlepsze
z mozliwych i dzwignia dalej jest zla.

### BILANS PRZEWIDYWAN — werdykty 3 z 4, mechanizmy 0 z 4

| przewidywalem | wyszlo |
|---|---|
| `prf_desc` przegra | TAK — ale przewidywalem wzrost recall, spadl o 6,6 pkt |
| `embed_desc` pierwszy raz spelni warunek negatywny | **NIE**. 97,7% |
| `gate_desc` przegra, mediana bramki spadnie ponizej 140 | przegral TAK, mediana **wzrosla** do 157 |
| `graph_desc` — recall@25 w gore, MRR bez zmian | recall@25 TAK (43,3%), MRR **spadl** do 0,147 |

Odnotowuje uczciwie: **przewidywanie „przegra" po dziesieciu porazkach nie jest umiejetnoscia.**
Kazde przewidywanie dotyczace MECHANIZMU — czyli tego, DLACZEGO cos wyjdzie tak a nie
inaczej — bylo bledne. To jest czternasty raz i nadal nie rozumiem tego systemu na tyle,
zeby przewidziec jego zachowanie.

### Co te szesc pomiarow rozstrzyga

1. Rozszerzanie zapytania jest odrzucone **takze przy najlepszym mozliwym korpusie**.
2. Bramka M6 przegrala przez KONSTRUKCJE, nie przez korpus — zmierzone, nie zgadniete.
3. Opisy placa **wylacznie w polaczeniu z embeddingiem**, i tylko tam ruszaja grupe zerowa.
4. Sciana przeniosla sie w jedno miejsce: **kontrola negatywna**. `embed_desc` ma najlepsze
   uporzadkowanie (`MRR` 0,243) i nie umie powiedziec „nie wiem" (97,7%). Sam M8 umie
   powiedziec „nie wiem" wzorowo (25,0%) i nie umie uporzadkowac. **Zadna proba nie ma
   obu wlasciwosci naraz.**

Punkt 4 NIE jest prerejestracja niczego. Zapisuje go jako obserwacje po fakcie, wiec
nie ma sily dowodu i wymagalby wlasnego, wczesniej zapisanego kryterium.

Held-out (`blake2b256:e5d8e5b4...`) **NIETKNIETY**. Nadal nie ma kandydata.

## 2026-08-13T00:41 — PREREJESTRACJA M10: weryfikacja INNA REPREZENTACJA

### Uczciwe pochodzenie hipotezy — zapisane, zeby nie dalo sie go przemilczec

Ten pomysl powstal **PO zobaczeniu czternastu wynikow** i po przeczytaniu cudzego kodu
(`aions_core/server/pocket_qc.py`, `crla_core.py`, `cbms_unified_server.py`). To jest
najslabszy rodzaj hipotezy — dorobiona do danych, a nie postawiona przed nimi.
Prerejestracja tego NIE naprawia; zapobiega wylacznie dalszemu strojeniu.
Odnotowuje to jako oslabienie sily dowodu, tak samo jak przy M4.2b.

### Skad sie bierze

Czternascie mechanizmow zmienialo PUNKTACJE. Ten nie zmienia jej wcale — zmienia
**warunek dopuszczenia** symbolu do odpowiedzi. Inna dzwignia, nie kolejny wariant tej samej.

Trzy niezalezne miejsca w dzialajacym AIONS decyduja o „nie wiem" **licznikiem swiadectw**,
nigdy progiem na podobienstwie:
- `cbms_unified_server.py:186` — `if len(refs) < 2` (PANIC),
- `crla_core.py:104` — `if len(chunks) < cand.min_hits` (odmowa, `min_hits` in {1,2,3}),
- `pocket_qc.py:45` — `cbms_count > 0`, czyli „czy tekst koduje sie na jakiekolwiek pojecie".

PocketQC dokłada druga zasade, ktorej ACAE nie stosuje NIGDZIE: sprawdza odpowiedz
**inna reprezentacja** niz ta, ktora ja wyprodukowala (codebook zamiast bazy wektorowej).
Dzis nasz ranker jest jednoczesnie sedzia wlasnej pracy — jedno przejscie, zero kontroli.

Nasze wlasne liczby mowia to samo: dwa warianty z twardym warunkiem obecnosci slowa
(M8 25,0%, `graph_desc` 24,9%) maja najlepsza kontrole negatywna w projekcie, a jedyny
bez niego (`embed_desc` 97,7%) — najgorsza.

### Konstrukcja

**Ranker: `embed_desc`, BEZ ZMIAN.** Najlepsze uporzadkowanie w projekcie (`MRR` 0,243).
Nie dotykam ani modelu, ani kwantyzacji, ani sposobu skladania tekstu symbolu.

**Weryfikator: twardy warunek leksykalny.** Dla kazdego symbolu liczymy, ile ROZNYCH
terminow zapytania wystepuje DOSLOWNIE w jego tekscie (`_haystack` + opis pliku).
Symbol wchodzi do odpowiedzi tylko przy `>= MIN_TERMS`. Gdy zaden symbol nie przejdzie —
**zwracamy pusto**, czyli „nie wiem".

Reprezentacje sa rozne z konstrukcji: ranker liczy podobienstwo gestych wektorow,
weryfikator sprawdza doslowna obecnosc tokenu. Weryfikator NIE jest tym, co szeregowalo,
wiec sprawdzenie nie jest sprawdzaniem samego siebie.

**Punktacja nie zmienia sie ani o promil.** Filtr moze tylko USUWAC. Nie promuje niczego,
nie dodaje terminow, nie wprowadza nowej wagi.

### `MIN_TERMS` — dwa warianty, oba zadeklarowane TERAZ

Nie wybieram wartosci po zobaczeniu wyniku, wiec deklaruje obie i obie zaraportuje:

- **M10a `verify1`** — `MIN_TERMS = 1`. Najslabszy mozliwy warunek: chocby jedno slowo
  z pytania musi gdzies wystapic. Ten sam prog, ktory baseline stosuje juz dzis
  niejawnie (symbol wchodzi do rankingu przy `score > 0`).
- **M10b `verify2`** — `MIN_TERMS = 2`. Wartosc NIE wymyslona teraz: `MIN_TERMS_COVERED = 2`
  stoi w `expand.py` od M4.2 (regula LCA), a `len(refs) < 2` jest progiem PANIC w AIONS.
  Dwa niezalezne precedensy, zadnego dobierania.

**Trzeciej wartosci nie bedzie.** Jesli obie przegraja, kierunek „twardy warunek
dopuszczenia" jest zamkniety dla tej konstrukcji.

### KRYTERIUM PRZYJECIA — bez zmian, pietnasty raz to samo

`recall@10` >= **34,6%** ORAZ `MRR` >= **0,172** ORAZ `neg/poz` <= **85,2%**.
Wszystkie trzy naraz. Zbior roboczy 30+/6-.

### WARUNEK WARTOSCI DODANEJ — jak w M9

Wariant, ktory przejdzie kryterium, musi pobic **oba** skladniki, z ktorych powstal:
lepszy od M8 (`recall@10` > 26,6% ALBO `MRR` > 0,156) ORAZ lepszy od `embed_desc`
(`neg/poz` < 97,7%). Inaczej nie jest polaczeniem, tylko jednym z nich w przebraniu.

### REGULA OSTRZEGAWCZA

Jesli przejda OBA warianty — sygnal ostrzegawczy, nie sukces. Roznia sie jednym progiem
na tych samych 30 pytaniach, wiec nie sa niezalezne. To jest pietnasty i szesnasty pomiar
na tym zbiorze i zapisuje ten koszt jawnie.

### WARUNEK DIAGNOSTYCZNY — dwie liczby, obie obowiazkowe

1. **`verify_cut`** — dla ilu pytan POZYTYWNYCH filtr USUNAL wlasciwy symbol. Odpowiednik
   `gate_cut` z M6 i jedyna rzecz odrozniajaca „filtr za ostry" od „ranker za slaby".
   Bez tej liczby porazka bylaby nieinterpretowalna.
2. **`verify_empty`** — dla ilu pytan NEGATYWNYCH odpowiedz wyszla PUSTA. Wprost miara
   „czy system nauczyl sie mowic nie wiem", niezalezna od werdyktu pass/fail.
   Punkt odniesienia: dzis pusta odpowiedz na negatyw nie zdarza sie ANI RAZU.

Plus wspolna diagnostyka M9: ile z 11 pytan grupy zerowej wchodzi do top-25.

### PRZEWIDYWANIA, zapisane przed pomiarem. Bilans: 1 trafione na 14

- **`neg/poz` mocno spadnie w obu wariantach.** To nie jest odwazne — filtr z definicji
  zeruje wynik tam, gdzie nie ma trafien, a pytania spoza zakresu takich trafien nie maja.
- **`verify1` NIE utnie grupy zerowej.** M8 pokazal, ze po dodaniu opisow wszystkie 11
  maja wynik niezerowy, czyli maja co najmniej jedno doslowne trafienie.
- **`verify2` utnie czesc grupy zerowej** — spodziewam sie `verify_cut` >= 3.
- **`MRR` wzrosnie w obu**, bo filtr usuwa smieci LEZACE NAD wlasciwym symbolem,
  a uporzadkowanie `embed_desc` zostaje nietkniete.
- **Pierwszy raz spodziewam sie PRZEJSCIA kryterium — przez `verify1`.**

Ostatnie zdanie zapisuje swiadomie, bo jest najbardziej narazone na osmieszenie.
Moj bilans przewidywan mechanizmow to **0 na 14**; przewidywalem porazke czternascie razy
i czternascie razy mialem racje, co nie jest umiejetnoscia. Pierwszy raz stawiam
na sukces i pierwszy raz naprawde nie wiem.

## 2026-08-15T21:46 — M10: ODRZUCONY, oba warianty. Filtr nie filtruje.

Pomiary: `_baseline/m4_verify1_dev_2c1f820.json`, `m4_verify2_dev_2c1f820.json`.
Zbior roboczy 30+/6-, held-out NIETKNIETY, korpus opisow bez zmian (`cc54efc7...`).

| wariant | recall@10 | recall@25 | MRR | neg/poz | werdykt |
|---|---|---|---|---|---|
| `embed_desc` (punkt wyjscia) | 30,0% | 36,6% | 0,243 | 97,7% | — |
| **M10a `verify1`** (MIN_TERMS=1) | 30,0% | 36,6% | 0,243 | **97,7%** | ODRZUCONY |
| **M10b `verify2`** (MIN_TERMS=2) | 30,0% | 36,6% | 0,242 | **97,5%** | ODRZUCONY |

Oba nie spelniaja dwoch z trzech warunkow. **Pietnasty i szesnasty pomiar, dwa kolejne
odrzucenia.** Zgodnie z prerejestracja: trzeciej wartosci `MIN_TERMS` NIE BEDZIE,
kierunek „twardy warunek dopuszczenia" w TEJ konstrukcji jest zamkniety.

### WARUNEK DIAGNOSTYCZNY — odpowiedzial jednoznacznie

| pomiar | verify1 | verify2 | co znaczy |
|---|---|---|---|
| `verify_kept_median` | **1429 z 1598** | **897 z 1598** | filtr przepuszcza 89% / 56% wszystkiego |
| `verify_empty` | **0 z 6** | **0 z 6** | ANI RAZU nie powiedzial „nie wiem" |
| `verify_cut` | 0 | 1 | filtr prawie nie tnie wlasciwych symboli |
| grupa zerowa -> top25 | 2 z 11 | 1 z 11 | zaostrzenie zaczyna szkodzic tej grupie |

`verify_empty = 0` jest calym werdyktem. Mechanizm powstal po to, zeby system
umial zwrocic pustke na pytanie o rzecz, ktorej nie ma. Nie zrobil tego ani raz.

### PRZYCZYNA — i jest to blad, ktory SAM zdiagnozowalem trzy dni wczesniej

Opisy daly kazdemu plikowi ~134 slowa zwyklej angielszczyzny. Slowa z pytan tez sa zwykle.
Wiec prawie kazdy symbol ma w tekscie swojego pliku co najmniej jedno — czesto dwa —
slowo z pytania. Warunek „>= N terminow obecnych" jest **trywialnie spelnialny**.

To jest DOKLADNIE ten sam tryb awarii co M9c (`gate_desc`), gdzie zapisalem:

> *„gdy KAZDY plik ma opis, kazdy termin trafia w wiele plikow, wiec kazdy zakres zbiera
> trafienia — a punktacja nie jest normalizowana przez rozmiar"*

Zdiagnozowalem to na poziomie ZAKRESOW i trzy dni pozniej zbudowalem to samo na poziomie
SYMBOLI. Mediana 140/169 plikow w M6, mediana 1429/1598 symboli w M10. Ten sam ksztalt.

**Wniosek ogolniejszy, wart zapamietania:** korpus opisow rozwiazal problem braku kandydata
i tym samym **uniewaznil kazdy filtr oparty na obecnosci slowa**. Te dwie rzeczy sa
tym samym zjawiskiem widzianym z dwoch stron: bogaty opis sprawia, ze wszystko pasuje
do wszystkiego — i dlatego pomaga na zerowy recall, i dlatego psuje kazde zawezanie.

### Blad w PRZENIESIENIU wzorca z AIONS — moj, nie AIONS-a

Wzorzec `len(refs) < 2` w AIONS dziala, bo `refs` to **wyniki retrievalu**, czyli juz
wyselekcjonowany maly zbior. Liczy „ile swiadectw ZNALAZLEM".

Ja policzylem „ile slow z pytania WYSTEPUJE w tym kandydacie" — i zastosowalem to do
KAZDEGO z 1598 kandydatow. To nie jest ta sama wielkosc. Skopiowalem forme licznika,
nie jego znaczenie. Prerejestracja tego nie wylapala, bo opisywala konstrukcje poprawnie
i nie zadawala pytania, czy licznik mierzy to samo, co pierwowzor.

### BILANS PRZEWIDYWAN: 1 z 5 w tym etapie

| przewidywalem | wyszlo |
|---|---|
| `neg/poz` mocno spadnie w obu | **NIE**. 97,7% -> 97,7% i 97,5%. Bez zmian |
| `verify1` nie utnie grupy zerowej | TAK. `verify_cut` = 0 |
| `verify2` utnie czesc, `verify_cut` >= 3 | **NIE**. `verify_cut` = 1 |
| `MRR` wzrosnie w obu | **NIE**. 0,243 -> 0,243 i 0,242 |
| **pierwszy raz przejdzie kryterium** | **NIE** |

Pierwszy raz postawilem na sukces i pierwszy raz mialem konkretny powod, zeby w niego
wierzyc. Nie przeszlo. Odnotowuje to z ta sama waga, z jaka zapisalem przewidywanie.

### Regresja

- `python -m pytest` -> **215 zielonych**
- `--variant baseline` -> 26,6% / 36,6% / 0,172 / 85,2% (punkt odniesienia odtworzony)
- `--variant embed_desc` -> 30,0% / 36,6% / 0,243 / 97,7% (punkt wyjscia odtworzony)
- `pack_hash` = `6442322d...` NIEZMIENIONY

### Gotcha — naprawa AIONS przesunela grunt pod eksperymentem

Poprawka echa (`299411d`) dotknela `aions_core/server/cbms_direct_server.py`
i `cbms_unified_server.py` — a oba sa wsrod 169 plikow packa. `pack_hash` zmienil sie
na `89447c7c...` i miernik **ODMOWIL LICZENIA**, zamiast po cichu wyprodukowac liczby
nieporownywalne z czternastoma poprzednimi pomiarami.

Dokladnie po to `load_descriptions` sprawdza hash. Gdyby tego warunku nie bylo, M10
zostalby zmierzony na innym repo niz M8 i M9, a roznica bylaby nie do wykrycia po fakcie.

Rozwiazanie: na czas pomiaru te dwa pliki cofniete do stanu z `262c70d`
(`git checkout 262c70d -- ...`), pomiar wykonany, poprawka przywrocona z `299411d`.
Obie wersje sa zacommitowane, wiec operacja jest odwracalna i widoczna w historii.

**Regula na przyszlosc:** kazda zmiana w `aions_core/`, `control_plane/`, `server/`
lub `scripts/` uniewaznia korpus opisow. Pomiary ACAE trzeba robic na stanie repo
przypietym do `pack_hash 6442322d...`, albo swiadomie przemrozic korpus od nowa
i zaczac tabele porownawcza od zera.

## 2026-08-15T22:20 — DIAGNOZA: pomylki sa SKUPIONE, nie rozrzucone

Skrypt: `scripts/measure_confusion.py`. Nic nie buduje, tylko liczy. Pytanie Marcina:
czy zle odpowiedzi biora sie z balaganu, czy z mylenia dziedzin (jego obraz: bibliotekarz
nie odroznia oleju silnikowego od slonecznikowego).

Dla kazdego pytania pozytywnego bierzemy czolowa dziesiatke obecnego najlepszego rankera
(`embed_desc`) i patrzymy, z ilu ROZNYCH katalogow pochodzi. Katalog (dwa poziomy) jest
tu przyblizeniem dziedziny.

| | pytania UDANE (9) | pytania NIEUDANE (21) |
|---|---|---|
| roznych katalogow w czolowce, mediana | 3 | **2** |
| ile z 10 z jednego katalogu, mediana | 5 | **8** |
| wlasciwy katalog obecny w czolowce | **9 z 9** | **7 z 21** |

**Wynik jest odwrotny do mojego oczekiwania i potwierdza hipoteze Marcina.** Przy porazce
ranking jest BARDZIEJ skupiony, nie mniej: osiem z dziesieciu odpowiedzi z jednego
katalogu — i w **14 z 21** przypadkow wlasciwy katalog nie pojawia sie w ogole.

Przyklady skrajne:
```
d007  wszystkie 10 z control_plane/operator   ->  odpowiedz byla w scripts
d009  wszystkie 10 z aions_core/server        ->  odpowiedz w mcpServers/VS_CODE_MCP_CODEX
d010  wszystkie 10 z aions_core/tools         ->  odpowiedz w aions_core/server
d022  wszystkie 10 z control_plane            ->  odpowiedz w mcpServers, pozycja 1127
d026  wszystkie 10 z aions_core/server        ->  odpowiedz w scripts, pozycja 770
```

**To nie jest szum. To jest pewne siebie chodzenie na zla polke.** Blad uporzadkowany
da sie naprawic kierowaniem; szumu nie.

### Sufit tego kierunku, policzony teraz

14 z 21 porazek to „zla polka" — te da sie w zasadzie uratowac routowaniem.
Pozostale **7 z 21 to „dobra polka, zla ksiazka"** — tam samo zawezenie nie wystarczy.
Czyli warstwa dziedzin adresuje najwyzej **dwie trzecie** dzisiejszych chybien.

### Drugi wzorzec, widoczny golym okiem w tych samych danych

Czterokrotnie powtarza sie ten sam ksztalt: **odpowiedz w `scripts`, ranker idzie
w `aions_core/server`** (d001, d007, d025, d026). To nie jest pomylka co do TEMATU,
tylko co do RODZAJU rzeczy: pytanie dotyczy czegos, co sie URUCHAMIA, a ranker podaje
cos, co STOI I NASLUCHUJE. Odnotowuje jako kandydata na druga warstwe, po dziedzinach.

## 2026-08-15T22:26 — PREREJESTRACJA M11: warstwa DZIEDZIN (routowanie do polki)

### Skad sie bierze i czym rozni sie od M6

M6 (`gate`) tez zawezal i przegral. Ale jego „zakresy" byly wyprowadzane ze STRUKTURY —
wspolzmiennosci commitow i grafu wywolan — i zlepily sie w jedna kluche na 139 plikow
ze 169. Bramka nie bramkowala. M9c powtorzyl go na opisach i bylo GORZEJ (mediana 157).

M11 zmienia rzecz zasadnicza: **dziedziny sa PISANE po ludzku, nie wyliczane.**
Ten sam ruch, ktory zadzialal przy opisach — nie licz tego, czego w repo nie ma, tylko
to wytworz. Dziedzina moze przecinac katalogi i nie ma obowiazku pokrywac sie z drzewem.

### Co powstaje

Dwuetapowo, obie czesci pisane przez model, obie zamrozone i zacommitowane:

1. **Lista dziedzin** — model dostaje wszystkie 169 opisow (zamrozony korpus
   `cc54efc7...`) i proponuje dziedziny wraz z opisem kazdej: czym jest, jakimi slowami
   czlowiek by o nia zapytal.
2. **Przypisanie** — kazdy ze 169 plikow trafia do jednej lub kilku dziedzin.

**KATEGORYCZNY ZAKAZ: model NIE oglada `acae/tests/`.** Ta sama regula co przy opisach
i ten sam powod — inaczej piszemy sobie odpowiedzi do wlasnego egzaminu.

Wyjscie: `_desc/domains.json` — dziedziny plus mapa plik -> dziedziny, z prowieniencja
(model, data, `pack_hash`, hash korpusu opisow).

**LICZBA DZIEDZIN: 12-20, ustalona TERAZ, przed generowaniem.** Nie jest to pokretlo
strojone na wyniku, tylko warunek arytmetyczny: przy 169 plikach daje 8-14 plikow na
dziedzine, wiec przy `TOP_DOMAINS = 3` zawezenie wypada w okolicach 25-42 plikow —
z zapasem ponizej progu 85 z warunku koniecznego. Gdyby dziedzin bylo 5, kazda mialaby
po 34 pliki i trzy wybrane daly by 100+, czyli mechanizm bylby no-opem jeszcze przed
pomiarem. Ta liczba jest wiec czescia konstrukcji, nie jej strojeniem.

### Jak sie tego uzywa przy zapytaniu

Pytanie porownywane jest **z opisami DZIEDZIN**, nie z plikami — tym samym embeddingiem,
ktory juz mamy. Wybieramy `TOP_DOMAINS` dziedzin. Ranking `embed_desc` biegnie potem
WYLACZNIE po plikach z tych dziedzin. Sam ranker BEZ ZMIAN.

**Fallback:** gdy zadna dziedzina nie zostanie wybrana — pelna przestrzen, jak w M6.
Chroni recall i jest oznaczane w diagnostyce.

### `TOP_DOMAINS` — dwa warianty, oba zadeklarowane TERAZ

- **M11a `domain3`** — trzy dziedziny. Wartosc z precedensu: `TOP_SCOPES = 3` w M6.
- **M11b `domain1`** — jedna dziedzina. Zawezenie maksymalne, drugi kraniec.

**Trzeciej wartosci nie bedzie.**

### WARUNEK KONIECZNY — nauczka z M6 i M10, zapisana PRZED pomiarem

Dwa razy zbudowalem filtr, ktory nie filtrowal (M6: mediana 140/169 plikow,
M10: 1429/1598 symboli), i dwa razy odczytalem z tego wnioski, ktorych ten pomiar
nie uprawnial.

Dlatego: **jesli mediana zawezenia zostawi wiecej niz POLOWE plikow (>= 85 ze 169),
mechanizm uznaje za NIEURUCHOMIONY, a wynik za NIEINTERPRETOWALNY** — niezaleznie od
tego, co pokaza pozostale liczby. Nie wolno wtedy napisac ani „zawezanie dziala",
ani „zawezanie nie dziala".

### KRYTERIUM PRZYJECIA — bez zmian, siedemnasty raz

`recall@10` >= **34,6%** ORAZ `MRR` >= **0,172** ORAZ `neg/poz` <= **85,2%**.
Wszystkie trzy naraz. Zbior roboczy 30+/6-.

### WARUNEK WARTOSCI DODANEJ

Musi pobic punkt wyjscia `embed_desc`: `recall@10` > 30,0% ALBO `neg/poz` < 97,7%.

### DIAGNOSTYKA — obowiazkowa, trzy liczby

1. `domain_files_median` — ile plikow zostaje po zawezeniu (patrz warunek konieczny).
2. `domain_cut` — dla ilu pytan pozytywnych wlasciwy plik zostal WYCIETY.
   Sufit z pomiaru 22:20 mowi, ze 14 z 21 porazek to zla polka; ta liczba powie,
   ile z nich naprawilismy, a ile nowych zepsulismy.
3. `domain_empty` — dla ilu pytan NEGATYWNYCH nie wybrano zadnej dziedziny.
   Dzis system nie mowi „nie wiem" ani razu.

### PRZEWIDYWANIA. Bilans: 1 na 15

- **Zawezenie tym razem ZADZIALA** — mediana spadnie znacznie ponizej 85 plikow.
  Opieram to na tym, ze dziedziny sa pisane, a nie zlepiane ze struktury.
- **`recall@10` wzrosnie**, bo 14 z 21 porazek to zla polka.
- **`domain_cut` bedzie niezerowy** — spodziewam sie 2-4 pytan, w ktorych zawezenie
  wytnie wlasciwy plik. To jest cena kierowania i chce ja zobaczyc, a nie ukryc.
- **`neg/poz` prawie sie nie ruszy.** Dziedzina zawsze jakas zostanie wybrana, wiec
  odpowiedz i tak powstanie. „Nie wiem" wymaga warstwy „czym to NIE jest" — osobnej
  i nierejestrowanej tutaj.

Zapisuje takze kierunek zgloszony dzis przez Marcina, ktorego NIE mierze i ktory
wymagalby wlasnej prerejestracji: **bibliotekarz, ktory pyta, gdy nie wie.** Warunkiem
wstepnym jest umiejetnosc rozpoznania wlasnej niewiedzy — czyli dokladnie to, czego
brakuje od szesnastu pomiarow. Wariant zachowujacy determinizm: pytac OFFLINE i zamrazac
odpowiedz, tak jak zrobilismy z opisami. Wariant slabszy, ale tani: zapisywac pytania
bez odpowiedzi jako liste dziur w bibliotece.

## 2026-08-15T23:07 — M11: ODRZUCONY. Ale PIERWSZY RAZ zawezenie faktycznie zawezilo.

Pomiary: `_baseline/m4_domain3_dev_bb886cf.json`, `m4_domain1_dev_bb886cf.json`.
Artefakt: `_desc/domains.json` — 20 dziedzin, 169 przypisan, `claude-opus-5`.
Zbior roboczy 30+/6-, held-out NIETKNIETY.

| wariant | recall@10 | recall@25 | MRR | neg/poz | werdykt |
|---|---|---|---|---|---|
| `embed_desc` (punkt wyjscia) | 30,0% | 36,6% | 0,243 | 97,7% | — |
| **M11a `domain3`** | 23,3% | 30,0% | 0,178 | 98,6% | ODRZUCONY |
| **M11b `domain1`** | 23,3% | 26,6% | 0,164 | 94,2% | ODRZUCONY |

Siedemnasty i osiemnasty pomiar. Oba gorsze od punktu wyjscia na `recall@10`.

### WARUNEK KONIECZNY — po raz pierwszy SPELNIONY

| | domain3 | domain1 | prog niezadzialania |
|---|---|---|---|
| `domain_files_median` | **29 ze 169** | **9 ze 169** | >= 85 |

M6 zostawial 140 ze 169, M9c 157, M10 1429 z 1598 symboli. **Tym razem mechanizm
naprawde sie uruchomil** i wynik JEST interpretowalny. To jest jedyny powod, dla ktorego
mozna z tego pomiaru cokolwiek wyczytac.

### DLACZEGO PRZEGRAL — i to nie jest wina dziedzin

| | domain3 | domain1 |
|---|---|---|
| `domain_cut` | **18 z 30** | **22 z 30** |
| `domain_empty` | 0 z 6 | 0 z 6 |

Zawezenie wycina wlasciwy plik w 60% pytan przy trzech dziedzinach i w 73% przy jednej.
Ryzyko nazwane w prerejestracji („jesli pytanie trafi do zlego dzialu, ksiazki nie
znajdziemy w ogole") zrealizowalo sie w skali, ktorej nie przewidzialem — zakladalem
2-4 przypadki, wyszlo 18.

### Pomiar rozstrzygajacy: routing czy dziedziny?

Dla kazdego pytania sprawdzilem, na ktorej pozycji router stawia dziedzine, w ktorej
NAPRAWDE lezy odpowiedz (na 20 dziedzin):

| | ile z 30 |
|---|---|
| wlasciwa dziedzina w pierwszej trojce | **12** |
| wlasciwa dziedzina w pierwszej szostce | 17 |
| mediana pozycji wlasciwej dziedziny | **6 z 20** |

Losowo bylaby mediana 10 i okolo 4-5 trafien w trojce. Router jest wiec **lepszy od
przypadku, ale nierzetelny**: trafia za pierwszym podejsciem w 12 z 30 pytan.

**Dziedziny sa dobre.** Tam, gdzie router trafia, trafia w rzeczy oczywiste i czytelne
dla czlowieka: `personal-admin-and-calendar`, `keeping-the-system-healthy`,
`setup-environment-and-secrets`. Struktura polek nie jest problemem.

### BLAD KONSTRUKCYJNY, ktory teraz widze jasno

Pomiar z 22:20 mowil: **ranker pewnym krokiem idzie na zla polke**. Zbudowalem wiec
warstwe wybierajaca polke — i kazalem jej wybierac **tym samym embeddingiem**, ktory
te zla polke wybiera.

Wiec router chodzi tam, gdzie ranker i tak by poszedl. Roznica polega tylko na tym,
ze wczesniej wlasciwa odpowiedz lezala nisko (pozycja 40-800), a teraz jest **wycieta
calkowicie**. Zamienilem bledna kolejnosc na bledna nieodwracalnie.

To jest ta sama klasa bledu co przy M10: skopiowalem KSZTALT rozwiazania, nie zmieniajac
NARZEDZIA, ktore jest zepsute. Tam liczylem slowa tam, gdzie AIONS liczy swiadectwa.
Tu wybieram polke tym, co polki myli.

### Czego ten pomiar NIE rozstrzyga

**Nie rozstrzyga, czy kierowanie do dziedziny jest zlym pomyslem.** Rozstrzyga, ze
kierowanie NIE MOZE isc po tym samym podobienstwie, co ranking. Twierdzenie „warstwa
dziedzin nie dziala" nie ma pokrycia w tym pomiarze i nie wolno go zapisac jako wniosku.

Nie stroje `TOP_DOMAINS` na 6, mimo ze mediana 6 az sie o to prosi. To byloby dobranie
progu po zobaczeniu wyniku i uniewaznilo by cala prerejestracje. Zgodnie z zapisem —
trzeciej wartosci nie ma.

### BILANS PRZEWIDYWAN: 2 z 4

| przewidywalem | wyszlo |
|---|---|
| zawezenie zadziala, mediana ponizej 85 | **TAK** — 29 i 9 |
| `recall@10` wzrosnie | **NIE** — spadl z 30,0% na 23,3% |
| `domain_cut` 2-4 | **NIE** — 18 i 22 |
| `neg/poz` sie nie ruszy | TAK — 97,7% -> 98,6% i 94,2% |

### CO Z TEGO WYNIKA NA NASTEPNY KROK

Artefakt `_desc/domains.json` **zostaje i jest dobry** — 20 czytelnych polek, po 6-14
plikow, kazda ksiazka ma miejsce. Problemem jest wylacznie **czym wybieramy polke**.

Kandydat zgloszony przez Marcina tego samego wieczoru, teraz z konkretnym uzasadnieniem
z pomiaru: **kazda ksiazka (albo dziedzina) dostaje wypisana liste slow, na ktore ma sie
odezwac** — pisana, wybrana pod ODROZNIANIE, a nie pod opisywanie. Router leksykalny
po takich listach jest narzedziem INNYM niz embedding, wiec nie odziedziczy jego bledu.
Wymaga wlasnej prerejestracji.

Regresja: `pytest` 215 zielonych, `baseline` 26,6/36,6/0,172/85,2, `embed_desc`
30,0/36,6/0,243/97,7 — oba odtworzone co do cyfry. Poprawka echa cofnieta na czas
pomiaru i przywrocona po nim (`git checkout 299411d`).

## 2026-08-15T23:15 — STAN SZTUKI: to nie jest nowy problem i ma nazwe

Sprawdzone na zadanie Marcina, PRZED zbudowaniem czegokolwiek.

To, co robimy od M11, nazywa sie w literaturze **collection selection** (albo shard
selection / query routing): dzielimy zbior na czesci i kierujemy zapytanie tylko do tych,
w ktorych prawdopodobnie lezy odpowiedz. Klasyczne algorytmy to **CORI** (Callan i in.,
lata 90., podejscie leksykalne) i **ReDDE** (podejscie oparte na probkowaniu).

**Pomysl Marcina z wieza Babel — „slowo z jednej dziedziny slychac tylko w tej dziedzinie" —
jest DOKLADNIE skladnikiem `ICF` w CORI.** `ICF` to odwrotna czestosc kolekcyjna:

    icf_i = log((|C| + 0.5) / cf_i) / log(|C| + 1.0)

gdzie `cf_i` to liczba kolekcji zawierajacych termin. Termin obecny w niewielu kolekcjach
daje wysokie `ICF` i mocno wskazuje kolekcje; termin obecny prawie wszedzie daje `ICF`
bliskie zeru i nie wnosi nic. To jest to samo zdanie, ktore Marcin powiedzial obrazem
o chinskich paleczkach, tylko zapisane trzydziesci lat wczesniej.

### Co z tego BIERZEMY, a czego NIE

**Bierzemy zasade:** waga slowa rosnie, gdy nalezy do malej liczby dziedzin.

**NIE bierzemy wzoru CORI.** Ma wbudowane stale `d_t = 0.4` i `d_b = 0.4`, a praca
„Is CORI Effective for Collection Selection?" (ADCS 2004) pokazala, ze wynik jest na te
stale bardzo czuly, a przy `b = 1.0` CORI sprowadza sie po prostu do liczenia wspolnych
terminow. Stale dobrane na cudzych zbiorach sa dokladnie tym pokretlem, ktorego ta
metodologia zabrania. Wolimy wersje bez ani jednej takiej stalej.

Odnotowuje tez, ze istnieje bliska praca „Collection Selection with Highly Discriminative
Keys" (Hiemstra) — czyli dobor **kluczy odrozniajacych** dla kolekcji, co jest wprost
odpowiednikiem „karteczki chochlika".

## 2026-08-15T23:15 — PREREJESTRACJA M12: routing leksykalny po slowach odrozniajacych

### Co konkretnie naprawia

M11 przegral z jednego powodu, nazwanego w jego wpisie: **router wybieral polke tym samym
embeddingiem, ktory te polki myli.** Pomiar to potwierdzil — wlasciwa dziedzina trafiala
do pierwszej trojki tylko w 12 z 30 pytan.

M12 zmienia **DOKLADNIE JEDNA RZECZ: narzedzie routingu.** Dziedziny, przypisania,
ranking `embed_desc`, `TOP_DOMAINS` — wszystko bez ruchu. Dzieki temu roznica wobec M11
jest przypisywalna wylacznie zmianie routera, a nie czemukolwiek innemu.

### Konstrukcja

**Karteczki.** Kazda z 20 dziedzin dostaje pisana liste slow, na ktore ma sie odezwac.
Slowa dobierane pod **ODROZNIANIE**, nie pod opisywanie — to inne zadanie niz streszczanie
i tak zostanie modelowi postawione. Model widzi wszystkie 20 opisow naraz, zeby moc
wybierac slowa rozlaczne. **Zakaz ogladania `acae/tests/`** jak zawsze.

**Glosowanie.** Termin zapytania glosuje na kazda dziedzine, ktora ma go na karteczce,
z waga zalezna od tego, na ilu karteczkach w ogole wystepuje:

    waga = LICZBA_DZIEDZIN // liczba_dziedzin_z_tym_slowem

Arytmetyka calkowita, bez floatow. Slowo na jednej karteczce wazy 20, na dwoch 10,
na dziesieciu 2, na wszystkich 1. **Zero progow, zero stalych do dobrania.**

**Cisza.** Gdy zadne slowo zapytania nie pada na zadnej karteczce, nie ma glosow —
fallback na pelna przestrzen, odnotowany w diagnostyce jako `imp_silent`. Dla pytan
NEGATYWNYCH ta liczba jest wprost odpowiedzia na „czy system umie powiedziec nie wiem".

### Warianty: `imp3` i `imp1`

Te same wartosci co w M11 (3 i 1), zeby porownanie bylo jeden do jednego.
**Trzeciej wartosci nie bedzie.**

### KRYTERIUM PRZYJECIA — bez zmian, dziewietnasty raz

`recall@10` >= **34,6%** ORAZ `MRR` >= **0,172** ORAZ `neg/poz` <= **85,2%**.

### WARUNEK WARTOSCI DODANEJ — dwustopniowy, bo tu porownujemy dwie rzeczy

1. Wobec M11 (izolacja zmiany): `domain_cut` musi spasc **ponizej 18 z 30**.
   Bez tego zmiana routera nic nie dala i cala hipoteza upada, niezaleznie od reszty.
2. Wobec punktu wyjscia `embed_desc`: `recall@10` > 30,0% ALBO `neg/poz` < 97,7%.

### WARUNEK KONIECZNY — jak w M11

Jesli `domain_files_median` >= 85 ze 169, mechanizm jest NIEURUCHOMIONY, a wynik
NIEINTERPRETOWALNY. (W M11 wyszlo 29 i 9, wiec ryzyko jest male, ale zapis zostaje.)

### PRZEWIDYWANIA. Bilans: 3 trafione na 19

- **`domain_cut` spadnie** — ale nie wiem o ile. Stawiam, ze ponizej 18, czyli warunek
  pierwszy bedzie spelniony.
- **`recall@10` wzrosnie wobec M11 (23,3%)**, ale **NIE dobije do 34,6%**.
- **`imp_silent` bedzie niezerowy na negatywach** i to bedzie najciekawsza liczba
  tego etapu — pierwszy raz mielibysmy mechanizm, ktory potrafi zamilknac.
- **Kryterium jako calosc NIE zostanie spelnione.**

Zapisuje to ostatnie zdanie swiadomie po wczorajszym, gdy postawilem na sukces i przegralem.
Nie zmieniam jednak zdania z powodu wstydu: zmieniam je, bo M11 pokazal, ze routing trafia
w dobra polke w 12 z 30 przypadkow, a poprawa narzedzia musialaby byc ogromna, zeby
z tego zrobic 34,6% skutecznosci calosci.

## 2026-08-16T04:20 — ROZPOZNANIE: mechaniki z gier, ktore rozwiazywaly nasz problem

Na zadanie Marcina. Trzy zrodla, wszystkie sprawdzone, nie z pamieci.

### 1. Parser Infocom / Inform — CZASOWNIK JEST OGRANICZENIEM TYPU

To jest najwazniejsze znalezisko i najlatwiejsze do przeniesienia.

Kazdy czasownik ma liste **linii gramatyki**, probowanych PO KOLEI, pierwsza pasujaca
wygrywa. Linia to ciag **tokenow**, a kazdy token jest OGRANICZENIEM na kandydata:

| token | co dopuszcza |
|---|---|
| `noun` | cokolwiek „w zasiegu" (scope) |
| `held` | tylko to, co aktor NIESIE |
| `creature` | tylko obiekt ozywiony |
| `edible` (ATTR_FILTER_TT) | tylko obiekty z dana **cecha** |
| `noun=Routine` (ROUTINE_FILTER_TT) | predykat wolany dla kazdego kandydata |
| `scope=Spells` (SCOPE_TT) | **PODMIENIA cala regule zasiegu** dla tego czasownika |

Przyklad z biblioteki: `Verb 'burn' 'light' * noun -> Burn * noun 'with' held -> Burn;`
— „spal X czym Y": X musi byc widoczny, Y musi byc TRZYMANY. Dwa rozne ograniczenia
w jednym zdaniu, oba deterministyczne.

Do tego dwa zachowania warte skopiowania:
- **implicit take** — gdy warunek nie jest spelniony, ale da sie go naprawic (banan lezy
  na polce, a `eat` wymaga trzymania), gra NIE ODMAWIA, tylko dobiera brakujacy krok,
- **disambiguation** — gdy pasuje kilka, PYTA: „masz na mysli bialy zeton czy chipsa?".

Zork mial 600 slow slownika i wywracal sie na slowie spoza listy. Nasza przewaga: slownik
pisze model, nie czlowiek. Mechanizm zostaje ten sam.

### 2. STALKER, A-Life — DWIE WARSTWY SYMULACJI

Swiat dzieli sie na **online** (pelna symulacja, blisko gracza) i **offline** (tanie
rekordy danych przesuwane po grafie). Gdy gracz sie zbliza, byt jest „przelaczany online"
i dopiero wtedy dostaje pelne AI. Do tego **Smart Terrains** — strefy, ktore nakladaja
wlasne reguly na kazdego, kto do nich wejdzie.

Przelozenie: tani przebieg po wszystkich 1598 symbolach (offline), a drogi sedzia tylko
dla tych ~25, ktore zostaly „przelaczone online". Smart Terrain = dziedzina, ktora niesie
wlasne reguly („tutaj preferuj rzeczy typu `stores`").

### 3. EVE Online, Overview — TAKSONOMIA + STANY + WYJATKI

Overview to silnik filtrowania boolowskiego nad **trojpoziomowa taksonomia**:
`typeID` -> `groupID` -> `categoryID`. My mamy dokladnie to samo: symbol -> plik -> dziedzina.

Dwie rzeczy, ktorych u nas nie ma:
- **stany** (przyjazny/wrogi) zmieniajace, czy dany typ w ogole sie wyswietla,
- **wyjatki HIERARCHICZNE, najwyzszy priorytet na gorze listy** — czyli deterministyczna
  regula rozstrzygania konfliktow. To jest wprost lekarstwo na znana chorobe systemow
  regulowych: gdy odpala sie wiele regul naraz, musi istniec zapisany porzadek.
- **zakladki = gotowe profile** przelaczane kontekstem, zamiast strojenia w locie.

## 2026-08-16T04:20 — PREREJESTRACJA M13: INTENCJA OGRANICZA RODZAJ (regula czasownika)

### Dlaczego to, a nie karteczki (M12 czeka dalej)

Pomiar pomylek z 22:20 pokazal wzorzec powtorzony **cztery razy**: odpowiedz lezala
w `scripts`, a ranker szedl w `aions_core/server` (d001, d007, d025, d026). To nie jest
pomylka co do TEMATU — to pomylka co do RODZAJU: pytanie dotyczy czegos, co sie URUCHAMIA,
a ranker podaje cos, co STOI I NASLUCHUJE.

W Zorku ta pomylka jest **niemozliwa**, bo token czasownika z gory odsiewa zly rodzaj.

I najwazniejsze praktycznie: **dane juz sa**. Przy przypisywaniu dziedzin (M11) kazdy
ze 169 plikow dostal `kind` z zamknietej szostki: `runs`, `serves`, `stores`, `checks`,
`connects`, `describes`. Rozklad: runs=77, checks=33, stores=19, describes=14,
connects=13, serves=13. Nie trzeba ani jednego nowego agenta.

### Konstrukcja

**Tablica intencji.** Maly, pisany recznie slownik: czasownik/fraza pytania -> dopuszczalne
rodzaje. Pisany WYLACZNIE z szostki `kind` i z ogolnych form pytan po angielsku,
**BEZ ogladania `acae/tests/`**. Kolejnosc linii ma znaczenie, pierwsza pasujaca wygrywa —
dokladnie jak linie gramatyki w Inform.

**Ograniczenie.** Gdy intencja rozpoznana, ranking `embed_desc` biegnie WYLACZNIE
po symbolach z plikow o dopuszczonym rodzaju. Punktacja bez zmian.

**Implicit take (z Zorka).** Gdy zaden kandydat nie przechodzi ograniczenia, NIE odmawiamy
— wracamy do pelnej przestrzeni i odnotowujemy to jako `intent_widened`. Odmowa w takiej
sytuacji byla by „petty", zeby uzyc slowa z dokumentacji Inform.

**Cisza.** Gdy zadna linia tablicy nie pasuje do pytania, ograniczenia nie ma —
`intent_none`. Ta liczba mowi, jak czesto tablica w ogole ma cokolwiek do powiedzenia.

### Warianty

- **M13a `intent`** — ograniczenie po rodzaju, ranking `embed_desc`.
- **M13b `intent_domain`** — ograniczenie po rodzaju ORAZ dziedzina z M11 (`TOP_DOMAINS=3`).
  Dwa tokeny naraz, jak `* noun 'with' held` w jednej linii gramatyki.

**Trzeciego wariantu nie bedzie.**

### KRYTERIUM PRZYJECIA — bez zmian, dwudziesty raz

`recall@10` >= **34,6%** ORAZ `MRR` >= **0,172** ORAZ `neg/poz` <= **85,2%**.

### WARUNEK WARTOSCI DODANEJ

Wobec punktu wyjscia `embed_desc` (30,0% / 0,243 / 97,7%): `recall@10` > 30,0%
ALBO `neg/poz` < 97,7%.

### WARUNEK KONIECZNY — jak zawsze od M11

Jesli mediana zawezenia zostawia ponad polowe symboli, mechanizm NIEURUCHOMIONY,
wynik NIEINTERPRETOWALNY.

### DIAGNOSTYKA — obowiazkowa

1. `intent_none` — dla ilu pytan tablica nie rozpoznala intencji.
2. `intent_cut` — dla ilu pytan pozytywnych ograniczenie wycielo wlasciwy plik.
   **To jest liczba, ktora zabila M11** (18 z 30). Musi byc znaczaco nizsza.
3. `intent_widened` — ile razy zadzialal implicit take.
4. `intent_symbols_median` — ile symboli zostaje po ograniczeniu.

### PRZEWIDYWANIA. Bilans: 5 trafionych na 23

- **`intent_cut` bedzie DUZO nizszy niz 18** — rodzajow jest szesc, a najliczniejszy
  (`runs`) obejmuje 77 ze 169 plikow, wiec ograniczenie jest z natury lagodniejsze
  niz wybor 3 z 20 dziedzin.
- **`intent_none` bedzie wysoki** — spodziewam sie, ze ponad polowa pytan nie trafi
  w zadna linie tablicy. Recznie pisana tablica na sluch to sluchowka Zorka: dziala
  swietnie w zakresie, ktory ktos przewidzial, i milczy poza nim.
- **`recall@10` wzrosnie nieznacznie**, bo mechanizm zadziala tylko na czesci pytan.
- **Kryterium jako calosc NIE zostanie spelnione.**

Zapisuje tez ksztalt docelowy, ktorego NIE buduje teraz i ktory wymaga wlasnej
prerejestracji: **dwuwarstwowa architektura w stylu A-Life** — tani przebieg po calosci,
drogi sedzia (lokalny model) tylko dla garstki przelaczonej „online" — plus
**hierarchiczne wyjatki w stylu EVE** jako deterministyczna regula rozstrzygania,
gdy odpali sie kilka regul naraz.

## 2026-08-16T04:41 — M13: ODRZUCONY. Ale `neg/poz` ruszylo sie PIERWSZY RAZ we wlasciwa strone.

Pomiary: `_baseline/m4_intent_dev_530b8dd.json`, `m4_intent_domain_dev_530b8dd.json`.
Zbior roboczy 30+/6-, held-out NIETKNIETY.

| wariant | recall@10 | recall@25 | MRR | neg/poz | werdykt |
|---|---|---|---|---|---|
| `embed_desc` (punkt wyjscia) | 30,0% | 36,6% | 0,243 | 97,7% | — |
| M11 `domain3` | 23,3% | 30,0% | 0,178 | 98,6% | — |
| **M13a `intent`** | 30,0% | 36,6% | 0,217 | **92,6%** | ODRZUCONY |
| **M13b `intent_domain`** | 20,0% | 26,6% | 0,144 | 99,7% | ODRZUCONY |

Kryterium: `intent` spelnia `MRR` (0,217 >= 0,172), nie spelnia `recall@10` ani `neg/poz`.
Dwudziesty i dwudziesty pierwszy pomiar.

### WARUNEK WARTOSCI DODANEJ — SPELNIONY przez `intent`

Zapisany przed pomiarem: `recall@10` > 30,0% ALBO `neg/poz` < 97,7%.
**`neg/poz` 92,6% < 97,7%**, przy NIEZMIENIONYM `recall@10` (30,0%) i `recall@25` (36,6%).

To jest **pierwszy raz, kiedy jakikolwiek mechanizm poprawil kontrole negatywna wobec
`embed_desc`, nie placac za to trafnoscia.** Poprawka jest skromna — 92,6% to wciaz daleko
od progu 85,2% — ale ta liczba nie drgnela we wlasciwa strone przez dwadziescia pomiarow.

### DIAGNOSTYKA

| | intent | intent_domain |
|---|---|---|
| `intent_none` (tablica milczala) | **22 z 36** | 22 z 36 |
| `intent_cut` (wycieto wlasciwy plik) | **6 z 30** | **20 z 30** |
| `intent_widened` (implicit take) | 0 | 1 |
| `intent_symbols_median` | 1598 z 1598 | 181 z 1598 |

**`intent_cut` = 6 wobec 18 w M11.** Ograniczenie po rodzaju jest trzykrotnie lagodniejsze
niz kierowanie do dziedziny, i to jest zgodne z konstrukcja: rodzajow jest szesc,
a `runs` obejmuje 77 ze 169 plikow.

**Tablica milczy w 22 z 36 pytan.** Czyli mechanizm w ogole nie dotknal 61% zbioru,
a i tak przesunal `neg/poz` o pieć punktow. Efekt na pytanie jest wiec wyrazniej wiekszy,
niz sugeruje liczba zbiorcza.

### WARUNEK KONIECZNY — zle dobrana statystyka, odnotowuje to jawnie

Prerejestracja mowila: „jesli mediana zawezenia zostawia ponad polowe, mechanizm jest
NIEURUCHOMIONY, a wynik NIEINTERPRETOWALNY". Mediana wyszla **1598 z 1598**, wiec wedlug
LITERY tej reguly `intent` jest nieuruchomiony.

Ale rozklad jest **dwumodalny**: w 22 pytaniach ograniczenia nie ma wcale, w 14 jest ostre.
Mediana mierzy wtedy tylko to, ktorych przypadkow jest wiecej, a nie sile mechanizmu.
Regula byla pisana pod inny tryb awarii — pod filtr, ktory ODPALA ZAWSZE i nie odsiewa
(M6: 140 ze 169, M10: 1429 z 1598). Tu jest odwrotnie: odsiewa mocno, ale rzadko.

**Nie uzywam tego jako furtki.** Werdykt i tak brzmi ODRZUCONY na dwoch warunkach z trzech,
wiec nic nie zalezy od tej reguly. Odnotowuje wylacznie, ze **zle dobralem statystyke
do tego mechanizmu**: dla filtra warunkowego wlasciwa miara to mediana LICZONA TYLKO
WTEDY, GDY FILTR ODPALIL, plus osobno czestosc odpalen. Nastepna prerejestracja
z filtrem warunkowym ma uzyc tej pary.

### `intent_domain` — dwa zle zawezenia nie daja jednego dobrego

`intent_cut` 20 z 30, czyli GORZEJ niz kazdy skladnik osobno (6 i 18). Przeciecie dwoch
niedoskonalych filtrow kumuluje ich bledy: wystarczy, ze jeden z nich sie pomyli, a plik
wypada. To jest wynik wart zapamietania przed skladaniem kolejnych warstw —
**warstwy nie sumuja sie, one sie mnoza, i to w zla strone.**

### BILANS PRZEWIDYWAN: 3 z 4 — najlepiej dotad

| przewidywalem | wyszlo |
|---|---|
| `intent_cut` duzo nizszy niz 18 | **TAK** — 6 |
| `intent_none` wysoki, ponad polowa | **TAK** — 22 z 36 |
| `recall@10` wzrosnie nieznacznie | **NIE** — stanelo dokladnie na 30,0% |
| kryterium jako calosc nie zostanie spelnione | **TAK** |

### CO Z TEGO WYNIKA

Regula czasownika **dziala w kierunku, w ktorym nic dotad nie dzialalo** — odsiewa pytania
spoza zakresu, nie tracac trafnosci. Ale dziala na 39% pytan, bo tablica jest recznie
pisana i ma sluchawke Zorka: swietna w zakresie, ktory ktos przewidzial, gluchа poza nim.

Naturalny nastepny ruch, WYMAGAJACY WLASNEJ PREREJESTRACJI: tablica intencji pisana
przez model zamiast przeze mnie, dokladnie tak jak opisy i dziedziny. To jest jedyna
przewaga, jaka mamy nad Zorkiem z 1979 — ich szescset slow wpisywal czlowiek.

Regresja: `pytest` 215 zielonych, `baseline` 26,6/36,6/0,172/85,2 i `embed_desc`
30,0/36,6/0,243/97,7 odtworzone co do cyfry. Poprawka echa cofnieta na czas pomiaru
i przywrocona po nim.

## 2026-08-16T05:30 — STAN SZTUKI: nasz problem ma nazwe i dwudziestoletnia literature

**Query Performance Prediction (QPP)** — przewidywanie, czy wyszukiwanie sie udalo,
BEZ zagladania do poprawnej odpowiedzi. Dokladnie nasza brakujaca umiejetnosc.

Rodzina **po-wyszukiwawcza** patrzy nie na slowa, tylko na **ROZKLAD WYNIKOW**:
- **NQC** (Normalized Query Commitment) — rozrzut (odchylenie) wynikow czolowki,
  znormalizowany. Intuicja: dobrze rozdzielony rozklad = latwe zapytanie.
- **Clarity** — dywergencja KL miedzy modelem jezykowym czolowki a calym korpusem.
- **WIG** — zagregowany przyrost informacji czolowki wobec korpusu.

Dlaczego to jest dla nas inne niz wszystko dotad: **nie dotyka zadnej z rzeczy,
ktore nam sie psuly.** Nie zalezy od slow (zabilo M10), nie wybiera polki (zabilo M11),
nie zmienia punktacji ani kandydatow. Czyta WYLACZNIE oceny, ktore ranker juz wyliczyl.
Czysta arytmetyka, wiec w pelni deterministyczne, zero nowych artefaktow.

**DWA ZASTRZEZENIA, oba z literatury, oba przeciwko nam:**
1. NQC dziala **o okolo 10% gorzej na neuronowym IR** niz na klasycznym — a nasz najlepszy
   ranker to wlasnie embedding. Udokumentowana slabosc dokladnie w naszym przypadku.
2. Standardowa praktyka to **dostrajanie `k` na zbiorze rozwojowym**. To jest zabronione.
   Wartosc musi byc ustalona z gory i z uzasadnieniem spoza danych.

## 2026-08-16T05:30 — M14: POMIAR SUFITU, nie mechanizm

### Dlaczego pomiar, a nie od razu mechanizm

Zeby na podstawie ksztaltu wynikow powiedziec „nie wiem", trzeba postawic **prog**.
Prog dobrany na szesciu negatywach to dokladnie to pokretlo, ktore uniewaznia wszystko.

Wiec najpierw pytanie tansze i wczesniejsze: **czy ten sygnal w ogole istnieje?**
Ten sam ruch, ktory uratowal nam tydzien przed M8 (`measure_prose_ceiling.py`: policz,
czy proza o tych plikach w ogole istnieje, zanim zaczniesz na niej trenowac).

**Ten wpis NIE jest prerejestracja mechanizmu i NIE ma werdyktu wobec kryterium.**
To pomiar diagnostyczny. Jesli sygnal istnieje — powstanie osobna prerejestracja
z progiem uzasadnionym strukturalnie, nie dobranym.

### Co liczymy

Dla kazdego z 36 pytan, na rankingu `embed_desc` (bez zmian):
- `NQC` w wersji calkowitoliczbowej: `1000 * odchylenie(czolowka_k) // srednia(wszystkie)`,
- `top1`, `srednia czolowki`, `spadek` miedzy pierwszym a dziesiatym wynikiem.

**`k = 10`, ustalone z gory i NIE dobrane:** nasze kryterium od M0 brzmi `recall@10`,
wiec dziesiatka jest w tym projekcie liczba pierwotna, starsza od tego mechanizmu.

### Pytanie, na ktore ma odpowiedziec

Czy **30 pytan pozytywnych** ma inny ksztalt wynikow niz **6 negatywnych**?
Jesli rozklady sie nakladaja — kierunek zamkniety, zadnego progu nie da sie postawic
i nie bedziemy udawac, ze da sie. Jesli sie rozdzielaja — jest po czym stawiac granice.

### PRZEWIDYWANIE

Spodziewam sie **slabego rozdzielenia**. Powod: `embed_desc` ma `neg/poz` 97,7%, czyli
srednia czolowka negatywow jest niemal identyczna jak pozytywow. To juz jest sygnal,
ze rozklady sa podobne. Ale `neg/poz` porownuje SREDNIE, a NQC patrzy na ROZRZUT —
to inna wielkosc i moze rozdzielac tam, gdzie srednia nie rozdziela.
Bilans przewidywan: 6 na 23.

### WYNIK — SYGNALU NIE MA. Kierunek zamkniety za godzine zamiast za dzien.

Skrypt: `scripts/measure_qpp_ceiling.py`. Ranking `embed_desc`, 30 pozytywow, 6 negatywow.

| miara | pozytywy (mediana) | negatywy (mediana) | rozlaczne? |
|---|---|---|---|
| NQC | 39 | **49** | NIE |
| spadek top1→top10 | 35 | **52** | NIE |
| odchylenie czolowki | 11 | **15** | NIE |
| top1 | 522 | **559** | NIE |
| srednia czolowki | 497 | **520** | NIE |

**Rozklady nie tylko sie nakladaja — sa lekko ODWROCONE.** Na kazdej z pieciu miar
negatywy wypadaja WYZEJ od pozytywow, czyli pytanie o rzecz, ktorej nie ma, wyglada
odrobine PEWNIEJ niz pytanie o rzecz, ktora jest.

Liczby szczegolowe sa jeszcze wymowniejsze. Szesc negatywow ma NQC 19, 22, 35, 49, 89, 96.
Szesc pozytywow o najnizszym NQC: 8, 12, 13, 14, 16, 19. **Pozytywy zajmuja DOLNY koniec
skali.** Prog „odmawiaj, gdy NQC ponizej X" odcinalby najpierw pytania, na ktore
odpowiedz istnieje.

### Dlaczego intuicja z literatury tu nie dziala

Hipoteza, ktorej NIE weryfikuje (obserwacja po fakcie): przy pytaniu SPOZA zakresu
embedding znajduje kilka rzeczy powierzchownie podobnych i one odstaja od reszty —
czolowka wychodzi ostra. Przy pytaniu SENSOWNYM wiele powiazanych plikow dostaje
podobne oceny, bo naprawde sa powiazane — czolowka wychodzi plaska.

Czyli w naszym korpusie **plaskosc znaczy „duzo rzeczy na temat", a nie „nic na temat"**.
To jest odwrotnie niz w klasycznym IR, gdzie kolekcja jest heterogeniczna. Nasze 169
plikow to jeden system, wiec wszystko jest ze wszystkim troche zwiazane.

Zgadza sie to takze z zastrzezeniem z literatury: NQC dziala gorzej na neuronowym IR.
U nas nie tyle dziala gorzej, co **nie dziala wcale**.

### Co ten pomiar rozstrzyga, a czego nie

**Rozstrzyga:** z samego rozkladu ocen `embed_desc` NIE DA SIE odczytac, czy odpowiedz
istnieje. Zadnego progu nie da sie tu poprowadzic i nie bedziemy udawac, ze da sie.
Cala rodzina po-wyszukiwawczych QPP na TYM rankerze jest zamknieta.

**NIE rozstrzyga:** czy dalo by sie to odczytac z rozkladu ocen INNEGO rankera —
w szczegolnosci przesiewacza (cross-encoder), ktory zwraca ocene z zupelnie innej skali
i z innego rodzaju osadu. To pozostaje otwarte.

### BILANS PRZEWIDYWAN: trafione

Przewidywalem „slabe rozdzielenie". Wyszlo **zadne, miejscami odwrocone** — czyli
kierunek zgodny, sila gorsza niz zakladalem. Zaliczam jako trafione: 7 na 24.

### CO Z TEGO WYNIKA

Ten pomiar **wzmacnia argument za przesiewaczem**. Skoro ksztalt ocen nie niesie
informacji o tym, czy odpowiedz istnieje, to potrzebne jest cos, co **naprawde czyta
pytanie i kandydata razem** — a nie mierzy statystyke tego, co juz policzyl embedding.

Koszt tego ustalenia: jeden skrypt i jedno uruchomienie. Gdybym poszedl od razu
w mechanizm, dobralbym prog na szesciu negatywach, dostal jakis wynik i dopiero pozniej
zorientowal sie, ze prog stoi po zlej stronie rozkladu.

### Uwaga Marcina do etapu przesiewacza (nie teraz, ale zapisane)

Gdy powstanie warstwa przesiewacza (cross-encoder), jej zapisane oceny **maja tworzyc
jedna siec z CBMS**, a nie lezec jako martwy plik obok. Czyli kazdy osad
„pytanie X <-> plik Y, ocena Z" ma trafiac do CBMS jako blok z `references`,
w tym samym ksztalcie co reszta pamieci AIONS. Wtedy pamiec rosnie na uzywaniu,
a nie tylko na generowaniu — i jest to zgodne z tym, co CBMS juz robi z chunkami.
Podpiecie do CBMS DOPIERO gdy przesiewacz sie sprawdzi (decyzja Marcina, 2026-08-16).

## 2026-08-16T05:27 — PREREJESTRACJA M15: PRZESIEWACZ (cross-encoder) na czolowce

### Dlaczego to jest inne narzedzie, a nie dwudziesty trzeci wariant

Dwadziescia dwa mechanizmy MIERZYLY PODOBIENSTWO — leksykalne, wektorowe, grafowe,
statystyczne. Wszystkie licza, jak bardzo dwie rzeczy sa do siebie podobne, i zadna
nie potrafi odroznic „to jest O oleju" od „to ODPOWIADA na twoje pytanie o olej".

Cross-encoder robi co innego: dostaje **pytanie i kandydata RAZEM, w jednym wejsciu**,
i zwraca jedna liczbe — na ile ten kandydat odpowiada na to pytanie. Nie porownuje
dwoch osobno policzonych reprezentacji. **Czyta pare.**

Wzmocnione pomiarem M14: ksztalt ocen embeddingu nie niesie ZADNEJ informacji o tym,
czy odpowiedz istnieje (rozklady nakladaja sie, miejscami odwrocone). Skoro statystyka
tego, co embedding policzyl, jest bezuzyteczna, potrzebne jest cos, co czyta.

Architektura wprost ze STALKERa (A-Life): **tanio wszedzie, drogo tylko dla garstki.**
Tani przebieg embeddingu po 1598 symbolach zostaje BEZ ZMIAN; drogi sedzia oglada
wylacznie czolowke.

### Model

`cross-encoder/ms-marco-MiniLM-L-6-v2` — ~22 mln parametrow, ~90 MB. Wybrany NIE przeze
mnie: `aions_core/aions_hybrid_retrieval.py:138` juz go wywoluje jako domyslny reranker
AIONS. Biblioteki (`sentence_transformers`, `torch`, `transformers`, `onnxruntime`)
sa zainstalowane; brakuje tylko pliku modelu.

### Ile kandydatow: `DEPTH = 25`

Nie dobrane teraz. `DEPTH = 25` stoi w `measure_m4.py` od poczatku ablacji M4 i jest
glebokoscia, na ktorej liczymy `recall@25`. Liczba starsza od tego mechanizmu.

### Tekst kandydata: DOKLADNIE ten sam, ktory widzi embedding

`symbol_text_with_description(path, row, opis)` — bez zmian. **To jest celowe
i wazniejsze niz wygoda:** gdybym podal przesiewaczowi ladniejszy tekst, nie wiedzialbym,
czy poprawa pochodzi z LEPSZEGO SEDZIEGO czy z LEPSZEGO MATERIALU. Ten sam material,
inny sedzia — roznica jest przypisywalna do jednej rzeczy.

Odnotowuje ryzyko tej decyzji: cross-encodery trenowano na prozie, a nasz tekst symbolu
to w duzej mierze rozbite identyfikatory. Moze to obnizyc wynik. Swiadomie place te cene
za czystosc eksperymentu.

### Determinizm — i uczciwie, gdzie jest jego granica

Przesiewacz **nie pisze, tylko mierzy**: brak losowania, brak temperatury, jedno wejscie
daje jedna liczbe. Ale to sa obliczenia zmiennoprzecinkowe, wiec miedzy maszynami
i wersjami bibliotek moga wystapic roznice na dalekich miejscach po przecinku.

**Rozwiazanie: artefaktem jest CACHE, nie model.** Oceny liczone RAZ, kwantyzowane
do liczb calkowitych (milijednostki), zapisane w `_desc/rerank_cache.json` z kluczem
`(hash pytania, pack_hash, nazwa modelu)` i ZACOMMITOWANE. Od tej chwili kazdy pomiar
odtwarza sie bit w bit **bez uruchamiania modelu w ogole**.

Ten sam wzorzec, ktory zadzialal trzy razy: streszczenia, dziedziny, tablica wektorow.
Droga rzecz dzieje sie raz, na boku, i zostaje zamrozona.

### Warianty

- **M15a `rerank`** — czolowa 25 z `embed_desc`, przestawiona wylacznie ocena przesiewacza.
- **M15b `rerank_abstain`** — jak wyzej, plus: gdy **najlepsza ocena przesiewacza jest
  ujemna**, zwracamy PUSTO.

**Prog zero NIE JEST dobrany na naszych danych.** To wlasna granica decyzyjna modelu:
przy trenowaniu binarnym logit 0 odpowiada prawdopodobienstwu 0,5, czyli „raczej nie".
Bierzemy granice modelu, nie swoja.

**WARUNEK UCZCIWOSCI:** przed pomiarem sprawdze karte modelu. Jesli nie potwierdzi
tej interpretacji wyniku, **M15b zostaje WYCOFANY, a nie przestrojony na inna wartosc.**

**Trzeciego wariantu nie bedzie.**

### KRYTERIUM PRZYJECIA — bez zmian, dwudziesty trzeci raz

`recall@10` >= **34,6%** ORAZ `MRR` >= **0,172** ORAZ `neg/poz` <= **85,2%**.

### WARUNEK WARTOSCI DODANEJ

Wobec `embed_desc` (30,0% / 0,243 / 97,7%): `recall@10` > 30,0% ALBO `neg/poz` < 97,7%.

### WARUNEK KONIECZNY — sufit przestawiania

Przesiewacz przestawia WYLACZNIE czolowa 25. Jesli wlasciwej odpowiedzi tam nie ma,
nie moze jej wciagnac. Sufit `recall@25` dla `embed_desc` to **36,6%**, wiec
`recall@10` po przestawieniu **nie moze przekroczyc 36,6%**. Prog 34,6% miesci sie
pod tym sufitem, ale z zapasem tylko 2 punktow — odnotowuje to jawnie, zeby nie udawac,
ze mechanizm ma duzo miejsca.

### DIAGNOSTYKA — obowiazkowa

1. `rerank_moved` — dla ilu pytan przesiewacz zmienil symbol na pierwszym miejscu.
   Zero znaczyloby, ze zgadza sie z embeddingiem i niczego nie wnosi.
2. `rerank_promoted` — dla ilu pytan pozytywnych wlasciwy symbol AWANSOWAL do top-10
   z pasma 11-25. To jest cala nadzieja tego etapu.
3. `rerank_demoted` — dla ilu SPADL z top-10. Cena.
4. `abstain_neg` / `abstain_pos` — ile negatywow i ile pozytywow dostalo pustke.
   **Pierwsza para liczb w tym projekcie, ktora wprost mierzy „umie powiedziec nie wiem".**

### PRZEWIDYWANIA. Bilans: 7 na 24

- **`rerank_moved` bedzie wysokie** (ponad polowa pytan) — cross-encoder ocenia inaczej
  niz podobienstwo wektorow, wiec musi sie rozejsc z embeddingiem.
- **`recall@10` wzrosnie**, ale **nie dobije do 34,6%**, bo sufit to 36,6% i wymagaloby
  to przestawienia niemal idealnego.
- **`abstain_neg` bedzie niezerowy** — pierwszy raz cokolwiek odmowi.
- **`abstain_pos` tez bedzie niezerowy** i to bedzie kosztowac `recall`.
- **Kryterium jako calosc NIE zostanie spelnione**, ale `neg/poz` spadnie ponizej 97,7%,
  czyli warunek wartosci dodanej BEDZIE spelniony.

## 2026-08-16T05:42 — M15b WYCOFANY PRZED POMIAREM (warunek uczciwosci zadzialal)

Prerejestracja mowila: prog odmowy to wlasna granica decyzyjna modelu (logit 0 =
sigmoid 0,5), a **jesli karta modelu tego nie potwierdzi, wariant zostaje WYCOFANY,
a nie przestrojony**.

Sprawdzone po kolei:
1. Karta modelu **milczy** o interpretacji wyniku — pokazuje tylko przyklad `+8,6` / `-4,3`.
2. Kod `sentence_transformers` 3.0.1: `nn.Sigmoid() if num_labels == 1 else nn.Identity()`
   — wygladalo na potwierdzenie.
3. **Ale ten model NADPISUJE domyslne zachowanie**:
   `config.sbert_ce_default_activation_function = torch.nn.modules.linear.Identity`.
   Faktycznie uzyta aktywacja: `Identity`. Wyjscie to **surowy logit**.
4. Proba na jawnych parach: pasujaca **-0,95**, niepasujaca **-11,45**. Nawet trafienie
   jest UJEMNE, wiec zero nie jest zadna granica.

**M15b wycofany.** Prog dobrany po zobaczeniu tego rozkladu bylby dokladnie tym,
czego ta metodologia zabrania. M15a (`rerank`, samo przestawianie) nie potrzebuje
granicy bezwzglednej i zostaje.

## 2026-08-16T05:42 — M15a: ODRZUCONY. Przesiewacz przestawia duzo i bezuzytecznie.

Pomiar: `_baseline/m4_rerank_dev_505c48e.json`. Cache: `_desc/rerank_cache.json`,
900 par, `ms-marco-MiniLM-L-6-v2`, zamrozony i zacommitowany.

| | embed_desc | M15a rerank |
|---|---|---|
| recall@10 | 30,0% | **26,6%** |
| recall@25 | 36,6% | 36,6% |
| MRR | 0,243 | 0,229 |
| neg/poz | 97,7% | **NIEMIERZALNE** |

Dwudziesty trzeci pomiar, dwudzieste trzecie odrzucenie.

### WARUNEK DIAGNOSTYCZNY — rozstrzyga jednoznacznie

| pomiar | wartosc |
|---|---|
| `rerank_moved` | **24 z 36** — przesiewacz zmienil symbol na pierwszym miejscu |
| `rerank_promoted` | **0** — ani razu nie wciagnal wlasciwego symbolu z pasma 11-25 do top-10 |
| `rerank_demoted` | 1 — raz wypchnal wlasciwy symbol z top-10 |

**Przestawia agresywnie i bezuzytecznie.** Rozchodzi sie z embeddingiem w dwoch trzecich
pytan, czyli naprawde ocenia po swojemu — i ta ocena jest nieskorelowana z poprawnoscia.
Zero awansow przy 24 przestawieniach to nie jest slaby wynik, to jest **brak sygnalu**.

### TA SAMA WADA MOJEJ PREREJESTRACJI PO RAZ DRUGI

`neg/poz` liczy `srednia_neg * 1000 // srednia_poz`. Przy wynikach UJEMNYCH ta arytmetyka
daje bezsens (-868700%). **Dokladnie to samo zapisalem przy M7** o wariancie `embed_borda`:
*„zadeklarowalem jedno kryterium dla trzech wariantow, nie sprawdzajac, czy skala wyniku
kazdego z nich to kryterium udzwignie"*.

Zapisalem te lekcje i **popelnilem ten sam blad ponownie**. Regula na przyszlosc,
tym razem operacyjna: **przed kazda prerejestracja sprawdzic ZAKRES wyniku wariantu
i jawnie napisac, czy `neg/poz` jest dla niego definiowalne.**

### PRAWIE ZARAPORTOWALEM SUKCES, KTOREGO NIE MA

Surowe srednie wygladaly obiecujaco: `top1` pozytywow **-5623**, negatywow **-8687**.
Czyli model ocenia pytania spoza zakresu o ~3 logity nizej — wygladalo to na pierwszy
prawdziwy sygnal „nie wiem".

Sprawdzenie ROZKLADU, a nie srednich, wywrocilo to:

| | mediana | zakres |
|---|---|---|
| pozytywy | -6160 | -10698 .. **+1779** |
| negatywy | -8987 | -10031 .. **-4932** |

**20 z 30 pozytywow lezy PONIZEJ najwyzszego negatywu.** Prog postawiony gdziekolwiek
odcialby dwie trzecie prawdziwych pytan. Rozklady sie nakladaja, sygnalu nie ma —
ten sam wniosek co w M14 i z tego samego powodu.

Odnotowuje to jako **przestroge metodologiczna**: srednie roznily sie o 3 logity
i gdybym poprzestal na nich, ogloszilbym przelom. Rozklad mowi co innego.

### HIPOTEZA PO FAKCIE (nieweryfikowana, wymagalaby wlasnej prerejestracji)

Mediana oceny to **-9,9 logita** — model uwaza, ze praktycznie NIC nie jest odpowiedzia.
To jest zachowanie modelu daleko poza rozkladem, na ktorym go trenowano: `ms-marco`
uczono na akapitach prozy, a my podajemy mu rozbite identyfikatory plus opis.

Prerejestracja **nazwala to ryzyko i swiadomie je przyjela**, zeby roznica byla
przypisywalna do SEDZIEGO, a nie do materialu. Cena zaplacona, wynik jednoznaczny.

Naturalny nastepny krok: podac przesiewaczowi **sam opis pliku** — czysta proze,
bez identyfikatorow. To jest zmiana MATERIALU, wiec wymaga wlasnej prerejestracji
i jest osobnym eksperymentem, nie poprawka do tego.

### BILANS PRZEWIDYWAN

Trafione: `rerank_moved` wysokie (24 z 36).
Chybione: `recall@10` wzrosnie — **spadlo** z 30,0% na 26,6%.
Nieaktualne: dwa przewidywania o odmowie (wariant wycofany przed pomiarem).

### Regresja i gotcha

`pytest` 215 zielonych, `baseline` 26,6/36,6/0,172/85,2 i `embed_desc` 30,0/36,6/0,243/97,7
odtworzone co do cyfry.

**Gotcha, ktora kosztowala by nas poprawke w AIONS:** hook `checkpoint.py` zamiotl
do HEAD serwery w wersji CELOWO cofnietej na czas pomiaru (commit 3f7f54e
„checkpoint: before edit of rerank.py"). Zweryfikowane: HEAD mial 0 wystapien
`query=user_message`, dysk 1. Naprawione commitem `a3b7568`.

To ten sam mechanizm co gotcha z M0, w nowym wariancie: **hook nie rozroznia
„cofniete tymczasowo" od „tak ma zostac"**. Regula na przyszlosc: po kazdym cyklu
cofnij-zmierz-przywroc sprawdzic `git show HEAD:<plik>`, a nie tylko stan dysku.

## 2026-08-16T06:09 — NARZEDZIE DZIALA. Blokada to JEZYK, nie wyszukiwanie.

### Skad ten pomiar

Marcin, po dwudziestu trzech odrzuceniach: *„przeciez cala rzecz w tym sie zaczela zeby
acae umial zrozumiec ludzka mowe"*. Slusznie — zjechalem w optymalizowanie rankera
i zgubilem cel. Poprosilem go o pytania zadane JEGO slowami. Dal piec i kazal dopisac
reszte z pamieci.

Kazde pytanie zapisane w DWOCH wersjach o tym samym znaczeniu: jego polskiej
i angielskim odpowiedniku. Zbiory: `tests/marcin_pl_questions.json`,
`tests/marcin_en_questions.json`, generator `scripts/make_marcin_questions.py`.

### WYNIK — ranker `embed_desc`, te same pytania, tylko inny jezyk

| | po polsku | po angielsku |
|---|---|---|
| recall@10 | 20,0% | **70,0%** |
| recall@25 | 40,0% | **90,0%** |
| MRR | 0,125 | **0,662** |
| neg/poz | 100,5% | **66,3%** |

Per pytanie, pozycja wlasciwego pliku:

```
m01  gdzie jest mapa lasu                      poza  ->   1
m02  co jest kurwa zawiecha                      15  ->   1
m03  czym sprawdze co mam na dyskach             21  ->   1
m04  sprawdz czy aions dziala                  poza  ->  22
m05  czy jestes podlonczony                    poza  ->   1
m06  czemu mi nie pamieta rozmowy              poza  ->   1
m07  gdzie sie kurwa zapisuja te chunki           7  ->   2
m08  co robi to esperanto                         1  ->   1
m09  czemu mi mowi ze nie wie                  poza  -> poza
m10  gdzie sie sprawdza czy odpowiedz dobra    poza  ->  13
```

**W pierwszej dziesiatce: 2 z 10 po polsku, 7 z 10 po angielsku.
Na PIERWSZYM miejscu: 1 z 10 po polsku, 6 z 10 po angielsku.**

### Naturalny eksperyment wewnatrz danych

`m08` „co robi to esperanto" jest **jedynym polskim pytaniem, ktore dziala** — i jedynym,
ktore zawiera slowo **identyczne w obu jezykach**. To nie jest anegdota, to jest
potwierdzenie mechanizmu z samego zbioru: dziala dokladnie tam, gdzie jezyk przestaje
byc przeszkoda.

### Co to znaczy

**Narzedzie dziala.** Na pytaniach zadanych po ludzku, w jezyku korpusu, wskazuje
wlasciwy plik **na pierwszym miejscu w szesciu przypadkach na dziesiec**, a w dziewieciu
na dziesiec miesci go w pierwszej dwudziestce piatce.

Dwadziescia trzy odrzucenia nie byly pomiarem narzedzia. Byly pomiarem narzedzia
na zbiorze zbudowanym CELOWO tak, zeby bylo trudno — agent mial instrukcje „opisuj
zachowanie, NIE nazywaj symboli". A prawdziwa blokada w codziennym uzyciu lezala gdzie
indziej i **nie zostala zmierzona ani razu przez tydzien**.

### CZEGO TEN POMIAR NIE DOWODZI — trzy rzeczy, wszystkie przeciwko mnie

1. **To nie jest slepa proba.** Klucz odpowiedzi ustalilem ja, znajac korpus.
   Wyniku **NIE WOLNO** wstawiac do tabeli z dev/heldout.
2. **Trafienie liczone na poziomie PLIKU**, nie symbolu — prog znacznie lagodniejszy
   niz w zamrozonym zbiorze. „70%" i „30%" to nie sa te same liczby.
3. **Zbior ma 10 pozytywow.** Jedno pytanie to 10 punktow procentowych.

**Ale porownanie PL vs EN jest czyste**: ten sam zbior, ten sam prog, ten sam ranker,
ten sam klucz — rozni sie WYLACZNIE jezyk pytania. I to porownanie jest cala teza.

### Co z tego wynika na nastepny krok

Blokada jest **tania do usuniecia** w porownaniu ze wszystkim, co probowalismy:
- przetlumaczyc pytanie na angielski przed szukaniem (i zamrozic tlumaczenia, jak wszystko),
- albo dopisac opisy plikow po polsku,
- albo jedno i drugie.

Zadne z tych nie wymaga nowego mechanizmu rankingu. To jest praca na wejsciu, nie
w silniku. **I to jest pierwszy raz w tym projekcie, kiedy wiadomo, co konkretnie
zrobic, zeby bylo lepiej.**

Zamrozony held-out pozostaje **NIETKNIETY** — ten pomiar go nie dotyka.

## Gotcha — agent raportuje dlugosc opisu, ktorej nie napisal

Pierwszy przebieg M8 (przerwany awaria shella) dal 169 opisow, w ktorych KAZDY z szesciu
agentow zaraportowal „descriptions are 100-160 words". Zmierzone: mediana **59 slow**,
165 ze 169 ponizej zamowionego minimum, a jeden „opis" byl notatka agenta do siebie:
`"Stopped at 1 line - file was already read before in batch."` dla realnego pliku serwera.

Samoocena agenta nie jest pomiarem. Kazda partia przechodzi teraz przez
`scripts/build_descriptions.py`, ktory ODMAWIA ZAPISU artefaktu przy: brakach pokrycia,
duplikatach, `UNREADABLE`, meta-tekscie agenta, wyciekach z `tests/` i opisach urwanych.

Przyczyna nie byla w modelu, tylko w dlugosci serii: 28 plikow na agenta (46-49 tur).
Po podziale na 12 partii po ~14 plikow, tym samym modelem i ostrzejsza instrukcja:
mediana **134 slowa**, 154 ze 169 powyzej 100 slow, zero meta-tekstu.
Podzial idzie po BAJTACH, nie po sztukach (`scripts/make_desc_batches.py`) — koszt partii
zalezy od rozmiaru plikow, wiec rowna liczba plikow dawala nierowne obciazenie.
Wersja odrzucona lezy w `_desc/v1_rejected/`.
