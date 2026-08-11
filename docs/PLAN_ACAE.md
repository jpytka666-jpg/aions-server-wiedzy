# ACAE — plan modułu

**Status:** PLAN v3. Zero zmian na dysku poza tym dokumentem. Zero kodu.
**Data:** 2026-08-11
**Zastępuje:** PLAN v2 (2026-08-10)
**Relacje:** zgodny z ADR-002 · konsumuje `PLAN_SERENA_TO_CBMS.md` §3A–C · nie realizuje ACAE-spec §15–16 (IR/translacja — wycięte)
**Ograniczenia wejściowe:** (A) działa z obecnym AIONS-Context MCP jako moduł · (B) projektowany pod migrację do Rusta wg ADR-002

## Zmiana wobec v2 — cztery rozstrzygnięcia i trzy korekty faktograficzne

| # | v2 mówił | v3 mówi | Powód |
|---|---|---|---|
| D1 | tree-sitter = **NEW** | tree-sitter = **REUSE**, ACAE konsumuje `ts_symbols.py` | plik istnieje w repo od 2026-08-08, 381 linii, robi outline+drill+drift (§2) |
| D2 | BLAKE3 „za modelem Block §4.2" | **BLAKE2b-256 ze stdlib**, prefiks `b2b256:` | ADR-002 nie wymienia BLAKE3 ani razu; w repo nie ma żadnego blake; `blake3` niezainstalowany (§6) |
| D3 | „zmierzyć koszt wprowadzenia modelu", ±5% | zamrożony **zbiór plików odpowiedzi** na zapytanie, model poza pętlą, ±0% | z modelem w pętli pomiar jest nieodtwarzalny z definicji (§11 M0) |
| D4 | root `D:/AIONS_DEV/repo/server-wiedzy`, kod w `D:\acae\` | root `E:\server wiedzy`, kod w `E:\server wiedzy\acae\` | kopia na D: nie ma `.git`, stoi od 11 lipca; E: jest żywe (§1.1, §8) |
| K1 | „REUSE ALGORYTMU — nie wybierać drugiego" | przesłanka **fałszywa** — nie ma czego reużywać | `grep -rn "blake3\|BLAKE3\|blake2"` po repo → 0 trafień |
| K2 | ADR-002 §4.2 definiuje `content_hash` | `content_hash` jest w **§4.1**; §4.2 to niezmienniki I1–I9 | odczyt ADR-002 |
| K3 | R2 „nieznana liczba bloków CBMS" — nieaktualne | nieaktualne **z innego powodu**: rozjazd repozytoriów jest większym ryzykiem (§1.1) | recon |

---

## 0. Terminologia — obowiązująca, jedno znaczenie na termin

Do `TERMS.md`. Kontrola w `cbms_doctor.py`: termin użyty, ale niezarejestrowany → wpis do raportu.

| Termin | Znaczy dokładnie to | Nie znaczy |
|---|---|---|
| **ACAE** | silnik: pakowanie, ekstrakcja, dopasowanie, składanie | magazyn, format, baza |
| **pack** | wynik pakowania: jeden plik na dysku | kontekst w oknie modelu |
| **manifest** | metadane packa | treść |
| **component** | rekord w **magazynie ACAE**, adresowany treścią | chunk CBMS, blok pamięci |
| **symbol** | jednostka składniowa z tree-sittera: funkcja, klasa, metoda | komponent |
| **name_path** | adres logiczny symbolu (`Klasa/metoda`) — termin z `ts_symbols.py`, przejęty bez zmian | ścieżka pliku |
| **outline** | szkielet: sygnatury bez ciał | streszczenie |
| **provides[] / requires[]** | co komponent daje / czego wymaga | uprawnienie |
| **capability** | uprawnienie w kernelu (K4, ADR-002 §3.2) | co kod potrafi |
| **codebook** | koreański indeks symboliczny (`kr_postings.bin`) | **zarezerwowane — nie używać** |
| **chunk** | jednostka CBMS (wiedza prozą) | komponent, symbol |

`Codebook` z pierwotnej specyfikacji ACAE — **wycofane** (kolizja).

Korekta wobec v2: w tabeli terminów było „capability — uprawnienie w kernelu (K10, Z2)". ADR-002 ma zasady **K1–K9**, nie K10, i nie zna oznaczenia „Z2". Właściwe odniesienie to **K4** (brak ambient authority) i §3.2 (granica kernela).

---

## 1. Recon — co już istnieje

Wykonany 2026-08-10/11 na żywym systemie. Każdy werdykt ma dowód.

| Zdolność | Stan | Werdykt |
|---|---|---|
| Lokalizacja plików | `fast_search` (Everything) | **REUSE** — wymaga filtra kandydatów |
| Skan projektu | `project_scan_turbo`, `project_scan_status`, `project_scan_results` | **WRAP** |
| Zależności pliku | `project_file_deps` | **WRAP** |
| **Parsowanie tree-sitter** | **`aions_core/server/ts_symbols.py`, 381 linii, commit `06fdfe2` (2026-08-08)** | **REUSE — nie budować drugi raz (§2)** |
| Outline-then-drill | `aions_core/server/cbms_outline.py`, commit `06fdfe2` | **WZORZEC DO PRZEJĘCIA**, ale dla chunków, nie dla kodu |
| Hash treści | **brak jakiegokolwiek** | **NEW — wybór w §6** |
| Kształt prowenancji | ADR-002 §4.1: `{source, job, tool, trust_tier}` | **REUSE KSZTAŁTU** |
| Magazyn komponentów | brak | **NEW — własny, §1.2** |
| Rozumienie kodu (LSP) | brak, świadomie odrzucone 2026-08-08 | **DO NOT BUILD** |
| Pakowanie repo → jeden plik | brak | **NEW** |
| Rejestr `provides` | brak | **NEW** |
| Sandbox kompilacji | brak | **NEW**, późno |

**Dowody:**

- **Szum Everything:** `fast_search("ACAE")` → 30 trafień, **0 z repo AIONS**. Zwrócone: `C:\Windows\WinSxS\…`, `C:\Users\User\AppData\Local\npm-cache\…`, `C:\Users\User\iCloudPhotos\Photos\1509cfae-….mp4`, `D:\AIONS_DEV\cache\pip\…`. Trafienia to fragmenty sum SHA-512 zawierające podciąg „acae". Lokalizator bez filtra jest dla ACAE bezużyteczny.
- **Rozsyp dokumentów:** `fast_search("ADR-002")` → 6 trafień, z czego **5 to kopie tego samego pliku** (`… (1).md`, `(2)`, `(3)`, `(4)` w `E:\szul\DOWNLOAD`).
- **Brak hasha:** `grep -rn "blake3\|BLAKE3\|blake2"` po `aions_core/` → 0 trafień. `import blake3` → `ModuleNotFoundError` w każdym sprawdzonym interpreterze (system 3.13.14, venv 3.11.9).
- **Tree-sitter działa:** `tree_sitter_language_pack` importuje się w `E:\server wiedzy\venv` (Python 3.11.9). W systemowym 3.13 — brak.
- **Liczniki tokenów:** `tiktoken` obecny w systemowym 3.13, brak w venv 3.11.
- **Objętość celu:** `aions_core` = 65 plików `.py` / 754 240 bajtów. Reszta repo: `control_plane` 42, `scripts` 39, `tools` 30, `mcpServers` 12, `server` 8.

### 1.1 Trzy kopie repozytorium — ryzyko wyższe niż cokolwiek w v2

Recon ujawnił rzecz, której v2 nie zna i która zmienia znaczenie słowa „root":

| Kopia | HEAD / data | Zawiera `aions_core/`? | Status |
|---|---|---|---|
| `E:\server wiedzy` | `06fdfe2`, **2026-08-08** | tak — 65 plików `.py` | **żywa, jedyna prawdziwa** |
| `D:\AIONS_DEV\repo\server-wiedzy` | **brak `.git`**, pliki z 11 lipca | tak, ale stara | martwa kopia — do skasowania |
| GitHub `jpytka666-jpg/aions-server-wiedzy` | `1614f00`, **2025-12-15** | **nie — katalogu nie ma w ogóle** | ~8 miesięcy w tyle |

Dowód rozjazdu z GitHubem: `git cat-file -t 06fdfe2` w klonie zdalnym → `fatal: Not a valid object name`. Commit wnoszący `ts_symbols.py`, `cbms_outline.py`, `refgraph.py`, `cbms_purgatory.py`, `cbms_doctor.py` (2301 linii) **nie istnieje** w repozytorium zdalnym. Zdalne ma 20 plików `.py`; E: ma ponad 190.

**Konsekwencja dla ACAE, wprost:** ten dokument leży w repozytorium zdalnym, bo tylko tam mogę pisać. Kod, który opisuje, żyje na E:. Dopóki E: nie zostanie wypchnięte, plan i przedmiot planu są w dwóch różnych miejscach.

To jest **warunek wejścia do M0**, nie uwaga na marginesie: pomiar bazowy odnosi się do konkretnego commita (§11 M0), a commit musi istnieć tam, gdzie pomiar będzie powtarzany. Synchronizacja E: → GitHub jest osobną decyzją Marcina i osobnym ryzykiem (`.gitignore` na E: wycina `aions_core/memory/`, `runtime/secrets/`, `_measure/` — wypchnięcie „wszystkiego" wypchnęłoby też to, czego wypychać nie wolno). **ACAE tej decyzji nie podejmuje i od niej nie zależy** — pracuje na E: lokalnie. Zależy od niej wyłącznie powtarzalność pomiaru między maszynami.

### 1.2 Dlaczego własny magazyn, a nie CBMS

Zamknięta decyzja *„jeden Memory Engine, cztery indeksy nad jednym magazynem"* broni przed konkretną patologią: **jedna dziedzina rozbita na cztery magazyny** — Chroma ‖ codebook ‖ graf ‖ CBMS, cztery ścieżki zapisu, cztery liczenia score'a, brak wspólnej tożsamości.

Komponenty kodu to inna dziedzina:

| | chunk CBMS | component ACAE |
|---|---|---|
| Treść | wiedza prozą | kod źródłowy |
| Cykl życia | `salience`, `decay`, `access_count` | `DISCOVERED→…→VERIFIED`, unieważniany hashem toolchaina |
| Zapytanie | recall semantyczny, top-K | dokładne dopasowanie `provides` + lookup po hashu |
| Autorytet | model + prowenancja | wykonany dowód (kompilacja, testy) |

Osobny magazyn dla **innej klasy danych** nie jest tą samą chorobą co cztery magazyny jednej klasy.

Argument rozstrzygający jest operacyjny: CBMS jest w stanie, którego nikt nie umie zmierzyć — ADR-002 §4.6 stawia `C8` (liczność zgodna z pełnym skanem) jako test rozstrzygający rozbieżność **617 vs 445**, a odczyty w kolejnych sesjach dawały 613 → 457 → 159 → 167. Wpięcie nowego modułu w ten punkt oznacza, że ACAE dziedziczy każdą z tych awarii. Zgodnie z zasadą *leaf nodes najpierw* — ACAE jest liściem i ma nim zostać.

**Dwa warunki, tanie teraz, drogie później:**

1. Ta sama funkcja tożsamości (§6) i ten sam kształt prowenancji co w modelu Block (ADR-002 §4.1). Nie dla współdzielenia magazynu — po to, by ewentualny most kosztował zero zamiast migracji.
2. Referencje **jednokierunkowe**: chunk CBMS może wskazać komponent po `content_hash`. Nigdy scalanie w drugą stronę. To jest szew, nie sprzężenie.

**Trzeci warunek, dodany w v3 po decyzji D1:** ACAE czyta z `ts_symbols.py` wyłącznie `outline()` i `get()`. **Nie wywołuje `as_chunk_candidates()`.** Ta metoda produkuje rekordy z polami `concept: "code_symbol"`, `provenance: "parsed"`, `id: "KTS…"` — czyli wlewa kod do CBMS jako chunki. To jest dokładnie ten kocioł, którego ma nie być: kod i wiedza prozą w jednym worku, z jednym schematem i jednym recallem. Ta ścieżka zostaje własnością CBMS i ACAE jej nie dotyka.

---

## 2. Tree-sitter — z NEW na REUSE

v2 klasyfikował parsowanie jako `NEW` i planował spike „policzyć pokrycie gramatyk" w M1. Recon to unieważnia.

**`aions_core/server/ts_symbols.py` (commit `06fdfe2`, 2026-08-08, 381 linii) już dostarcza:**

| Zdolność | Interfejs | Uwaga |
|---|---|---|
| Parsowanie pliku → symbole | `SymbolIndex.from_file(path)` | przez `tree_sitter_language_pack` |
| Outline bez ciał | `.outline()` → `[{name_path, kind, line, lines, signature, body_hash, n_refs}]` | dokładnie wejście dla `manifest.files[].symbols[]` |
| Drill pojedynczego symbolu | `.get(name_path)` → `Symbol` z `.body` | miękkie dopasowanie po sufiksie |
| Wykrycie dryfu | `.drift(previous)` → `{added, removed, changed, unchanged}` | bez reparsowania całości |
| Skan katalogu | `scan_dir(root)` | ma własną listę `skip` |
| Mapa języków | `LANGS` — **19 rozszerzeń** | `.py .js .jsx .ts .tsx .go .rs .java .c .h .cpp .hpp .rb .php .cs .sh .lua .kt .swift` |

**Werdykt:** ACAE nie pisze drugiego parsera. Port `Parser` (§3) jest adapterem nad `SymbolIndex`.

**Co ACAE musi dołożyć, i tylko to:**

1. **Determinizm kolejności.** `scan_dir()` iteruje `os.walk` i zwraca `dict` w kolejności systemu plików. §5 pkt 1 tego zabrania. Adapter sortuje.
2. **Własny hash.** `ts_symbols.sha12()` to **SHA-1 obcięty do 12 znaków heksowych = 48 bitów**. To jest w porządku jako detektor dryfu (do tego został napisany) i nie nadaje się na funkcję tożsamości magazynu adresowanego treścią — przy 48 bitach kolizja urodzinowa staje się prawdopodobna w rzędzie 10⁷ obiektów. ACAE liczy własny `content_hash` wg §6 i **nie nadpisuje** `body_hash`; oba współistnieją, każdy do swojego zadania.
3. **Obsługa braku gramatyki.** `from_file()` rzuca `ValueError` dla nieznanego rozszerzenia, a `scan_dir()` łyka to `except`-em i **milcząco pomija plik**. ACAE potrzebuje tego jawnie: `skipped: [{path, reason: "no_grammar"}]` w manifeście. Ciche pominięcie w narzędziu, którego produktem jest kompletność, jest wadą.
4. **Ignore.** `scan_dir()` ma zaszytą listę `skip`; ACAE czyta `.gitignore` + `.acaeignore` (§8).

**Dlaczego to nadal nie jest LSP.** `PLAN_SERENA_TO_CBMS.md` §7 odrzuca warstwę LSP: *„lata pracy społeczności. Tree-sitter daje 80% za 5% kosztu"*. Decyzja zostaje w mocy — i jest już wykonana, bo `ts_symbols.py` to właśnie ten wybór zmaterializowany.

| | tree-sitter | LSP |
|---|---|---|
| Co daje | strukturę składniową **jednego pliku** | rozstrzyganie semantyczne **między plikami** |
| Czego wymaga | jedna biblioteka + gramatyki | serwer językowy na każdy język, uruchomiony |
| Stan | bezstanowy | stanowy, długożyjący |
| Determinizm | ten sam plik → to samo drzewo, zawsze | zależny od stanu serwera i timingu |
| Rust | natywne wiązania, gramatyki jako crate'y | nadzór nad obcymi procesami |

**Konsekwencja migracyjna:** przy przepisaniu do Rusta przepisywany jest adapter, nie parser. `tree-sitter` ma natywne wiązania Rusta; gramatyki są crate'ami.

---

## 3. Granice modułu — cztery porty i rdzeń

Rdzeń ACAE jest **czystą funkcją**. Całe I/O za wąskimi portami. To jedyny mechanizm czyniący migrację do Rusta podmianą, a nie przepisaniem.

```
                    ┌───────────────────────────┐
   PackRequest ────▶│      ACAE CORE            │────▶ PackManifest
   (deterministic)  │  czysta funkcja, bez I/O  │      (+ pack na dysku)
                    └───────────┬───────────────┘
                                │
          ┌──────────────┬──────┴───────┬──────────────┐
          ▼              ▼              ▼              ▼
    ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐
    │ Locator   │  │  Reader   │  │  Parser   │  │  Store    │
    └───────────┘  └───────────┘  └───────────┘  └───────────┘
     Everything     filesystem     ts_symbols     magazyn ACAE
     (fast_search)  (+ ignore)     (adapter)      (własny)
