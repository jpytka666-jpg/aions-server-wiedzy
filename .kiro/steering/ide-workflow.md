---
inclusion: always
---

# IDE Workflow - Kiedy używać VS Code vs Kiro IDE

## Zasada: Używaj odpowiedniego narzędzia do zadania

### Używaj VS Code (zwykły) gdy:

1. **Szybkie edycje**
   - Poprawka literówki
   - Zmiana jednej linii
   - Przeglądanie kodu

2. **Praca bez AI**
   - Nie potrzebujesz pomocy AI
   - Chcesz pracować samodzielnie
   - Testowanie kodu

3. **Performance**
   - Potrzebujesz szybkiego startu
   - Masz mało RAM
   - Pracujesz na słabszym komputerze

4. **Backup**
   - Kiro nie działa
   - Kiro się zawiesił
   - Potrzebujesz awaryjnego edytora

### Używaj Kiro IDE gdy:

1. **Praca z AI**
   - Potrzebujesz pomocy Kiro/Claude
   - Generowanie kodu
   - Refactoring
   - Debugging z AI

2. **MCP Servers**
   - Używasz AIONS Context
   - Pracujesz z AWS DSQL
   - Potrzebujesz MCP tools

3. **Automatyzacja**
   - Auto Git workflow
   - Agent hooks
   - Steering rules

4. **Złożone projekty**
   - Multi-tenant SaaS
   - AWS integration
   - Duże refactoring

## Workflow:

```
1. Otwórz projekt w Kiro IDE (główna praca)
2. Jeśli potrzebujesz szybkiej edycji → VS Code
3. Wróć do Kiro IDE dla AI assistance
```

## Ustawienia:

### VS Code - Minimalna konfiguracja:
- Tylko podstawowe extensions
- Lekki theme
- Szybki start

### Kiro IDE - Pełna konfiguracja:
- Wszystkie AI extensions
- MCP servers
- Steering rules
- Agent hooks

## Skróty:

- `code .` → Otwórz w VS Code
- `kiro .` → Otwórz w Kiro IDE (jeśli masz alias)

## NIGDY nie:

- Nie edytuj tego samego pliku w obu jednocześnie
- Nie commituj z obu jednocześnie
- Nie instaluj tych samych extensions w obu

## Synchronizacja:

Kiro automatycznie commituje zmiany, więc:
1. Pracujesz w Kiro → auto commit
2. Przełączasz się na VS Code → git pull
3. Edytujesz w VS Code → manual commit
4. Wracasz do Kiro → git pull

## Przykład workflow:

```
09:00 - Start dnia → Kiro IDE (główna praca)
10:30 - Szybka poprawka → VS Code
10:32 - Wróć do Kiro IDE
12:00 - Lunch break → Zamknij wszystko
13:00 - Kontynuuj → Kiro IDE
```
