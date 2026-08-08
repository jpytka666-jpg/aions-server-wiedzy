# PLAN: Pakiet AIONS — absorpcja Sereny + 6 podsystemów

**Data:** 2026-08-08
**Status:** PLAN — zero zmian wykonanych
**Zakres:** Serena (mechanika) + GCD + prefix cache + Tree-sitter + DSPy + Model Cascading

---

## 1. Ustalenia sprzętowe — to determinuje wszystko

| Element | Stan | Źródło |
|---|---|---|
| **GPU** | **Quadro M2000M, 4096 MiB, Maxwell (sm_50, 2015)** | `nvidia-smi` |
| Sterownik | 581.42 | `nvidia-smi` |
| Silnik lokalny | **Ollama** zainstalowana | `where ollama` |
| Modele lokalne | **ZERO pobranych** | `ollama list` → pusto |
| Python | 3.13.14 | probe |
| `torch`, `transformers` | OK | probe |
| `tree_sitter`, `dspy`, `outlines`, `xgrammar`, `llama_cpp`, `vllm`, `sglang` | **wszystkie MISSING** | probe |
| Rust (`cargo`), Node | OK | probe |

### Co z tego wynika — twardo

**4 GB VRAM na Maxwellu to sufit, nie sugestia.**

- **vLLM** wymaga compute capability ≥ 7.0 (Volta+). Twoja karta ma 5.0. → **niedostępne**
- **SGLang** (czyli natywna RadixAttention) — ta sama bariera. → **niedostępne**
- **FlashAttention** wymaga Turinga/Ampere. → **niedostępne**
- Phi-4 (14B) w Q4 to ~9 GB. **Nie zmieści się.** Phi-4-mini (3.8B) w Q4 to ~2.5 GB — **zmieści się**.

Wsparcie sm_50 w nowych buildach PyTorcha bywa wycinane — **do zweryfikowania osobno**,
bo `torch` jest zainstalowany, ale to nie znaczy, że widzi tę kartę.

---

## 2. Werdykt per pomysł

| # | Pomysł | Na tym sprzęcie | Mechanizm, który realnie zadziała |
|---|---|---|---|
| 1 | **Tree-sitter** | ✅ **Zielone** | Czysty CPU, bez GPU. `pip install tree-sitter tree-sitter-language-pack`. Najlepszy stosunek zysku do kosztu z całej listy |
| 2 | **Grammar-Constrained Decoding** | ✅ **Zielone (ograniczone)** | Ollama `format` = JSON Schema (GBNF pod spodem). Dla dowolnych gramatyk: `outlines` na `transformers`/CPU |
| 3 | **RadixAttention** | ❌ **Czerwone** | Wymaga SGLang → wymaga nowoczesnego GPU. **Zamknięte na tej karcie** |
| 3b | **Prefix cache na NVMe** | 🔶 **Żółte** | Osiągalne, ale **nie przez Ollamę**. `llama.cpp --prompt-cache PLIK` persystuje KV do pliku i działa na CPU |
| 4 | **DSPy** | ✅ **Zielone** | Orkiestracja, nie compute. Wymaga jednak zbioru + metryki — patrz §4 |
| 5 | **Model Cascading** | ✅ **Zielone** | Sprzęt wręcz *wymusza* poprawny projekt — patrz §5 |
| 6 | **Serena: mechanika A–D** | ✅ **Zielone** | Bez zmian z poprzedniej wersji planu |
| 7 | **Serena: warstwa LSP** | ❌ **Nie przepisywać** | Lata pracy społeczności. Tree-sitter daje 80% za 5% kosztu |

---

## 3. Kluczowa teza — twoja lista to nie 6 pomysłów, tylko jeden system

Na 4 GB VRAM lokalny model będzie **słaby**. To fakt, nie opinia.
Ale trzy pozycje z twojej listy dokładnie to kompensują i robią to razem:

**Tree-sitter** daje strukturę (co jest symbolem, gdzie się zaczyna i kończy).
**GCD** gwarantuje, że wyjście jest poprawne strukturalnie — *niezależnie od tego, jak głupi jest model*.
**Cascading** przerzuca rozumowanie do chmury tylko wtedy, gdy lokalny nie ma podstaw.

To jest właściwa odpowiedź na „phi4 jest ryjem, aions mózgiem". Precyzyjniej:

> **CBMS jest mózgiem. Tree-sitter jest wzrokiem. GCD jest gramatyką — dosłownie.
> Mały model lokalny jest językiem. Chmura jest konsultantem, nie właścicielem kontekstu.**

### Najmocniejsze zastosowanie GCD w AIONS

Nie „ładny JSON". To:

**Gramatyka wyliczająca dopuszczalne ID chunków ze zbioru retrieved.**

Jeśli gramatyka pozwala zacytować wyłącznie `K...` z aktualnie pobranego Top-K,
to **halucynacja cytowania staje się niemożliwa, nie tylko karana**.
CRLA dziś punktuje kryterium *Facts* po fakcie. GCD wyklucza błąd *przed* faktem.

