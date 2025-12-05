---
inclusion: always
priority: 1
---

# Check Before Create - ZAWSZE Sprawdź Przed Tworzeniem

## ZASADA NADRZĘDNA:

**NIGDY nie twórz niczego bez sprawdzenia czy już istnieje!**

## PRZED każdą akcją:

### 1. Przed stworzeniem pliku:

```bash
# ZAWSZE sprawdź czy plik istnieje
fast_search("nazwa_pliku")
# LUB
fileSearch("nazwa_pliku")
# LUB
readFile("ścieżka/do/pliku")
```

**Jeśli plik istnieje:**
- Przeczytaj go
- Sprawdź co zawiera
- Zapytaj użytkownika czy nadpisać/zaktualizować
- NIE twórz duplikatów!

### 2. Przed stworzeniem funkcji/klasy:

```bash
# ZAWSZE sprawdź czy funkcja już istnieje
grepSearch("def nazwa_funkcji|class NazwaKlasy")
```

**Jeśli funkcja istnieje:**
- Pokaż użytkownikowi gdzie jest
- Zapytaj czy zaktualizować istniejącą
- NIE twórz duplikatów!

### 3. Przed instalacją pakietu:

```bash
# ZAWSZE sprawdź requirements.txt
readFile("requirements.txt")
```

**Jeśli pakiet już jest:**
- Powiedz użytkownikowi
- Sprawdź wersję
- NIE dodawaj duplikatów!

### 4. Przed stworzeniem repo na GitHub:

```bash
# ZAWSZE sprawdź czy repo istnieje
gh repo list | grep "nazwa-repo"
# LUB
gh repo view username/nazwa-repo
```

**Jeśli repo istnieje:**
- Pokaż użytkownikowi
- Zapytaj czy użyć istniejącego
- NIE twórz duplikatów!

### 5. Przed dodaniem MCP server:

```bash
# ZAWSZE sprawdź mcp.json
readFile(".kiro/settings/mcp.json")
```

**Jeśli server już jest:**
- Pokaż konfigurację
- Zapytaj czy zaktualizować
- NIE dodawaj duplikatów!

### 6. Przed stworzeniem steering rule:

```bash
# ZAWSZE sprawdź .kiro/steering/
listDirectory(".kiro/steering/")
# LUB
fast_search("nazwa-rule.md")
```

**Jeśli rule istnieje:**
- Przeczytaj istniejącą
- Zapytaj czy zaktualizować
- NIE twórz duplikatów!

## WORKFLOW dla każdej akcji:

```
1. User: "Stwórz X"
2. Kiro: Sprawdza czy X już istnieje
3a. Jeśli NIE istnieje → Tworzy
3b. Jeśli istnieje → Pokazuje i pyta co zrobić
```

## Przykłady:

### ❌ ZŁE (bez sprawdzania):

```
USER: "Stwórz plik config.py"
KIRO: [tworzy config.py]
```

### ✅ DOBRE (ze sprawdzaniem):

```
USER: "Stwórz plik config.py"
KIRO: 
1. Sprawdzam czy config.py już istnieje...
2. [fileSearch("config.py")]
3a. Jeśli NIE znalazłem → "Tworzę config.py"
3b. Jeśli znalazłem → "config.py już istnieje w [ścieżka]. Czy chcesz go zaktualizować czy stworzyć nowy?"
```

## Narzędzia do sprawdzania (w kolejności priorytetu):

### PRIORYTET 1: AIONS Context MCP
```
fast_search()        → Najszybsze, szuka wszędzie
memory_recall()      → Sprawdza czy robiłem to wcześniej
cbms_search()        → Sprawdza wiedzę domenową
project_search()     → Szuka w zeskanowanym projekcie
```

### PRIORYTET 2: Lokalne narzędzia Kiro
```
fileSearch()         → Szuka plików
grepSearch()         → Szuka w zawartości
readFile()           → Czyta plik
listDirectory()      → Lista plików w folderze
```

### PRIORYTET 3: Git/GitHub
```
git status           → Sprawdza zmiany
gh repo list         → Lista repozytoriów
gh repo view         → Szczegóły repo
```

## Wyjątki:

Jedyny przypadek gdy NIE sprawdzam:
- User wyraźnie mówi "nadpisz" lub "stwórz nowy mimo że istnieje"

## Komunikaty dla użytkownika:

### Gdy coś istnieje:
```
"✋ Moment! [X] już istnieje w [lokalizacja].
Zawiera: [krótki opis]
Co chcesz zrobić?
A) Użyć istniejącego
B) Zaktualizować istniejący
C) Stworzyć nowy (duplikat)
D) Anulować"
```

### Gdy nic nie znalazłem:
```
"✅ Sprawdziłem - [X] nie istnieje. Tworzę..."
```

## Automatyczne sprawdzanie na początku sesji:

Gdy użytkownik rozpoczyna sesję:
1. Sprawdź `git status` - czy są zmiany
2. Sprawdź `.kiro/steering/` - jakie mam reguły
3. Sprawdź `mcp.json` - jakie mam serwery
4. Sprawdź `requirements.txt` - jakie mam pakiety
5. Pokaż użytkownikowi podsumowanie

## Przykład podsumowania na start:

```
🔍 Sprawdziłem twój projekt:

✅ Git: 3 uncommitted changes
✅ Steering rules: 5 aktywnych
✅ MCP servers: 4 skonfigurowane (3 działają, 1 disabled)
✅ Python packages: 6 zainstalowanych
✅ Repo: PRIVATE (bezpieczne)

Gotowy do pracy! Co robimy?
```

## KRYTYCZNE:

**ZAWSZE sprawdzaj PRZED:**
- Tworzeniem pliku
- Tworzeniem funkcji
- Instalacją pakietu
- Tworzeniem repo
- Dodawaniem MCP server
- Tworzeniem steering rule
- Commitowaniem zmian
- Pushowaniem na GitHub

**NIGDY nie zakładaj że czegoś nie ma - ZAWSZE sprawdź!**
