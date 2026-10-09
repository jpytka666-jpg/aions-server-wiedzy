# WPC — stan wiedzy, pochodzenie kodu i dowodów (2026-10-09)

> AIONS PROVENANCE | Author: GPT-6 / Board technical proxy | OBSERVED_AT: 2026-10-09T20:05–20:12Z | Source scope: WPC Git mirror, historical GitHub logs, Paperclip LOR-13–LOR-22 | Status: evidence catalogue, not a claim of successful deployment.
> Source-of-truth rule: każde zdanie rozróżnia VERIFIED SOURCE (kod lub oryginalny log), HISTORICAL REPORTED (pomiar opisany w dokumencie, bez surowych danych), OWNER-REPORTED (wspomnienie właściciela) i UNKNOWN (brak dowodu). Nowszy zapis nie usuwa historii prób i błędów.

## 1. Po co istnieje WPC

WPC to własny silnik kompresji i uruchamiania wag modeli AI, rozwijany jako część AIONS, a nie tylko nakładka na Ollama/llama.cpp. W repozytorium znajdują się kompilator formatów WPC, kodeki, dekodery, własny runtime Rust, program agentowy z narzędziami MCP, mechanizmy utrzymywania modelu w pamięci oraz eksperymentalne ścieżki CUDA. Trzeba wskazywać konkretną gałąź i commit: część zaawansowanych funkcji nie znajduje się w main.

Repo: https://github.com/jpytka666-jpg/wpc-engine
Zbadano 77 gałęzi, 51 różnych commitów HEAD oraz 776 commitów dostępnych w pełnej lokalnej historii Git (stan inwentaryzacji 2026-10-09). Drzewa 51 HEAD mają 336 unikalnych ścieżek plików; 95 ścieżek miało różne wersje blobów (w oddzielnej metodzie Haiku wyszło 98 — różnicę metody należy zachować, nie uśredniać). To kompletny indeks drzew HEAD, NIE przegląd każdej linii historii.

## 2. Kompresja WPC — co implementuje kod

| Wariant | Pakowanie 128 wag | Efektywny koszt | Status źródła |
|---|---|---|---|
| v2 | wartości skwantowane do 6 bitów, każdy kod przechowany w bajcie + nagłówek FP16 | 132 B / 128 = 8,25 bitu/wagę | VERIFIED SOURCE |
| v3 | te same 6-bitowe kody co v2, przepakowane po cztery w trzy bajty | 100 B / 128 = 6,25 bitu/wagę | VERIFIED SOURCE |
| v4 | 4-bitowe kody, dwie połówki bajtu + nagłówek FP16 | 68 B / 128 = 4,25 bitu/wagę | VERIFIED SOURCE |

Formuła dekodera: w = zero_point + kod * scale; zero_point i scale są przechowywane w formacie FP16. Sercem są wpc-core/src/quant_encoder.rs, wpc-format/src/lib.rs, wpc-compiler/src/main.rs oraz wpc-runtime/src/wpc_weights_v2.rs, wpc_weights_v3.rs i wpc_weights_v4.rs. Kompilator zapisuje model_v2.wpc / model_v3.wpc / model_v4.wpc i metadane; runtime wczytuje skompresowane bloki i może wykonywać matvec bez rozwinięcia całego modelu do pełnej precyzji. v3 jest przepakowaniem kwantyzacji v2, co ma zachowywać te same wartości zrekonstruowane.

Źródło przypięte do commita: https://github.com/jpytka666-jpg/wpc-engine/blob/f3c7c1f945977dafbd0fa409a5f84e8fde3978d3/wpc-core/src/quant_encoder.rs
Źródło formatu: https://github.com/jpytka666-jpg/wpc-engine/blob/f3c7c1f945977dafbd0fa409a5f84e8fde3978d3/wpc-format/src/lib.rs

### Znalezione luki — do TESTÓW, nie udowodnione awarie

- Kody w encoderze wyznaczane są na podstawie wartości FP32, ale nagłówki min/scale w decoderze mają zaokrąglenie FP16; może to powiększać błąd w niektórych zakresach.
- Brakuje jawnego zabezpieczenia encoder/loader przed skrajnymi zakresami powodującymi overflow FP16 / Inf / NaN (według przeglądu kodu main).
- Dekoder SIMD/FMA i skalarny nie muszą zwracać bitowo identycznych liczb przez inną kolejność sumowania, mimo mylącego komentarza o zgodności.
- W przejrzanej main brak testu rzeczywistych skompresowanych wag porównującego matvec scalar z fused i brak obsługi v4 w części dense model.rs. Kod Qwen3-MoE ma kilka różnych wariantów między gałęziami, które nie były w całości porównane.

