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
