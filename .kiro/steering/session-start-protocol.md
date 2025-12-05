---
inclusion: always
priority: 0
---

# Session Start Protocol - ZAWSZE na początku sesji

## ZASADA NADRZĘDNA:

**Na początku KAŻDEJ sesji Kiro MUSI sprawdzić AIONS Context i załadować poprzedni kontekst!**

## WORKFLOW na start sesji:

### 1. Sprawdź poprzednią sesję w AIONS Context

```bash
# ZAWSZE jako PIERWSZE
memory_recall(session_id="kiro-*", query="last session summary")
```

**Jeśli znalazłem poprzednią sesję:**
- Pokaż użytkownikowi krótkie podsumowanie
- Zapytaj czy kontynuować czy zacząć od nowa
- Załaduj kontekst z poprzedniej sesji

**Jeśli nie znalazłem:**
- To pierwsza sesja
- Przywitaj się
- Zapytaj czym się zająć

### 2. Sprawdź conversation history

```bash
conv_history(date="today")
```

**Pokaż użytkownikowi:**
- Ile rozmów było dzisiaj
- Ostatni temat
- Czy są niezakończone zadania

### 3. Sprawdź Git status

```bash
git status
```

**Jeśli są uncommitted changes:**
- Pokaż użytkownikowi co się zmieniło
- Zapytaj czy zrobić commit
- Wykonaj auto commit jeśli user zgodzi się

### 4. Sprawdź MCP servers status

```bash
# Sprawdź czy MCP servers odpowiadają
conv_status()  # Sprawdza AIONS Context
```

**Sprawdź:**
- Czy AIONS Context działa
- Czy ChromaDB jest dostępna
- Czy są błędy w logach

### 5. Pokaż podsumowanie

```
🔍 Sprawdziłem twój projekt:

📅 Ostatnia sesja: [data i czas]
📝 Temat: [co robiliśmy]
✅ Git: [status]
✅ MCP servers: [ile działa / ile total]
✅ Steering rules: [ile aktywnych]
✅ Context: [X% użyte]

Gotowy do pracy! Kontynuujemy [ostatni temat] czy coś nowego?
```

## Przykład pełnego workflow:

```
1. User: [otwiera Kiro IDE]

2. Kiro automatycznie:
   a) conv_status() → sprawdza AIONS Context
   b) memory_recall() → szuka ostatniej sesji (jeśli Context działa)
   c) conv_history() → sprawdza dzisiejsze rozmowy
   d) git status → sprawdza zmiany
   e) Pokazuje podsumowanie

3. Kiro: "Witaj! Ostatnio pracowaliśmy nad [X]. Kontynuujemy?"

4. User: "Tak" / "Nie, zróbmy [Y]"

5. Kiro: Kontynuuje z kontekstem LUB zaczyna nowy temat
```

## Kluczowe komendy AIONS Context:

### Memory Recall (szukanie w pamięci)
```bash
memory_recall(
  session_id="kiro-git-mastery-2025-12-05",
  query="what did we do last time",
  top_k=5
)
```

### Conversation History (historia rozmów)
```bash
conv_history(date="2025-12-05")
conv_history(date="today")
conv_history(date="")  # wszystkie
```

### Memory Store (zapisywanie do pamięci)
```bash
memory_store(
  session_id="kiro-session-YYYY-MM-DD",
  text="Podsumowanie sesji...",
  ttl_days=90
)
```

### Conversation Dump (zrzut rozmowy)
```bash
conv_dump(summary="Krótkie podsumowanie sesji")
```

### CBMS Search (wiedza domenowa)
```bash
cbms_search(query="Git configuration")
```

## Format Session ID:

**Zawsze używaj formatu:**
```
kiro-[temat]-YYYY-MM-DD
```

**Przykłady:**
- `kiro-git-mastery-2025-12-05`
- `kiro-aws-dsql-2025-12-06`
- `kiro-saas-builder-2025-12-07`

## Co zapisywać na końcu sesji:

### 1. Memory Store (długoterminowa pamięć)
```
- Co osiągnęliśmy
- Kluczowe decyzje
- Konfiguracje
- Problemy i rozwiązania
- Następne kroki
```

### 2. Conversation Dump (backup rozmowy)
```
- Automatyczny zrzut co 5 wiadomości
- Ręczny dump na końcu sesji
- Format: JSONL
```

## Automatyczne zapisywanie:

**Kiro automatycznie zapisuje:**
- Co 5 wiadomości → `conv_log()` + auto dump
- Na końcu sesji → `conv_dump()` + `memory_store()`
- Przy ważnych decyzjach → `memory_store()` natychmiast

## Przykład podsumowania na start:

```
🔍 Sprawdziłem AIONS Context:

📅 Ostatnia sesja: 2025-12-05 19:39
📝 Temat: Git Mastery + Kiro Configuration
✅ Osiągnięcia:
   - Skonfigurowano Git + GitHub
   - Stworzono repo (PRIVATE)
   - 8 steering rules aktywnych
   - Odinstalowano VS Code i Cursor

📊 Status:
   - Git: clean (wszystko zacommitowane)
   - MCP servers: 4/4 działają
   - Context: 53% użyte (bezpieczne)

💡 Następne kroki:
   - Nauka AWS DSQL
   - Kiro Powers (SaaS Builder)
   - Git branches/merge

Kontynuujemy AWS DSQL czy coś innego?
```

## KRYTYCZNE:

**ZAWSZE na początku sesji:**
1. ✅ Sprawdź `memory_recall()` - ostatnia sesja
2. ✅ Sprawdź `conv_history()` - dzisiejsze rozmowy
3. ✅ Sprawdź `git status` - zmiany w repo
4. ✅ Sprawdź `system_health()` - MCP servers
5. ✅ Pokaż podsumowanie użytkownikowi

**NIGDY nie zacznij sesji bez sprawdzenia AIONS Context!**

## Troubleshooting:

### Problem: Memory recall nie zwraca wyników
```
Rozwiązanie:
1. Sprawdź czy ChromaDB działa: system_health()
2. Sprawdź conv_history() - może są backupy
3. Sprawdź logs/conversation_dumps/ - ręczne backupy
```

### Problem: Session ID nie pasuje
```
Rozwiązanie:
1. Użyj session_list() - pokaż wszystkie sesje
2. Znajdź najbliższą datę
3. Załaduj z tej sesji
```

### Problem: Context za duży (>80%)
```
Rozwiązanie:
1. Zapisz obecną sesję: conv_dump() + memory_store()
2. Zaproponuj użytkownikowi restart sesji
3. W nowej sesji załaduj z memory_recall()
```

## Monitoring contextu:

**Kiro powinien monitorować:**
- Przy 50% → Informacja: "Context w połowie"
- Przy 70% → Ostrzeżenie: "Context 70%, wkrótce zapisuję"
- Przy 80% → Akcja: Automatyczny dump + propozycja restartu
- Przy 90% → Wymuszony dump + restart

## Przykład ostrzeżenia:

```
⚠️ Context: 80% użyte

Zapisuję obecną sesję do AIONS Context...
✅ Zapisane: session_id="kiro-git-mastery-2025-12-05"

Polecam restart sesji. W nowej sesji automatycznie załaduję kontekst.
Kontynuować czy restart?
```