```

```
Locator.find(roots[], patterns[], excludes[])  -> [PathCandidate]   # posortowane
Reader.read(path)                              -> Bytes | NotFound
Reader.stat(path)                              -> {size, mtime}     # mtime NIE wchodzi do hasha
Parser.outline(path, bytes)                    -> [SymbolRow] | NoGrammar
Parser.body(path, bytes, name_path)            -> Bytes | NotFound
Store.put(Component)                           -> ComponentId       # = content_hash
Store.get(ComponentId)                         -> Component
Store.find(provides[], constraints)            -> [ComponentId]
```

Port `Parser` jest nowy wobec v2 — wynika z D1. Rdzeń nie zna Everything, nie zna tree-sittera, nie zna CBMS, nie zna MCP.

**Test granicy:** rdzeń musi się uruchomić na sztucznym `Reader` i sztucznym `Parser` w pamięci, bez dysku i bez serwera. Jeśli się nie da — granica jest w złym miejscu.

**Magazyn ACAE w M3:** SQLite + katalog blobów adresowany treścią. Embedded, zero demonów, jeden plik do backupu. Nie przesądza ADR-003 — jest lokalny dla ACAE, nie dla pamięci systemu.

---

## 4. Format wyjściowy `acae.pack.v1` — właściwy kontrakt migracji

Format, nie kod, jest umową między implementacją Pythona a przyszłą implementacją Rusta.

```
pack/
  manifest.json        # acae.pack.v1 — kanoniczny JSON
  content.txt          # treść: outline lub pełna