To jest dokładnie ta sama filozofia, którą już masz w guardrailu
(brak evidence → twarda odmowa) — tylko przeniesiona na warstwę dekodowania.
Dlatego to pasuje do AIONS lepiej niż cokolwiek innego z listy.

---

## 4. Poprawki merytoryczne — rzeczy, w których się mylisz albo Gemini się myli

### 4.1 „Wjebać na NVMe obliczone z roku" — nie zadziała tak, jak myślisz

KV cache jest **związany z konkretnym modelem, kwantyzacją i pozycją w kontekście**.
Nie jest przenośnym artefaktem. Zmiana modelu lub kwantyzacji → cały cache do kosza.

Rachunek dla Phi-4-mini (32 warstwy, 8 głów KV, head_dim 128, fp16):
`2 × 32 × 8 × 128 × 2 B ≈ 128 KB na token`.
128 GB NVMe ≈ **~1 mln tokenów KV**. Dużo — ale tylko dla **dokładnych dopasowań prefiksu**.

**Werdykt:** prefix cache na NVMe ma sens dla *stabilnego, długiego prefiksu*
(system prompt CBMS + stały preambuł) — i tam da realny zysk latencji.
Nie ma sensu jako „pamięć roku". **Pamięcią roku jest CBMS** i to jest właściwy podział ról.

### 4.2 Router na średnim logprobie < 85% — słaby sygnał

Średnie prawdopodobieństwo tokenów jest zdominowane przez tokeny łatwe
(interpunkcja, spójniki) i jest źle skalibrowane. Mierzy **płynność**, nie **pewność**.

Lepsze sygnały, w kolejności wartości dla ciebie:

1. **Sygnał retrievalowy (najlepszy, już go masz)** — jeśli CBMS zwraca poniżej `min_hits`
   albo overlap najlepszego chunka jest poniżej progu → eskalacja.
   Mierzy „czy mam podstawy", nie „czy brzmię pewnie". **Zero nowego kodu do pomiaru.**
2. **Margines top-1 vs top-2** na tokenach decyzyjnych
3. **Minimalne** prawdopodobieństwo w odpowiedzi (nie średnie)
4. Entropia — dopiero na końcu

### 4.3 Pętla dystylacji to ta sama bomba, o której mówiliśmy

Odpowiedź z chmury → nowy chunk → **staje się evidence dla przyszłych odpowiedzi**.
Jeśli chmura się pomyliła, błąd jest teraz lokalną „prawdą" bez oznaczenia pochodzenia.

**Wymagane przed uruchomieniem cascadingu:**
- pole `provenance` w chunku: `local | cloud | human | verified`
- pole `confidence` + `created_by_query`
- CRLA waży *Facts* inaczej dla `cloud` niż dla `human`/`verified`
- chunki `cloud` podlegają obowiązkowemu przeglądowi w diagnostyce (Faza C)

### 4.4 „Oszczędność API 80–90%" to hipoteza, nie liczba

Wiarygodna co do rzędu wielkości, ale niezmierzona. Wchodzi do planu jako **metryka do weryfikacji**,
nie jako założenie.

---

## 5. Zaktualizowany plan faz

Kolejność nie jest dowolna — wynika z zależności.

### Tor 0 — Fundament (nic nie zależy od reszty)

| Faza | Zakres | Ryzyko |
|---|---|---|
| **0.1** | Zmierzyć pokrycie `references` w 457 chunkach (patrz §6) | zerowe, read-only |
| **0.2** | Serena zainstalowana **poprawnie**: `uv tool install -p 3.13 serena-agent@latest`, `serena init`. Wpis MCP na binarkę, nie na `git+`. Usunięcie z `disabledMcpServers` | zerowe dla AIONS |
| **0.3** | `ollama pull phi4-mini` (lub `qwen2.5:3b`) — **masz zero modeli, bez tego nic lokalnego nie ruszy** | zerowe |

### Tor A — Widzenie struktury (Tree-sitter)  ← *enabler, robić wcześnie*

| Faza | Zakres | Pliki |
|---|---|---|
| **A.1** | `pip install tree-sitter tree-sitter-language-pack`; PoC: outline pliku `.py` | scratch |
| **A.2** | `server/ts_symbols.py` — **nowy leaf**: plik → lista symboli z zakresami | nowy |
| **A.3** | Chunking kodu wyrównany do symboli (chunk = funkcja/klasa, nie N linii) | `tools/` |
| **A.4** | Reparse inkrementalny przy zmianie pliku | `server/ts_symbols.py` |

### Tor B — Mechanika Sereny w CBMS

| Faza | Zakres | Pliki |
|---|---|---|
| **B.1** | **Outline-then-drill**: Top-K zwraca szkielet, treść na żądanie | `server/cbms_memory.py` (addytywnie) |
| **B.2** | **Indeks wsteczny referencji** — zależy od wyniku 0.1 | nowy `server/refgraph.py` (leaf) |
| **B.3** | **Diagnostyka** — martwe referencje, sieroty, duplikaty, chunki `cloud` bez weryfikacji | nowy `tools/cbms_doctor.py` (leaf) |
| **B.4** | **Modes** — filtrowanie ~60 narzędzi AIONS-Context wg trybu | konfiguracja MCP |

