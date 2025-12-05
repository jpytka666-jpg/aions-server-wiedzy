# 🚀 KIRO MASTERY GUIDE - Jak Efektywnie Używać Kiro + AWS

## CZĘŚĆ 1: PODSTAWY KIRO

### 1.1 Jak Kiro Działa

Kiro to AI assistant który:
- **Wykonuje rzeczywiste operacje** na twoim kodzie (nie symuluje!)
- **Ma dostęp do narzędzi** (MCP servers, file operations, shell commands)
- **Pamięta kontekst** poprzez AIONS Context MCP
- **Integruje się z AWS** poprzez Powers

### 1.2 Hierarchia Narzędzi (ZAWSZE W TEJ KOLEJNOŚCI!)

```
PRIORYTET 1: AIONS Context MCP
├── fast_search()        → szukanie plików (błyskawiczne)
├── memory_recall()      → szukanie w pamięci ChromaDB
├── cbms_search()        → wiedza domenowa
├── project_search()     → szukanie w zeskanowanym projekcie
└── conv_history()       → poprzednie rozmowy

PRIORYTET 2: Lokalne Narzędzia Kiro
├── readFile()           → czytanie plików
├── grepSearch()         → szukanie w kodzie
├── strReplace()         → edycja plików
└── executePwsh()        → komendy shell

PRIORYTET 3: AWS Powers
├── aurora-dsql          → baza danych
└── saas-builder         → architektura SaaS

PRIORYTET 4: Web Search
└── TYLKO gdy user wprost poprosi
```

### 1.3 Jak Rozmawiać z Kiro

**✅ DOBRE przykłady:**
```
"Znajdź wszystkie pliki Python które używają ChromaDB"
"Pokaż mi schemat tabeli entities w DSQL"
"Stwórz endpoint API dla multi-tenant SaaS"
"Zmigruj tę funkcję na AWS Lambda"
```

**❌ ZŁE przykłady:**
```
"Czy możesz..." (nie pytaj, po prostu powiedz co chcesz)
"Spróbuj znaleźć..." (Kiro nie próbuje, Kiro robi)
"Może byś sprawdził..." (bądź konkretny)
```

## CZĘŚĆ 2: KONFIGURACJA AWS POWERS

### 2.1 Sprawdzenie Obecnej Konfiguracji

Masz już zainstalowane 2 Powers:
- **aurora-dsql** - PostgreSQL-compatible serverless database
- **saas-builder** - Multi-tenant SaaS architecture

### 2.2 Konfiguracja MCP dla AWS

Twój plik: `server wiedzy/.kiro/settings/mcp.json`


**Twoja obecna konfiguracja:**
```json
{
  "aions-context": "✅ DZIAŁA - Twój główny MCP server",
  "aurora-dsql": "✅ SKONFIGUROWANY - Połączony przez WSL Ubuntu",
  "aws-core": "✅ AKTYWNY - AWS documentation & best practices",
  "nonicatab-revit": "✅ AKTYWNY - Revit integration"
}
```

### 2.3 Jak Używać AWS Powers

**KROK 1: Zawsze aktywuj power przed użyciem**
```
"Aktywuj aurora-dsql power"
```

**KROK 2: Używaj konkretnych narzędzi**
```
"Pokaż mi wszystkie tabele w DSQL"
"Wykonaj query: SELECT * FROM entities WHERE tenant_id = 'tenant-123'"
"Stwórz tabelę dla multi-tenant SaaS"
```

**KROK 3: Łącz z AIONS Context**
```
"Znajdź wszystkie pliki które używają DSQL i pokaż mi schematy"
```

## CZĘŚĆ 3: WORKFLOW PATTERNS

### 3.1 Pattern: Eksploracja Projektu

```
1. "Zeskanuj projekt używając project_scan_turbo"
2. "Pokaż mi strukturę plików Python"
3. "Znajdź wszystkie endpointy API"
4. "Przeanalizuj zależności między modułami"
```

### 3.2 Pattern: Praca z AWS DSQL

```
1. "Pokaż wszystkie tabele w DSQL"
2. "Opisz schemat tabeli entities"
3. "Stwórz nową tabelę z tenant isolation"
4. "Wykonaj migrację dodając kolumnę"
```

### 3.3 Pattern: Budowanie SaaS

```
1. "Stwórz multi-tenant API endpoint"
2. "Dodaj tenant_id do wszystkich queries"
3. "Zaimplementuj RBAC authorization"
4. "Dodaj usage metering dla billing"
```

### 3.4 Pattern: Debugging

```
1. "Znajdź wszystkie błędy w logach"
2. "Pokaż mi ostatnie conversation dumps"
3. "Przeszukaj CBMS dla podobnych problemów"
4. "Sprawdź health wszystkich systemów"
```