## 3. Qwen3-Coder-30B-A3B MoE — co potwierdzono

- HISTORICAL REPORTED w WHITEPAPER: rozmiar nieskompresowanego modelu ~57 GB w przyjętej tam konwencji; WPC v3 ~22,21 GB, WPC v4 ~15,10 GB. To imponująca redukcja, ale sama wielkość pliku nie dowodzi braku utraty jakości.
- HISTORICAL REPORTED w WHITEPAPER: prędkość ~2,35 tokena/s (~141 tokenów/min). W dokumencie autor podaje również przybliżenie ~120 słów/min; nie ma dołączonego surowego logu, SHA binarki, identycznego promptu ani dowodu, że pomiar ten dotyczył GPU.
- OWNER-REPORTED: właściciel z Claude'em uruchamiali Qwen3 Coder ~30B MoE na HP ZBook z Quadro M2000/M2000M i obserwowali około 160 słów/min oraz pogorszenie jakości przy mocnej kompresji. Wspomnienie jest ważną wskazówką archiwalną, ale oryginalny log pełnej generacji 30B na GPU nie został jeszcze znaleziony w publicznym repozytorium.
- Dokładna arytmetyka: 2,5 tokena/s * 60 = 150 TOKENÓW/min, a 2,35 * 60 = 141 TOKENÓW/min. Token nie jest automatycznie słowem. Nie należy łączyć CPU i GPU w jeden wynik bez dowodu.
- Z plików prób KV 30B odczytano PENDING i wzmiankę o odzyskiwanym executable; nie ma tam zaliczonego testu szybkości generowania. MoE oznacza Mixture of Experts, nie Mixture of Agents.

WHITEPAPER: https://github.com/jpytka666-jpg/wpc-engine/blob/main/WHITEPAPER.md

## 4. NVIDIA Quadro M2000M — rzeczywisty zapis z 25 sierpnia 2026

VERIFIED HISTORICAL RUN LOG, lecz NIE pomiar wykonany dziś: na fizycznym GPU M2000M / sm_50 sprawdzono Qwen3-4B w WPC v4. Skompresowany model ~2038 MiB mieścił się w 4 GiB VRAM. Dzienniki zapisują 253 tensory, 4 022 272 000 dekodowanych wartości i 0 różnic wobec referencji CPU; suma czasów kerneli dekodowania ~891,966 ms. Fused decode+GEMV w osobnym teście ~1,043 ms dla konkretnego tensora i zgodność w granicach tolerancji. Dowodzi to wykonania na GPU prawdziwego dekodera WPC4 oraz konkretnego GEMV, NIE pełnej generacji tekstu przez 30B na GPU.

Raport: https://github.com/jpytka666-jpg/wpc-engine/blob/feature/gpu-wpc4-decode-sm50/docs/gpu-wpc4-decode-sm50-2026-08-25.md
Log dekodera: https://github.com/jpytka666-jpg/wpc-engine/blob/feature/gpu-wpc4-decode-sm50/gpu/wpc4-decode/runs/sweep_2026-08-25_0522.log
Log GEMV: https://github.com/jpytka666-jpg/wpc-engine/blob/feature/gpu-wpc4-decode-sm50/gpu/wpc4-decode/runs/gemv_2026-08-25_1522.log

## 5. Gemma 12B — zapis historyczny

VERIFIED LOG HISTORYCZNY: test_results/gemma_generation_test.log (wersja testowa sprzed naprawy, oznaczona OUTDATED) wykazuje 40 tokenów w ~46,7–47,3 sekundy (~0,85 tok/s), prefill ~7–13 s. W WHITEPAPER pojawia się v3 ~1,06 tok/s, ale bez surowego logu. W przeanalizowanym kodzie Gemma 12B jest dense; właściciel wspominał też niepewny większy model/MoE — jego identyfikacja pozostaje UNKNOWN.

## 6. Własny runtime i pętla agenta — rozróżnienie gałęzi

- main: wpc-runtime ładuje i uruchamia model, natomiast wpc-runtime/src/bin/aions-agent.rs realizuje pętlę z narzędziami MCP, zwykle ponownie wywołując osobny proces runtime przy kolejnych turach.
- feature/qwen3-moe-batched-prefill: wpc-resident ładuje wagi tylko raz, obsługuje wiele zleceń, ale resetuje KV cache na kolejne żądanie.
- feature/resident-multi-turn oraz feature/memory-kv-real-model-bridge: źródło zawiera ResidentEngine / ResidentSession, wieloturnowe utrzymanie modelu i ponowne użycie przynajmniej części KV kontekstu. Nie jest to dowód aktualnego wdrożenia na Darkstarze.
- W gałęziach memory-kv/organism istnieją biblioteki pamięci i most WPC, ale ich istnienie nie dowodzi spięcia z działającą pętlą agenta.
- WAŻNE BEZPIECZEŃSTWO: parametr operatorowego zatwierdzania wywołań MCP (--ask) w badanym aions-agent domyślnie ma false. Sam moduł Ghost Gate nie jest jeszcze dowodem jego podłączenia w tej ścieżce. Przed prawdziwymi lokalnymi pracownikami potrzeba jawnej kontroli uprawnień.