### Tor C — Gwarancje strukturalne (GCD)  ← *największy zysk architektoniczny*

| Faza | Zakres |
|---|---|
| **C.1** | Ollama `format` = JSON Schema dla odpowiedzi CBMS. Schemat wymusza pola `answer` + `evidence[]` |
| **C.2** | **Gramatyka z wyliczonymi ID chunków** z aktualnego Top-K → cytowanie nieistniejącego chunka staje się niemożliwe |
| **C.3** | Jeśli JSON Schema okaże się za słabe → `outlines` na `transformers`/CPU dla pełnych gramatyk |

### Tor D — Cascading + prefix cache

| Faza | Zakres | Uwaga |
|---|---|---|
| **D.1** | Pola `provenance` / `confidence` w schemacie chunka | **warunek konieczny przed D.2** |
| **D.2** | Router **retrievalowy** (nie logprobowy) — próg na `min_hits`/overlap | §4.2 |
| **D.3** | Pętla dystylacji: odpowiedź chmury → chunk z `provenance: cloud` | podlega B.3 |
| **D.4** | Pomiar realnej oszczędności tokenów przed/po | weryfikacja §4.4 |
| **D.5** | *Opcjonalnie:* llama.cpp obok Ollamy wyłącznie dla `--prompt-cache` na NVMe | tylko jeśli D.4 pokaże, że latencja jest wąskim gardłem |

### Tor E — DSPy  ← *ostatni, i to jest uzasadnione*

DSPy optymalizuje **program o zamrożonym kształcie**. Optymalizowanie programu,
który wciąż przebudowujesz, to spalony compute.

Ale materiał masz **już gotowy i to jest piękne**:
- zbiór treningowy → `memory/thinking_log.jsonl`, `memory/crla_runs.jsonl`, `cbms_outbox.jsonl`
- metryka → **scoreboard CRLA to dosłownie funkcja oceny, której DSPy potrzebuje**

CRLA i DSPy to ten sam pomysł na dwóch poziomach: CRLA optymalizuje w czasie inferencji
(turniej na zapytanie), DSPy w czasie kompilacji (przeszukanie promptów, zamrożone na końcu).
Spięcie ich = zwycięzcy CRLA jako zbiór uczący dla DSPy.

| Faza | Zakres |
|---|---|
| **E.1** | Eksport logów CRLA do formatu przykładów DSPy |
| **E.2** | Metryka DSPy = scoreboard CRLA (6 kryteriów) |
| **E.3** | `BootstrapFewShot` / `MIPROv2` na sygnaturze retrieval→answer |

---

## 6. Pierwszy pomiar — rozstrzyga kolejność

Policzyć w `memory/chunks`, ile z 457 chunków ma **niepuste `references`**.

- **> 60%** → B.2 opłacalne natychmiast, robić zaraz po A
- **20–60%** → B.2 po A.3 (tree-sitter dostarczy brakujące krawędzie dla kodu)
- **< 20%** → B.2 przesunąć; najpierw wzbogacenie danych

Jedno zapytanie, read-only, zero ryzyka.

---

## 7. Weryfikacja (bez tego nic nie jest „zrobione")

- `curl http://127.0.0.1:9000/health` → `chunks: 457`, bez regresji
- `python test_plasters_integration.py`, `python quick_chat_test.py` — bez zmian
- `RUN_ALL_BENCHMARKS.bat` → diff `logs/BENCHMARK_REPORT.md` przed/po
- **`refusal_rate` nie może wzrosnąć**
- Tor B.1: tokeny odpowiedzi przed/po na tym samym zestawie 10 zapytań
- Tor C: test negatywny — model **nie jest w stanie** wyprodukować ID chunka spoza Top-K
- Tor D: liczba wywołań chmury i tokenów przed/po
- `git status` przed i po każdej fazie

---

## 8. Czego nie wiem

1. Czy zainstalowany `torch` faktycznie widzi Quadro M2000M (sm_50 bywa wycinany z buildów) — **do sprawdzenia**
2. Struktury wewnętrznej Sereny — README opisuje *co*, nie *jak*. Klon repo do analizy, jeśli Tor B ma być inspirowany kodem
3. Realnego pokrycia `references` — §6
4. Czy `concept_map` w manifeście jest już hierarchiczna
5. Czy 128 GB NVMe to dysk systemowy czy osobny (wpływa na sens D.5)

---

## 9. Licencje

- **Serena — MIT** (Copyright (c) 2025 Oraios AI). Kopiowanie kodu legalne; przy dosłownych fragmentach zachować notę + `LICENSES/serena-MIT.txt`. Przy przeniesieniu samego wzorca — nic nie trzeba.
- **Tree-sitter — MIT.** Gramatyki: różne, przeważnie MIT/Apache-2.0 — sprawdzić per język.
- **DSPy — MIT.**
- **Outlines — Apache-2.0.**
- **llama.cpp — MIT.**

Żadna z nich nie jest copyleft. Cały pakiet jest bezpieczny do wchłonięcia.