## CZĘŚĆ 4: AWS BEST PRACTICES

### 4.1 Aurora DSQL - Krytyczne Zasady

**✅ ZAWSZE:**
- Używaj `tenant_id` w każdym query
- Twórz indexy z `ASYNC`: `CREATE INDEX ASYNC idx_name ON table(column)`
- Waliduj foreign keys w aplikacji (DSQL ich nie wymusza!)
- Serializuj arrays/JSON jako TEXT
- Trzymaj transakcje poniżej 3,000 wierszy
- Używaj UUID jako primary keys (nie sequences)

**❌ NIGDY:**
- Nie używaj FOREIGN KEY constraints (nie są wymuszane)
- Nie używaj array types (TEXT[], INTEGER[])
- Nie używaj JSON/JSONB columns
- Nie mieszaj DDL statements w transakcjach
- Nie używaj DEFAULT w ADD COLUMN
- Nie twórz synchronicznych indexów
- Nie przekraczaj 3,000 wierszy per transaction

### 4.2 Multi-Tenant SaaS - Wzorce

**Tenant Isolation:**
```sql
-- ✅ DOBRE
SELECT * FROM entities WHERE tenant_id = $1 AND entity_id = $2

-- ❌ ZŁE (brak tenant_id!)
SELECT * FROM entities WHERE entity_id = $1
```

**DynamoDB Keys:**
```
pk: ${tenantId}#${entityType}#${id}
sk: ${timestamp}
GSI1PK: ${tenantId}
GSI1SK: ${entityType}#${timestamp}
```

**Lambda Authorizer Pattern:**
```javascript
1. Extract tenant context from JWT
2. Extract user roles from JWT
3. Validate parameters
4. Check RBAC permissions
5. Prefix all DB operations with tenant_id
6. Return proper status codes
7. Log with tenant context
```

### 4.3 Money Handling (KRYTYCZNE!)

**✅ ZAWSZE:**
```javascript
// Store as integer cents
amount_cents: 1999  // represents $19.99

// Include currency
{
  amount_cents: 1999,
  currency: "USD"
}

// Calculate
const total = (price_cents * quantity) / 100
```

**❌ NIGDY:**
```javascript
// NEVER use floats for money!
amount: 19.99  // ❌ BŁĄD!
```

## CZĘŚĆ 5: ZAAWANSOWANE TECHNIKI

### 5.1 Używanie Context Memory

**Zapisywanie do pamięci:**
```
"Zapamiętaj że używamy tenant_id jako pierwszy parametr w każdym query"
"Zapisz do pamięci że nasza architektura to multi-tenant SaaS"
```

**Przeszukiwanie pamięci:**
```
"Przypomnij mi jak implementowaliśmy tenant isolation"
"Znajdź w pamięci wszystkie decyzje architektoniczne"
```

### 5.2 Conversation Dumps

Kiro automatycznie zapisuje rozmowy w `logs/conversation_dumps/`

**Przeszukiwanie historii:**
```
"Pokaż mi rozmowy z ostatniego tygodnia"
"Znajdź wszystkie rozmowy o DSQL"
```

### 5.3 CBMS (Context-Based Memory System)

CBMS to twoja wiedza domenowa w ChromaDB.

**Przeszukiwanie:**
```
"Szukaj w CBMS: AWS Lambda best practices"
"Znajdź w CBMS: multi-tenant patterns"
```

### 5.4 Browser Automation

Masz dostęp do Playwright przez AIONS Context:

```
"Otwórz AWS Console w przeglądarce"
"Zrób screenshot dashboardu"
"Wypełnij formularz rejestracji"
```

## CZĘŚĆ 6: TROUBLESHOOTING

### 6.1 Problemy z MCP Servers

**Problem: MCP server nie odpowiada**
```
1. "Sprawdź status wszystkich MCP servers"
2. Restart Kiro
3. Sprawdź logi w .kiro/logs/
```

**Problem: Aurora DSQL connection timeout**
```
1. Token wygasa po 15 minutach
2. Automatycznie regeneruje się przy następnym query
3. Sprawdź AWS credentials: aws configure list
```

### 6.2 Problemy z AWS

**Problem: "Foreign key constraint not supported"**
```
Rozwiązanie:
1. Usuń FOREIGN KEY z DDL
2. Waliduj w aplikacji przed INSERT
3. Sprawdź dependents przed DELETE
```

**Problem: "Transaction exceeds 3000 rows"**
```
Rozwiązanie:
1. Podziel na batche po 500-1000 wierszy
2. Przetwarzaj każdy batch osobno
3. Dodaj WHERE clause żeby ograniczyć scope
```

**Problem: "Please use CREATE INDEX ASYNC"**
```
Rozwiązanie:
-- ❌ ZŁE
CREATE INDEX idx_name ON table(column);

-- ✅ DOBRE
CREATE INDEX ASYNC idx_name ON table(column);
```

