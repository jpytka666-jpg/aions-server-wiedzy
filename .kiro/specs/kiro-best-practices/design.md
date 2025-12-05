# Design Document

## Overview

Implementacja Kiro Best Practices Boilerplate składa się z trzech głównych komponentów:
1. **Master MCP Config** - jednolita konfiguracja bez duplikatów
2. **14 Agent Hooks** - automatyzacja workflow (Tier 1-3)
3. **2 Steering Rules** - product.md i tech.md

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    KIRO BEST PRACTICES                      │
├─────────────────────────────────────────────────────────────┤
│  MASTER MCP CONFIG (.kiro/settings/mcp.json)               │
│  ├── TIER 1: AIONS-CONTEXT (główny, priorytet 0)           │
│  ├── TIER 2: aurora-dsql (bezpośrednie połączenie)         │
│  ├── TIER 3: fetch (web requests)                          │
│  └── DISABLED: duplikaty Powers (stripe, dynamodb, etc.)   │
├─────────────────────────────────────────────────────────────┤
│  AGENT HOOKS (.kiro/hooks/)                                │
│  ├── TIER 1 (Auto): 4 hooki na onFileSave                  │
│  ├── TIER 2 (Manual): 5 hooków z przyciskami               │
│  ├── TIER 3 (Optional): 4 hooki zaawansowane               │
│  └── EXISTING: 3 hooki (git commit/push/backup)            │
├─────────────────────────────────────────────────────────────┤
│  STEERING RULES (.kiro/steering/)                          │
│  ├── EXISTING: 9 rules                                     │
│  └── NEW: product.md, tech.md                              │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Master MCP Config

**Plik:** `.kiro/settings/mcp.json`

**Struktura priorytetów:**
- **Priorytet 0:** AIONS-CONTEXT (zawsze aktywny, główny serwer)
- **Priorytet 1:** aurora-dsql (bezpośrednie połączenie AWS)
- **Priorytet 2:** fetch (web requests)
- **Disabled:** Wszystkie duplikaty Powers (stripe, aws-knowledge, dynamodb, serverless, playwright)

### 2. Agent Hooks Structure

**Tier 1 - Auto (onFileSave):**
| Hook | Trigger | Action |
|------|---------|--------|
| auto-test-python.json | *.py save | Run pytest |
| auto-lint-python.json | *.py save | Run ruff/flake8 |
| auto-security-scan.json | code save | Scan for secrets |
| auto-validate-config.json | *.json/*.yaml save | Validate syntax |

**Tier 2 - Manual (button click):**
| Hook | Button | Action |
|------|--------|--------|
| manual-validate-mcp.json | "Validate MCP" | Test MCP connections |
| manual-validate-env.json | "Validate Env" | Check .env files |
| manual-api-schema.json | "API Schema" | Validate OpenAPI |
| manual-commit-helper.json | "Commit Helper" | Generate commit msg |
| manual-spell-check.json | "Spell Check" | Check README spelling |

**Tier 3 - Optional (advanced):**
| Hook | Button | Action |
|------|--------|--------|
| optional-test-mcp.json | "Test MCP" | Test MCP with samples |
| optional-check-deps.json | "Check Deps" | Check outdated packages |
| optional-coverage.json | "Coverage" | Run coverage report |
| optional-performance.json | "Performance" | Analyze performance |

### 3. Steering Rules

**Nowe pliki:**
- `product.md` - Wizja projektu AIONS, cele, użytkownicy
- `tech.md` - Stack technologiczny (Python, FastAPI, ChromaDB, MCP, AWS)

## Data Models

### Hook JSON Schema

```json
{
  "name": "string",
  "description": "string",
  "enabled": true,
  "trigger": {
    "type": "onFileSave|onAgentComplete|onNewSession|manual",
    "filePattern": "glob pattern (optional)"
  },
  "action": {
    "type": "sendMessage|executeCommand",
    "message": "string (for sendMessage)",
    "command": "string (for executeCommand)"
  }
}
```

## Error Handling

- Hooki z błędami nie blokują workflow
- Błędy są logowane do conversation dumps
- Manual hooki pokazują wynik w panelu Kiro

## Testing Strategy

- Każdy hook testowany przez ręczne wyzwolenie
- MCP config testowany przez restart Kiro
- Steering rules testowane przez sprawdzenie czy agent je ładuje
