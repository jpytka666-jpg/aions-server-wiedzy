# Claude/AI Workflow Rules - MANDATORY

## 🚨 BEZWZGLĘDNE ZASADY NA START KAŻDEJ SESJI

### 1. ZAWSZE NA POCZĄTKU:
1. Użyj `system_health` z aions-context MCP żeby sprawdzić stan systemu
2. Użyj `conv_history` żeby sprawdzić co było robione wcześniej
3. Użyj `memory_recall` z query o aktualny kontekst
4. DOPIERO POTEM odpowiadaj użytkownikowi

### 2. KOLEJNOŚĆ UŻYCIA NARZĘDZI:
```
1. aions-context MCP tools (ZAWSZE PIERWSZY WYBÓR)
   - fast_search → zamiast grep/find
   - memory_recall → zamiast szukania w plikach
   - cbms_search → dla wiedzy domenowej
   - project_search → dla plików projektu

2. Lokalne narzędzia Kiro (jeśli MCP nie wystarczy)
   - Read/Write/Edit
   - Bash (tylko jeśli naprawdę konieczne)

3. Web search (OSTATECZNOŚĆ)
   - Tylko gdy info nie ma lokalnie
   - Tylko gdy user wprost poprosi
```

### 3. ZAKAZY:
- ❌ NIE symuluj wyników - jeśli nie wiesz, powiedz że nie wiesz
- ❌ NIE mów "zrobiłem" bez faktycznego wykonania
- ❌ NIE twórz plików w losowych lokalizacjach
- ❌ NIE ignoruj istniejących plików/konfiguracji
- ❌ NIE używaj web search przed sprawdzeniem lokalnych źródeł

### 4. OBOWIĄZKI:
- ✅ ZAWSZE loguj ważne akcje przez `conv_log`
- ✅ ZAWSZE sprawdzaj `conv_status` przed zakończeniem sesji
- ✅ ZAWSZE używaj `conv_dump` na koniec znaczącej pracy
- ✅ ZAWSZE potwierdzaj wykonanie narzędzia jego wynikiem

## 📁 STRUKTURA PROJEKTU AIONS

```
E:\server wiedzy\           ← GŁÓWNY KATALOG
├── server\                 ← Core AIONS (context_schema, store, cbms)
├── mcpServers\             ← MCP servers (aions-context)
├── scripts\                ← Narzędzia (scanner, turbo)
├── data\                   ← ChromaDB, dane
├── logs\                   ← Logi konwersacji
├── scan_results\           ← Wyniki skanów projektu
├── skills\                 ← Skill files dla AI
└── .kiro\                  ← Konfiguracja Kiro
```

## 🔧 KIEDY MODYFIKUJESZ KOD:

1. PRZED edycją - użyj `project_file_deps` żeby zobaczyć zależności
2. PRZED edycją - użyj `memory_recall` żeby sprawdzić historię zmian
3. PO edycji - użyj `conv_log` żeby zapisać co zrobiłeś
4. PO edycji - uruchom testy jeśli istnieją

## 🎯 CELE PROJEKTU AIONS:

- CBMS (Chunk-Based Memory System) - deterministyczna pamięć AI
- Korean Compression - 97-98% kompresja tekstu
- CRLA - Chain Reaction Learning Algorithm
- Deterministic Responses - powtarzalne odpowiedzi AI

NIE TWÓRZ NOWYCH SYSTEMÓW - UŻYWAJ I ROZWIJAJ ISTNIEJĄCE!
