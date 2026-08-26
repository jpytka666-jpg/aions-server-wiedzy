# discovery/ — odkrywanie i zapisywanie struktury

Projekt istnieje po to, żeby **przestać odkrywać to samo po raz czwarty**.

Zasada: **git jest źródłem prawdy, baza wektorowa jest indeksem pochodnym.** Bazę można skasować
i odbudować jedną komendą. Zapisu w gicie odbudować się nie da — dlatego ustalenia idą do JSON-a
i Markdowna, a nie do bazy.

---

## Co tu jest

| Plik | Rola |
|---|---|
| `cbms/ARCHITECTURE.md` | trace CBMS do czytania przez człowieka — skąd się wziął, jak działa, co obalono |
| `cbms/findings.json` | te same ustalenia maszynowo, każde ze statusem i dowodem |
| `cbms/measurements.json` | surowy pomiar żywego magazynu, wygenerowany, nie pisany ręcznie |
| `inventory.py` | mierzy żywy magazyn **tylko do odczytu**, produkuje `measurements.json` |
| `ingest.py` | buduje z tego bazę wektorową, w **osobnym** katalogu |

Statusy w `findings.json` są trzy i znaczą dokładnie tyle, ile mówią:

| status | znaczy |
|---|---|
| `CONFIRMED` | odczytane z pliku albo zmierzone 2026-08-26 |
| `REFUTED` | sprawdzone i **nieprawdziwe**; pole `evidence` mówi jak to wykazano |
| `OPEN` | niesprawdzone — **nie cytować jako faktu** |

---

## Uruchomienie

```bash
# 1. pomiar żywego magazynu (nic nie zapisuje w magazynie)
python discovery/inventory.py --memory-dir "<...>/aions_core/memory"

# 2. indeks
python discovery/ingest.py

# 3. pytanie
python discovery/ingest.py --query "co robi bramka zapisu?"
```

Interpreter: venv projektu (`chromadb` 0.5.3 już tam stoi).

---

## Dwie granice, których ten katalog nie przekracza

**1. Nie pisze do żywej bazy.** `ingest.py` ma `refuse_live_store()` i odmawia startu, jeśli katalog
docelowy pokrywa się z `CHROMA_PATH` albo choćby wygląda jak `…/data/chroma`. Dwóch piszących na
tym samym pliku Chromy to uszkodzona baza — i to jest ten konkretny wypadek, któremu zapobiega
dyrygent uruchamiający stos po kolei.

**2. Nie dotyka magazynu CBMS.** `inventory.py` otwiera pliki wyłącznie do odczytu.

Domyślna baza tego projektu: `discovery/.chroma/` — poza gitem, wyrzucalna.

---

## Znane ograniczenie: osadzenia są angielskie

Domyślny model Chromy (`all-MiniLM-L6-v2`, ONNX, w cache lokalnie — działa bez sieci) jest
**anglojęzyczny**, a dokumenty tutaj są po polsku. Widać to na pomiarze: na pytanie
*„czy zastrzyk koreański w Phi-3 naprawdę coś zmienił w wagach?"* właściwa sekcja wyszła
**druga**, nie pierwsza (0,466 wobec 0,444 dla sekcji o warstwach pól).

Trafia w trójkę, więc do użytku wystarcza. Ale to jest sufit, nie cel.

`ingest.py --embed multilingual` jest przygotowane pod
`paraphrase-multilingual-MiniLM-L12-v2` i **dziś nie działa**: model leży w cache HuggingFace
(458 MB blobów), ale bez katalogu `snapshots/`, więc `transformers` go nie rozwiązuje i idzie
do sieci. Naprawa cache albo wskazanie modelu ścieżką lokalną — do zrobienia, nie zrobione.

---

## Dopisywanie ustaleń

1. Nowy wpis w `cbms/findings.json` — z **dowodem**, nie z samą tezą. Bez pola `evidence`
   wpis jest opinią i nie należy tu.
2. Jeśli zmienia obraz całości — akapit w `cbms/ARCHITECTURE.md`.
3. `python discovery/ingest.py` przebudowuje indeks (`upsert`, więc powtórzenie jest bezpieczne).
4. Commit. Baza wektorowa **nie** idzie do repozytorium.

Kolejny obszar dostaje własny podkatalog obok `cbms/`, ten sam kształt: `ARCHITECTURE.md`
+ `findings.json`, i `ingest.py` go podbierze.
