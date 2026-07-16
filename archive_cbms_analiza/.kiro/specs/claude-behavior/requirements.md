# Requirements: Claude/AI Behavior for AIONS Project

## Overview
Specyfikacja zachowań AI pracującego nad projektem AIONS. Te wymagania mają na celu eliminację typowych problemów: symulacji, amnezji, chaosu, ignorowania narzędzi.

## Functional Requirements

### FR-1: Session Initialization
**Priority:** CRITICAL

- FR-1.1: AI MUSI wywołać `system_health()` na początku każdej sesji
- FR-1.2: AI MUSI wywołać `conv_history()` żeby sprawdzić poprzedni kontekst
- FR-1.3: AI MUSI użyć `memory_recall()` dla aktualnego tematu przed odpowiedzią
- FR-1.4: AI NIE MOŻE odpowiadać na pytania merytoryczne bez wykonania FR-1.1-1.3

### FR-2: Tool Usage Priority
**Priority:** HIGH

- FR-2.1: AI MUSI preferować aions-context MCP tools nad inne narzędzia
- FR-2.2: AI MUSI użyć `fast_search()` zamiast `find` lub `ls`
- FR-2.3: AI MUSI użyć `memory_recall()`/`cbms_search()` przed szukaniem w plikach
- FR-2.4: AI NIE MOŻE używać web search bez wcześniejszego sprawdzenia lokalnych źródeł
- FR-2.5: AI MUSI logować ważne akcje przez `conv_log()`

### FR-3: Anti-Simulation
**Priority:** CRITICAL

- FR-3.1: AI NIE MOŻE mówić "zrobiłem X" bez faktycznego wykonania narzędzia
- FR-3.2: AI MUSI pokazać wynik wywołania narzędzia jako dowód
- FR-3.3: AI NIE MOŻE zgadywać ścieżek plików - MUSI użyć `fast_search()`
- FR-3.4: AI NIE MOŻE symulować zawartości plików - MUSI je odczytać
- FR-3.5: Jeśli AI nie wie - MUSI powiedzieć "nie wiem" zamiast zgadywać

### FR-4: Project Structure
**Priority:** HIGH

- FR-4.1: AI NIE MOŻE tworzyć plików w losowych lokalizacjach
- FR-4.2: AI MUSI przestrzegać struktury katalogów zdefiniowanej w aions-architecture.md
- FR-4.3: AI MUSI sprawdzić `project_file_deps()` przed modyfikacją pliku
- FR-4.4: AI NIE MOŻE duplikować istniejących funkcjonalności

### FR-5: Session Persistence
**Priority:** HIGH

- FR-5.1: AI MUSI wywołać `conv_dump()` przed zakończeniem znaczącej pracy
- FR-5.2: AI MUSI logować podsumowanie sesji przez `conv_log()`
- FR-5.3: AI MUSI potwierdzić zapis przez `conv_status()`

### FR-6: AIONS Integration
**Priority:** MEDIUM

- FR-6.1: AI MUSI używać CBMS do przechowywania wiedzy domenowej
- FR-6.2: AI MUSI używać ChromaDB do semantic search
- FR-6.3: AI MUSI używać Korean Keys dla fast matching
- FR-6.4: AI NIE MOŻE tworzyć nowych systemów pamięci - używa istniejących

## Non-Functional Requirements

### NFR-1: Reliability
- NFR-1.1: Każde twierdzenie AI musi być weryfikowalne przez wywołanie narzędzia
- NFR-1.2: AI musi być deterministyczne - te same inputy → podobne outputy

### NFR-2: Maintainability
- NFR-2.1: Kod tworzony przez AI musi być w odpowiednich katalogach
- NFR-2.2: AI musi dokumentować swoje zmiany przez logging

### NFR-3: Usability
- NFR-3.1: AI odpowiada konkretnie, bez zbędnego gadania
- NFR-3.2: AI przyznaje się do błędów i ograniczeń

## User Stories

### US-1: Jako Marcin chcę żeby AI pamiętało kontekst
```
GIVEN: Nowa sesja AI
WHEN: AI otrzymuje pytanie
THEN: AI sprawdza conv_history() i memory_recall() PRZED odpowiedzią
```

### US-2: Jako Marcin chcę żeby AI nie symulowało
```
GIVEN: AI twierdzi że wykonało akcję
WHEN: Sprawdzam wynik
THEN: Widzę faktyczny output narzędzia, nie tekst AI
```

### US-3: Jako Marcin chcę żeby AI używało moich narzędzi
```
GIVEN: AI potrzebuje znaleźć plik
WHEN: AI szuka pliku
THEN: AI używa fast_search() z aions-context MCP, NIE grep/find w bash
```

### US-4: Jako Marcin chcę żeby AI utrzymywało porządek
```
GIVEN: AI tworzy nowy plik
WHEN: Sprawdzam lokalizację
THEN: Plik jest w odpowiednim katalogu według aions-architecture.md
```