Przykładowy kod resident: https://github.com/jpytka666-jpg/wpc-engine/blob/feature/memory-kv-real-model-bridge/wpc-runtime/src/resident.rs
Agent: https://github.com/jpytka666-jpg/wpc-engine/blob/main/wpc-runtime/src/bin/aions-agent.rs

## 7. Jakość kompresji — bez dopisywania fikcyjnego PASS

OWNER-REPORTED: na bardzo agresywnej kompresji (około 4 bitów) duży model tracił zdolność poprawnego rozumowania; przy 6 bitach było lepiej; właściciel pamięta, że około 8 bitów odpowiedzi mogły być porównywalne albo nawet lepsze niż z nieskompresowanego modelu. Nie ma dziś odtworzonego testu A/B z identycznymi promptami, samplowaniem i materiałem referencyjnym, który potwierdza poprawę względem vanilla. WPC v4, v3 i v2 mają efektywnie ~4,25, 6,25 i 8,25 bitu/wagę — to pasuje do kierunku wspomnień, ale nie stanowi dowodu konkretnej konfiguracji historycznej.

Do przyszłego testu (oddzielne zatwierdzenie) porównać ten SAM zestaw promptów, seed, temperaturę, parser, długość odpowiedzi, zgodność funkcjonalną i pomiary szybkości na vanilla / v2 / v3 / v4. Wynik jakości ma być mierzalny i archiwizowany, a nie wybrany według jednego udanego tekstu.

## 8. Co zostało i gdzie szukać

1. Odzyskać oryginalne binarki, logi i modele ze starego środowiska Windows/WSL oraz archiwalnych dysków. Zapisane tam przebiegi mogą rozstrzygnąć spór o 30B na M2000M i ~160 słów/min.
2. Wskazać dokładny commit źródła użyty do historycznej binarki i modelu; SHA samego aktualnego repo nie jest dowodem działania wcześniejszego executable.
3. Domknąć porównanie gałęzi qwen3_moe_model.rs i przetestować błędy FP16, scalar/SIMD oraz macierze pełnych wag.
4. Sprawdzić aktywne środowisko i dostęp do GPU/RAM przed jakimkolwiek uruchomieniem modeli. Dwa urządzenia M60 po 8 GiB nie są automatycznie jednym urządzeniem 16 GiB; 30B FP16 nie mieści się w 24 GiB P40 bez dalszej kompresji lub offloadu.
5. Dopiero po potwierdzeniu kodeka, źródeł i operatorowej bramki narzędzi zorganizować lokalnych pracowników AIONS.

## 9. Audyt pochodzenia i odnajdywania dowodów

- Paperclip: LOR-13–LOR-18 (publiczne gałęzie + kod resident, w tym przerwane przebiegi); LOR-19 (wszystkie 77 gałęzi); LOR-20 (historia 30B/Gemma/GPU); LOR-21 (runtime i MCP); LOR-22 (kodeki v2/v3/v4).
- Lokalna kopia publicznego Git: ZBook, bare mirror z 77 refs / 51 HEAD, z zachowaną historią; indeks porównujący blobs/ścieżki istnieje osobno. Kopia i indeks służą do taniego audytu, a nie jako uruchomiony silnik.
- WPC należy badać razem z polip-agi i aions-server-wiedzy, ale nie utożsamiać różnych gałęzi/hostów ani starej dokumentacji z dzisiejszym stanem maszyny.
- Gdy historyczna obserwacja jest obalona nowszym logiem, zachować obie daty i wyjaśnić następstwo. Nie usuwać porażek, nie poprawiać historii pod wynik.

## 10. Granice tego dokumentu

Dokument jest trwałym indeksem wiedzy. Nie zawiera haseł, tokenów, danych osobowych, konfiguracji dostępu ani prywatnego archiwum rozmów. Nie dowodzi, że WPC jest obecnie uruchomiony w VM140 albo że model 30B generuje dziś na M2000M. W szczególności nie zezwala na instalowanie pakietów, kompilowanie kodu, zmiany Proxmoxa, sieci, GPU, uruchamianie inferencji lub modyfikacje pamięci CBMS.

END — następny wpis powinien być dopiskiem z datą/źródłami, a nie cichym nadpisaniem niewygodnej historii.