## CZĘŚĆ 7: QUICK REFERENCE

### 7.1 Najczęściej Używane Komendy

**Eksploracja:**
```
"Zeskanuj projekt"
"Pokaż strukturę plików"
"Znajdź wszystkie pliki Python"
"Opisz schemat bazy danych"
```

**AWS DSQL:**
```
"Pokaż tabele w DSQL"
"Opisz tabelę entities"
"Wykonaj query: SELECT..."
"Stwórz tabelę z tenant isolation"
```

**Pamięć i Historia:**
```
"Szukaj w pamięci: [temat]"
"Pokaż ostatnie rozmowy"
"Zapamiętaj: [informacja]"
"Szukaj w CBMS: [temat]"
```

**Debugging:**
```
"Sprawdź health systemów"
"Pokaż błędy w logach"
"Znajdź problemy w kodzie"
"Przeanalizuj performance"
```

### 7.2 Skróty Klawiszowe (w Kiro IDE)

```
#File          → Dodaj plik do kontekstu
#Folder        → Dodaj folder do kontekstu
#Problems      → Pokaż problemy w kodzie
#Terminal      → Pokaż terminal output
#Git Diff      → Pokaż zmiany git
#Codebase      → Przeszukaj całą bazę kodu
```

### 7.3 MCP Tools Quick Reference

**AIONS Context:**
- `fast_search` - Szukaj plików (Everything)
- `memory_recall` - Szukaj w ChromaDB
- `cbms_search` - Wiedza domenowa
- `project_search` - Szukaj w projekcie
- `conv_history` - Historia rozmów
- `browser_navigate` - Otwórz URL
- `git_status` - Status git
- `docker_ps` - Lista kontenerów

**Aurora DSQL:**
- `readonly_query` - SELECT queries
- `transact` - INSERT/UPDATE/DELETE
- `get_schema` - Schemat tabeli
- `dsql_search_documentation` - Szukaj w docs

**AWS Knowledge:**
- `aws___search_documentation` - Szukaj AWS docs
- `aws___read_documentation` - Czytaj AWS docs
- `aws___get_regional_availability` - Sprawdź dostępność w regionach
- `aws___list_regions` - Lista regionów AWS

## CZĘŚĆ 8: PRZYKŁADY REAL-WORLD

### 8.1 Przykład: Stworzenie Multi-Tenant API

```
USER: "Stwórz endpoint API dla entities z tenant isolation"

KIRO wykonuje:
1. Sprawdza schemat DSQL
2. Tworzy Lambda function z authorizer
3. Dodaje tenant_id validation
4. Implementuje RBAC
5. Dodaje error handling
6. Tworzy testy
```

### 8.2 Przykład: Migracja Bazy Danych

```
USER: "Dodaj kolumnę status do tabeli entities"

KIRO wykonuje:
1. Sprawdza obecny schemat
2. ALTER TABLE ADD COLUMN status VARCHAR(50)
3. UPDATE entities SET status = 'active' WHERE status IS NULL
4. CREATE INDEX ASYNC idx_entities_status ON entities(tenant_id, status)
5. Weryfikuje migrację
```

### 8.3 Przykład: Debugging Production Issue

```
USER: "Znajdź dlaczego query jest wolne"

KIRO wykonuje:
1. Sprawdza query plan
2. Analizuje indexy
3. Szuka w logach
4. Sprawdza CBMS dla podobnych problemów
5. Proponuje optymalizacje
```

## CZĘŚĆ 9: ZAAWANSOWANA KONFIGURACJA

### 9.1 Dodawanie Nowych MCP Servers

**Krok 1: Znajdź server w katalogu**
```
"Szukaj MCP servers dla [technologia]"
```

**Krok 2: Dodaj do mcp.json**
```json
{
  "mcpServers": {
    "new-server": {
      "command": "uvx",
      "args": ["package-name@latest"],
      "env": {
        "API_KEY": "your-key"
      },
      "disabled": false,
      "autoApprove": ["tool1", "tool2"]
    }
  }
}
```

**Krok 3: Restart Kiro**

### 9.2 Tworzenie Custom Steering Rules

Stwórz plik w `.kiro/steering/custom-rule.md`:

```markdown
---
inclusion: always
---

# Custom Rule

## When to use
[Opis kiedy stosować]

## Pattern
[Wzorzec do zastosowania]

## Example
[Przykład]
```

### 9.3 Konfiguracja Agent Hooks

**Hook: Auto-test on save**
```
Trigger: On file save (*.py)
Action: Run pytest for changed file
```

**Hook: Update translations**
```
Trigger: On save (en.json)
Action: Update all language files
```

## CZĘŚĆ 10: NAJLEPSZE PRAKTYKI

### 10.1 Organizacja Projektu

