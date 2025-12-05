---
inclusion: always
---

# Auto Git Workflow

## Zasada: Automatyczny Git Workflow

Kiro powinien automatycznie zarządzać Git workflow bez pytania użytkownika.

### Kiedy użytkownik zapisuje pliki:

**ZAWSZE wykonaj:**
1. `git status` - sprawdź co się zmieniło
2. `git add .` - dodaj wszystkie zmiany
3. `git commit -m "[auto] Opis zmian"` - commit z sensownym opisem
4. `git push` - wypchnij na GitHub

### Format commit message:

```
[auto] Krótki opis co się zmieniło

Przykłady:
[auto] Updated kiro-mastery-guide.md with Git hooks section
[auto] Fixed .gitignore formatting
[auto] Added new MCP server configuration
[auto] Updated Python dependencies in requirements.txt
```

### Kiedy NIE commitować:

- Gdy są tylko zmiany w `logs/` (logi nie powinny być w repo)
- Gdy są tylko zmiany w `data/` (dane nie powinny być w repo)
- Gdy są tylko zmiany w `venv/` (virtual env nie powinien być w repo)

### Workflow na początku sesji:

Gdy użytkownik rozpoczyna nową sesję z Kiro:
1. Sprawdź `git status`
2. Jeśli są uncommitted changes, zapytaj czy zrobić backup
3. Jeśli tak, wykonaj commit + push

### Przykład automatycznego workflow:

```
USER: [zapisuje plik]

KIRO automatycznie:
1. git status
2. git add .
3. git commit -m "[auto] Updated [nazwa pliku] - [co się zmieniło]"
4. git push
5. Informuje: "✅ Zmiany zapisane na GitHub"
```

## Wyjątki:

Jeśli użytkownik wyraźnie powie "nie commituj" lub "nie pushuj", respektuj to.

## Monitoring:

Co godzinę sprawdzaj czy są niezacommitowane zmiany i przypominaj użytkownikowi.