```

```json
{
  "schema": "acae.pack.v1",
  "pack_hash": "b2b256:...",
  "roots": ["E:/server wiedzy"],
  "mode": "outline",
  "generated_by": "acae-py/0.1.0",
  "counts": { "files": 412, "symbols": 3907, "tokens": 68231, "bytes": 2914003 },
  "files": [
    {
      "path": "aions_core/server/ts_symbols.py",
      "content_hash": "b2b256:...",
      "language": "python",
      "tokens": 1841,
      "symbols": [
        { "kind": "class", "name_path": "SymbolIndex", "line": 96,
          "signature": "class SymbolIndex:" },
        { "kind": "function", "name_path": "SymbolIndex/from_file", "line": 105,
          "signature": "def from_file(cls, path: str) -> \"SymbolIndex\"" }
      ]
    }
  ],
  "skipped": [ { "path": "...", "reason": "ignored|binary|too_large|secret|no_grammar" } ]
}
```

Zmiany wobec v2: prefiks hasha `b2b256:` (§6); `name` → `name_path` (zgodność z `ts_symbols.py`, §0); root przykładowy poprawiony na E:.

**Bramka migracji Python → Rust:**

> Dla tego samego wejścia i konfiguracji implementacja Rusta produkuje **bajt w bajt identyczny** `content.txt` i identyczny `manifest.json` po pominięciu `generated_by`.

---

## 5. Determinizm — reguły twarde

1. **Kolejność:** sortowanie po ścieżce POSIX, porównanie bajtowe, locale ignorowane. Nigdy kolejność z systemu plików. *(Dotyczy w szczególności adaptera nad `scan_dir()` — §2 pkt 1.)*
2. **Ścieżki:** w manifeście POSIX, względne wobec roota. Windows `\` normalizowane na wejściu.
3. **Hash:** wg §6. Wejściem **wyłącznie treść**. Nigdy mtime, ścieżka absolutna, timestamp.
4. **JSON kanoniczny:** klucze sortowane, bez nadmiarowych spacji, bez floatów, UTF-8 bez BOM, `\n`.
5. **Metadane osobno od tożsamości:** `generated_by`, czasy, statystyki nie wchodzą do `pack_hash`.
6. **Równoległość:** wolno czytać równolegle, składać wynik wyłącznie w kolejności z pkt 1.
7. **Dekodowanie:** UTF-8 z `errors="replace"` — tak jak `ts_symbols.py`. Ta sama sekwencja bajtów musi dać ten sam tekst na obu implementacjach; `replace` jest deterministyczny, `strict` rzuciłby wyjątkiem na pierwszym pliku z `latin-1`.

**Test:** ten sam pack liczony dwa razy w odstępie doby → identyczny `pack_hash`. Test regresyjny w CI.

---

## 6. Tożsamość treści — BLAKE2b-256 (decyzja D2)

v2 zakładał BLAKE3 „za modelem Block §4.2". Recon obala obie części tego zdania:

- ADR-002 **§4.2** to niezmienniki I1–I9. `content_hash` jest w **§4.1** i mówi wyłącznie: *„funkcja czysta od `content`; podstawa idempotencji"*. **BLAKE3 nie pada w ADR-002 ani razu.**
- W repo nie ma żadnej implementacji blake (grep czysty). Instrukcja v2 „REUSE ALGORYTMU — nie wybierać drugiego" opiera się na algorytmie, którego nie ma. **ACAE ustanawia go jako pierwszy**, więc wybór trzeba uzasadnić, a nie odziedziczyć.

**Decyzja: `hashlib.blake2b(content, digest_size=32)`, zapis z prefiksem `b2b256:`.**

| Kryterium | BLAKE2b-256 | BLAKE3 |
|---|---|---|
| Zależność w Pythonie | **stdlib** (`hashlib`, od 3.6) | `pip install blake3` — dziś nieobecny w żadnym interpreterze |
| Implementacja w Ruście | crate `blake2` (RustCrypto), czysty Rust | crate `blake3`, oficjalny |
| Determinizm cross-language | tak | tak |
| Bezpieczeństwo dla adresowania treścią | równoważne | równoważne |
| Przewaga | brak instalacji, M0/M1 startuje bez `pip` | równoległość na plikach wielo-MB |

Przewaga BLAKE3 to przepustowość na dużych plikach dzięki drzewiastej równoległości. ACAE hashuje **pliki źródłowe rzędu kilku–kilkudziesięciu KB**; przy tej wielkości różnica jest nieistotna wobec kosztu odczytu z dysku i parsowania. Kupowanie jej nową zależnością w module, którego pierwszą bramką jest „uruchamia się", jest złym handlem.

**Zasady użycia — normatywne:**

1. Prefiks `b2b256:` jest **częścią wartości**, nie ozdobą. Hash bez prefiksu nie jest poprawnym `ComponentId`. To czyni ewentualną zmianę algorytmu wykrywalną, a nie cichą.
2. Jedna funkcja, jedno miejsce w kodzie. Ten sam algorytm dla `content_hash` pliku, `content_hash` komponentu i `pack_hash`.
3. `ts_symbols.body_hash` (SHA-1/48b) **zostaje nietknięty** i zachowuje swoje zastosowanie: wykrywanie dryfu. Nie jest tożsamością i nie wolno go w tej roli użyć.
4. Jeśli kiedykolwiek pojawi się most do modelu Block, to **ADR-003 przyjmuje `b2b256:`**, albo most jawnie deklaruje konwersję. Nie ma trzeciej opcji „jakoś się dogadają".

---

## 7. Integracja z AIONS-Context MCP (ograniczenie A)

Serwer: FastMCP, stdio-only, ~85 narzędzi. ADR-002 §3.5 nazywa to wprost: narzędzie ma przestać być API systemu i stać się szczegółem implementacyjnym usługi. ACAE **nie dokłada dziesięciu**.

**Dwa narzędzia w M1:**

| Narzędzie | Zwraca |
|---|---|
| `acae_pack(roots, mode, profile)` | `{pack_id, path, counts, pack_hash}` — **metadane, nie treść** |
| `acae_pack_status(pack_id)` | stan + statystyki |

**Reguła krytyczna: pack nigdy nie wraca przez MCP do okna kontekstu.** Pack ma 60–200k tokenów; wciągnięcie go do odpowiedzi jest dokładnie tym problemem, który ACAE ma leczyć. Narzędzie zwraca **ścieżkę**.

Omija to też zmierzony defekt transportu: refy `OFF_*` wygasają w ~60–90 s (`OFF_d0659a47` przepadł po 75 s; ten sam wzorzec pobrany po 1 s zadziałał). Plik na dysku nie wygasa.

**Model asynchroniczny od M1.** Dowód konieczności: `git_status` bez argumentów → `MCP error -32001: Request timed out`. Skoro odpytanie gita przekracza limit, skan repo i kompilacja przekroczą go zawsze. `acae_pack` startuje zadanie i zwraca `pack_id`; `acae_pack_status` odpytuje.

---

## 8. Gdzie mieszka ACAE (decyzje D1 + D4)

v2: „`D:\acae\` jako osobny projekt". Odrzucone — D: jest kopią bez `.git` stojącą od 11 lipca i idzie do skasowania.

**Rozstrzygnięcie: ACAE mieszka wewnątrz żywego repo, we własnym katalogu.**

```
E:\server wiedzy\
├── acae\                       ← ACAE, cały kod modułu
│   ├── src\{core,ports,pack,cli}.py
│   ├── src\adapters\ts_adapter.py    ← jedyny punkt styku z ts_symbols.py
│   ├── config\acae.toml              ← rooty, profile, wykluczenia
│   ├── tests\
│   └── store\                        ← magazyn (M3), GITIGNOROWANY
├── aions_core\server\ts_symbols.py   ← czytany, nietykany
└── mcpServers\VS_CODE_MCP_CODEX\src\
    └── acae_tools.py                 ← adapter MCP, 2 narzędzia