```
project/
├── .kiro/
│   ├── settings/
│   │   └── mcp.json          # MCP configuration
│   └── steering/
│       ├── project-standards.md
│       ├── tools-priority.md
│       └── custom-rules.md
├── backend/
│   ├── functions/            # Lambda functions
│   ├── lib/                  # Business logic
│   └── infrastructure/       # IaC (CDK/SAM)
├── frontend/
│   ├── src/
│   └── public/
├── data/
│   └── chroma/              # ChromaDB storage
├── logs/
│   └── conversation_dumps/  # Kiro conversations
└── requirements.txt
```

### 10.2 Workflow dla Nowych Features

```
1. "Szukaj w pamięci podobnych implementacji"
2. "Sprawdź AWS best practices dla [feature]"
3. "Stwórz schemat bazy danych"
4. "Zaimplementuj backend z tenant isolation"
5. "Dodaj testy"
6. "Zapamiętaj decyzje architektoniczne"
```

### 10.3 Code Review Checklist

**Przed commit:**
```
□ Tenant isolation w każdym query
□ RBAC permissions sprawdzone
□ Error handling dodany
□ Logging z tenant context
□ Testy napisane
□ Documentation zaktualizowana
□ DSQL constraints przestrzegane
□ Money handling jako integer cents
```

## CZĘŚĆ 11: RESOURCES

### 11.1 Dokumentacja

- **Kiro Docs**: Wbudowane w IDE (Command Palette → "Kiro: Help")
- **AWS DSQL**: `dsql_search_documentation` tool
- **AWS General**: `aws___search_documentation` tool
- **AIONS Context**: `E:/server wiedzy/mcpServers/VS_CODE_MCP_CODEX/README.md`

### 11.2 Przydatne Pliki

```
E:/server wiedzy/
├── AIONS_MASTER_INSTRUCTIONS.md    # Project overview
├── KIRO_CONFIGURATION_GUIDE.md     # Kiro setup
├── requirements.txt                # Python deps
├── .kiro/steering/                 # Steering rules
└── logs/conversation_dumps/        # Historia rozmów
```

### 11.3 Komendy Diagnostyczne

```
"Sprawdź health wszystkich systemów"
"Pokaż status MCP servers"
"Lista wszystkich Docker containers"
"Sprawdź git status"
"Pokaż ostatnie logi"
```

## CZĘŚĆ 12: NASTĘPNE KROKI

### 12.1 Podstawowy Level (Jesteś tutaj!)

✅ Rozumiesz jak działa Kiro
✅ Znasz hierarchię narzędzi
✅ Umiesz używać AWS Powers
✅ Znasz podstawowe patterns

### 12.2 Intermediate Level

**Do nauczenia:**
- [ ] Tworzenie custom MCP servers
- [ ] Zaawansowane DSQL patterns
- [ ] Multi-region architecture
- [ ] Custom steering rules
- [ ] Agent hooks automation

**Ćwiczenia:**
```
1. "Stwórz kompletny multi-tenant API endpoint"
2. "Zaimplementuj usage-based billing"
3. "Dodaj RBAC z custom roles"
4. "Stwórz migration system dla DSQL"
```

### 12.3 Advanced Level

**Do nauczenia:**
- [ ] Custom Powers development
- [ ] Advanced ChromaDB patterns
- [ ] Multi-tenant observability
- [ ] Cost optimization strategies
- [ ] Disaster recovery patterns

**Projekty:**
```
1. "Zbuduj production-ready SaaS platform"
2. "Zaimplementuj multi-region failover"
3. "Stwórz custom MCP server dla [technologia]"
4. "Zoptymalizuj koszty AWS do minimum"
```

---

## 🎯 QUICK START CHECKLIST

**Zacznij od tego:**

1. ✅ Przeczytaj ten guide
2. ✅ Sprawdź konfigurację: "Pokaż mi konfigurację MCP"
3. ✅ Test AIONS Context: "Zeskanuj projekt"
4. ✅ Test AWS DSQL: "Pokaż tabele w DSQL"
5. ✅ Test pamięci: "Zapamiętaj że używamy multi-tenant architecture"
6. ✅ Pierwszy projekt: "Stwórz prosty API endpoint z tenant isolation"

**Pamiętaj:**
- Kiro **wykonuje**, nie symuluje
- Zawsze używaj **hierarchii narzędzi** (AIONS Context first!)
- **Tenant isolation** w każdym query
- **Integer cents** dla pieniędzy
- **ASYNC indexes** w DSQL
- **Waliduj foreign keys** w aplikacji

---

**Pytania? Po prostu zapytaj:**
```
"Jak zrobić [X]?"
"Pokaż przykład [Y]"
"Znajdź w pamięci [Z]"
```

Kiro jest tutaj żeby ci pomóc! 🚀