```

Dlaczego wewnątrz, a nie obok — to jest odpowiedź na „podpięty pod AIONS, ale żeby się kocioł nie robił":

| Wymóg | Jak spełniony |
|---|---|
| podpięty pod AIONS | jedno repo, jedna historia gita, jeden `git status`; brak czwartej kopii (§1.1) |
| bez kotła z innymi blokami | własny katalog · własny magazyn · **zero zapisu do CBMS** · zero importów z `cbms_*` |
| liść, nie węzeł | zależność jednokierunkowa: ACAE → `ts_symbols`. Nic w AIONS nie importuje ACAE poza `acae_tools.py` |
| odwracalny | rollback = skasuj `acae/` + usuń 2 linijki rejestracji. AIONS wraca do stanu sprzed |

**Adapter MCP nie trafia do `cbms_memory.py`** — to udokumentowany SPOF. Trafia do osobnego `acae_tools.py`, rejestrowanego w `server.py` dwiema linijkami.

**Magazyn w `.gitignore`.** `acae/store/` jest w całości odtwarzalny z packów (bramka M3) — to dane wyprowadzane w rozumieniu ADR-002 §4.1, a nie źródło prawdy. Do `.gitignore` idzie `acae/store/` i `acae/packs/`.

---

## 9. Ścieżka Python → Rust (ograniczenie B)

| Warstwa | Teraz | Docelowo | Kryterium ADR-002 §6.3 |
|---|---|---|---|
| Porty (kontrakt) | protokoły Pythona | traity Rusta | definicja, nie kod |
| Rdzeń: traversal, hash, kanonizacja | Python | **Rust** | ścieżka gorąca + klasa błędu usuwalna typami |
| Parsowanie | adapter nad `ts_symbols.py` | crate `tree-sitter` | przepisywany **adapter**, nie parser |
| Hash | `hashlib.blake2b` (stdlib) | crate `blake2` (RustCrypto) | ten sam algorytm po obu stronach (§6) |
| Magazyn | SQLite + blobs | redb lub SQLite | — |
| Adapter MCP | `acae_tools.py` | fasada brzegowa | ADR-002 §3.5 |
| Profile, konfiguracja | TOML | ten sam plik | — |

Przepisanie uzasadnione tym, że kanonizacja i hashowanie to ta sama klasa błędu co `_distance_to_similarity` z ADR-002 §4.4 — cicha, bez sygnału, usuwalna typami.

**Czego nie przepisujemy:** gramatyk, profili, formatu, `ts_symbols.py`.

---

## 10. Hooks i dowód

Trzy hooki w `C:\Users\User\.claude\hooks\` — przeczytane, obowiązują:

- **`guard_write.py`** (PreToolUse na Write|Edit) — blokuje ścieżki absolutne. Regex `["'][A-Za-z]:[\\/]{1,2}(?:Users|server|Program Files|ProgramData)` **złapie literał `"E:\server wiedzy…"`** w każdym pliku `.py`/`.toml`/`.sh`. Rooty i profile muszą iść z `config/acae.toml` przez `os.getenv`/parser — to nie jest zalecenie, to jest mechanicznie egzekwowane.
  *Uwaga z reconu:* `aions_core/server/cbms_outline.py` linia 48 ma `BASE = r"E:\server wiedzy\aions_core\memory"`. Ten plik nie przeszedłby dziś przez własny hook projektu. ACAE nie powtarza tego wzorca.
- **`proof_gate.py`** (Stop hook) — deklaracja ukończenia bez dowodu wykonania jest blokowana; wymagany blok `DOWOD | komenda | exit | output | sprawdzone` albo jawne `NIEZWERYFIKOWANE:`. Cykl życia komponentu **jest** tym samym proof gate'em przeniesionym do danych: `VERIFIED` bez zapisanego dowodu (komenda, wyjście, kod wyjścia, hash toolchaina) to naruszenie kontraktu.
- **`checkpoint.py`** — `git status` przed i po każdym milestonie, wpis do `.now/STATE.md`. `.now/CONTRACT.md` zakładany na starcie M0, czytany ponownie na wejściu do każdego milestone'u.

---

## 11. Milestone'y

Każdy: cel · zakres · bramka mierzalna · warunek porażki · rollback.

### M0 — Kontrakt i pomiar bazowy

**Cel:** wiedzieć, względem czego mierzyć.
**Pliki:** `acae/.now/CONTRACT.md`, `acae/TERMS.md`, `acae/config/acae.toml`, `acae/tests/queries.json`, `acae/scripts/measure_baseline.py`

**Jak mierzymy — decyzja D3, model poza pętlą.**

v2 chciał zmierzyć „ile tokenów zajmuje wprowadzenie modelu w repo obecnymi narzędziami" z powtarzalnością ±5%. To jest nieosiągalne z definicji: model przy każdym przebiegu wybierze inne pliki, w innej kolejności, po innej liczbie prób. Mierzylibyśmy wariancję modelu, nie koszt narzędzi.

Zamiast tego mierzymy **koszt ścieżki naiwnej**, czyli to, co faktycznie dzieje się dzisiaj: żeby odpowiedzieć na pytanie o kod, czyta się pliki w całości.

```json
{
  "id": "Q01",
  "question": "Gdzie CBMS konwertuje odległość na podobieństwo i dla jakiej metryki?",
  "answer_files": ["aions_core/server/cbms_memory.py", "server/store.py"],
  "required_symbols": ["_distance_to_similarity"],
  "frozen_at": "2026-08-11",
  "frozen_head": "06fdfe2"
}
```

- `answer_files` — pliki, bez których poprawna odpowiedź nie istnieje. Wybrane **raz, ręcznie**, zamrożone w repo.
- `baseline_tokens(Q)` = suma tokenów pełnej treści `answer_files`.
- `acae_tokens(Q)` = tokeny outline'u pokrywającego te same pliki (M1) lub outline + drill (M2).
- `redukcja(Q) = 1 − acae_tokens / baseline_tokens`.

**Dlaczego to jest powtarzalne co do bitu:** ta sama treść → ten sam licznik → **±0%**, nie ±5%. Treść pobierana przez `git show <frozen_head>:<path>`, więc pomiar nie dryfuje, gdy repo idzie do przodu.

**Zabezpieczenie przed oszukaniem bramki:** redukcję o 90% da się osiągnąć zwracając pusty outline. Dlatego `required_symbols` jest polem obowiązkowym: outline musi zawierać sygnaturę **każdego** wymienionego symbolu, inaczej zapytanie liczy się jako **niezaliczone**, niezależnie od liczby tokenów. Redukcja bez pokrycia nie jest redukcją, tylko utratą informacji.

**Licznik tokenów:** `tiktoken`, kodowanie `cl100k_base`. To tokenizer OpenAI, nie Claude'a — **liczba bezwzględna nie jest prognozą rachunku za API**. Do mierzenia *stosunku* przed/po jest w pełni wystarczający, bo ten sam licznik stoi po obu stronach. Zapisać to w `CONTRACT.md`, żeby liczba nie zaczęła później żyć własnym życiem. `tiktoken` jest obecny w systemowym Pythonie 3.13; w venv 3.11 wymaga instalacji — do rozstrzygnięcia w M0, który interpreter jest interpreterem ACAE (venv ma `tree_sitter_language_pack`, system ma `tiktoken`; **żaden nie ma obu**).

**Bramka M0:**
- 10 zapytań zamrożonych w `queries.json`, każde z `answer_files`, `required_symbols`, `frozen_head`
- `measure_baseline.py` przebiega dwa razy → **identyczne liczby** (nie ±5%, dokładnie identyczne)
- liczba bazowa zapisana w `CONTRACT.md`
- rozstrzygnięty interpreter ACAE, z obiema zależnościami dostępnymi
- **warunek wejścia:** `frozen_head` wskazuje commit osiągalny tam, gdzie pomiar będzie powtarzany (§1.1)

**Porażka:** dwa przebiegi dają różne liczby → błąd w liczniku, nie w metodzie.
**Rollback:** n/d (tylko odczyt).

### M1 — `acae_pack`, tryb outline

**Cel:** deterministyczny pack repozytorium, sygnatury bez ciał.
**Pliki:** `acae/src/{core,ports,pack,cli}.py`, `acae/src/adapters/ts_adapter.py`, `acae/tests/`, `mcpServers/…/acae_tools.py`

**Zakres:** traversal + ignore (`.gitignore`, `.acaeignore`) + wykrycie języka + **adapter nad `ts_symbols.py`** + liczenie tokenów + skan sekretów + zapis packa + 2 narzędzia MCP.

Zakres **zmniejszony** wobec v2 o pisanie parsera i o spike „pokrycie gramatyk" — `LANGS` w `ts_symbols.py` daje 19 rozszerzeń, pokrycie jest znane (§2).

**Bramka:**
- identyczny `pack_hash` przy dwóch uruchomieniach w odstępie ≥24 h
- redukcja tokenów **≥50%** wobec bazy z M0, przy **100% pokryciu `required_symbols`**
- CLI działa bez serwera MCP: `python -m acae pack --root ...`
- rdzeń przechodzi testy na `Reader` i `Parser` w pamięci, bez dysku
- zero sekretów w packu na zestawie kontrolnym
- `E:\server wiedzy` spakowane w < 60 s
- plik bez gramatyki → wpis w `skipped`, pack się nie wysypuje

**Porażka:** niedeterminizm hasha · pack wracający do kontekstu przez MCP · przekroczony czas · pokrycie `required_symbols` < 100%.
**Rollback:** usunąć rejestrację 2 narzędzi, skasować `acae/`. AIONS nietknięty.

### M2 — Drill-down

**Cel:** dociąganie ciał wyłącznie dla wskazanych symboli.
**Zakres:** `acae_fetch(pack_id, symbol_refs[])`, mapowane na `SymbolIndex.get(name_path)`. Wzorzec *overview-then-drill* z `PLAN_SERENA_TO_CBMS.md` §B.1 — ten sam, który `cbms_outline.py` realizuje dla chunków.
**Bramka:** ścieżka outline→fetch zużywa mniej tokenów niż pełny odczyt na ≥8 z 10 zapytań z M0, przy pełnym pokryciu `required_symbols`.
**Porażka:** model częściej prosi o pełne pliki niż o symbole → outline za ubogi, wracamy do M1.
**Rollback:** wyłączyć narzędzie.

### M3 — Magazyn komponentów (własny)

**Cel:** komponent jako trwały, adresowany treścią rekord ACAE.
**Zakres:** SQLite + blobs pod `acae/store/` (gitignorowane). Ekstrakcja komponentów z packa, `content_hash` wg §6, prowenancja w kształcie ADR-002 §4.1. Cykl życia **tylko** `DISCOVERED` → `PARSED`.
**Bramka:** zapis/odczyt przez port Store · deduplikacja po hashu działa · liczba komponentów przed/po zgadza się co do jednego · **magazyn odtwarzalny z packów** (skasuj i przelicz → identyczny stan).
**Porażka:** magazyn niedeterministyczny przy odbudowie.
**Rollback:** skasować `acae/store/`. Zero wpływu na AIONS.

Bramka odbudowy jest lokalnym odpowiednikiem `C4` z ADR-002 §4.6 — testu „czy da się wymienić silnik".

### M4 — `provides[]` / `requires[]`

**Cel:** dopasowanie po tym, co komponent robi.
**Zakres:** rejestr terminów **zamknięty** — nowy termin wymaga jawnej rejestracji, free-text odrzucany na wejściu.
**Bramka:** dwa niezależne przebiegi na tym samym repo → identyczny zbiór terminów · zero terminów spoza rejestru · pomiar hit-rate uruchomiony.
**Porażka:** rejestr rośnie szybciej niż liczba komponentów → model dopasowania zły, przeprojektować przed M5.
**Rollback:** dopasowanie wyłączone, komponenty zostają.

### M5 — Kompilacja i testy w izolacji

**Cel:** dowód zamiast deklaracji.
**Zakres:** zadania asynchroniczne z trwałym stanem · sandbox (WSL/cgroups przed Dockerem) · `COMPILED → TESTED → VERIFIED` · **cache negatywny** (co oblało, na jakim toolchainie).
**Bramka:** `VERIFIED` nieustawialny bez zapisanego dowodu · zmiana hasha toolchaina unieważnia `VERIFIED`.
**Porażka:** brak izolacji — wtedy nie ma M5. Uruchamianie nieufanego kodu bez sandboxa jest poza zakresem.
**Rollback:** cykl życia zatrzymany na `PARSED`.

### M6 — Składanie

**Cel:** deterministyczne złożenie zweryfikowanych komponentów.
**Zakres:** **wyłącznie Rust + cargo**, komponenty na poziomie funkcji, manifest złożenia.
**Bramka:** to samo wejście → identyczny wynik · manifest wskazuje każdy użyty komponent.
**Warunek wejścia:** hit-rate ponownego użycia z M4 **> 30%** na realnym ruchu przez 4 tygodnie. Poniżej — nie zaczynamy.

**Poza planem, świadomie:** IR i translacja między językami (ACAE-spec §15–16).

---

## 12. Ryzyka

| # | Ryzyko | Dowód / status | Mitygacja |
|---|---|---|---|
| **R0** | **Trzy rozjechane kopie repo; plan i przedmiot planu w różnych miejscach** | `git cat-file -t 06fdfe2` w klonie zdalnym → `Not a valid object name`; zdalne 20 plików `.py` vs E: ponad 190 | ACAE pracuje wyłącznie na E:; `frozen_head` w `queries.json`; synchronizacja to osobna decyzja Marcina (§1.1) |
| R1 | Transport MCP nie utrzyma długich operacji | `git_status` → timeout `-32001`; `OFF_*` TTL ~60–90 s | model async od M1, wynik na dysk |
| ~~R2~~ | ~~Nieznana liczba bloków CBMS~~ | — | **nieaktualne** — ACAE nie dotyka CBMS |
| R3 | Everything zwraca szum | `fast_search("ACAE")` → 30/30 spoza AIONS | filtr kandydatów w porcie Locator |
| ~~R4~~ | ~~Brak gramatyk tree-sitter~~ | `LANGS` w `ts_symbols.py` = 19 rozszerzeń, `tree_sitter_language_pack` działa w venv | **zamknięte reconem**; brak gramatyki → `skipped: no_grammar` |
| R5 | Niski hit-rate ponownego użycia | nieznany | mierzony od M4, bramka wejścia do M6 |
| R6 | Rozjazd terminologii po raz czwarty | AIONS ×5, CBMS ×4, codebook ×2, ADR-002 ×5 kopii | `TERMS.md` + kontrola w `cbms_doctor.py` |
| R7 | Dryf magazynu ACAE od modelu Block | — | jeden algorytm hasha (§6), jeden kształt prowenancji |
| **R8** | **Rozszczepienie zależności między interpreterami** | venv 3.11 ma `tree_sitter_language_pack`, brak `tiktoken`; system 3.13 odwrotnie | rozstrzygnięcie w bramce M0 |
| **R9** | **`ts_symbols.py` zmieni się pod ACAE** | jest w aktywnym rozwoju (commit sprzed 3 dni) | adapter w jednym pliku (`ts_adapter.py`); testy kontraktowe na `outline()`/`get()`; zmiana łamiąca jest widoczna w jednym miejscu |

---

## 13. Czego ten moduł świadomie nie robi

- Nie buduje warstwy LSP (odrzucone 2026-08-08).
- **Nie pisze drugiego parsera tree-sitter** — `ts_symbols.py` istnieje i wystarcza (§2).
- **Nie wywołuje `as_chunk_candidates()`** — nie wlewa kodu do CBMS jako chunków (§1.2).
- Nie dotyka CBMS, `cbms_memory.py` ani `store_http.py`.
- Nie synchronizuje repozytoriów ani nie kasuje kopii na D: — to decyzje Marcina, nie modułu.
- Nie wprowadza Dockera ani chmury.
- Nie przesądza ADR-003 ani ADR-004 — magazyn ACAE jest lokalny dla ACAE, nie dla pamięci systemu.
- Nie tłumaczy między językami.
- Nie dokłada więcej niż 2 narzędzia MCP przed M2.

---

## 14. Pierwszy krok

**M0.** Założyć `E:\server wiedzy\acae\`, kontrakt, zamrozić 10 zapytań z `answer_files` i `required_symbols`, rozstrzygnąć interpreter, zmierzyć bazę. Bez tej liczby bramka M1 („redukcja ≥50%") jest niesprawdzalna, a moduł staje się kwestią wiary.

**Rozstrzygnięte w v3:** root = `E:\server wiedzy` · kod = `acae/` wewnątrz repo · magazyn = własny, gitignorowany · hash = `b2b256:` · parser = `ts_symbols.py` przez adapter · zależność od CBMS = brak.

**Do rozstrzygnięcia przez Marcina, poza modułem:** czy i jak E: trafia na GitHub (§1.1) · kiedy znika kopia z D:.
