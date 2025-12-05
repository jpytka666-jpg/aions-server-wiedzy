---
inclusion: always
---

# Security Check - Automatyczne Sprawdzanie Bezpieczeństwa

## PRZED KAŻDYM COMMIT:

Kiro MUSI sprawdzić czy nie commituje danych wrażliwych:

### 1. Sprawdź czy są API keys/secrets:

```bash
git diff --cached | grep -E "(sk-proj-|ghp_|gho_|AWS_ACCESS_KEY|AWS_SECRET|AKIA|password.*=|api.*key.*=)"
```

### 2. Jeśli znajdziesz coś podejrzanego:

**ZATRZYMAJ commit i:**
1. Usuń wrażliwe dane z pliku
2. Dodaj plik do `.gitignore`
3. Powiadom użytkownika: "⚠️ UWAGA! Znalazłem potencjalne dane wrażliwe w [plik]. Usunąłem przed commitem."

### 3. Wzorce do wykrywania:

```
sk-proj-.*          # OpenAI API keys
ghp_.*              # GitHub Personal Access Tokens
gho_.*              # GitHub OAuth tokens
AKIA.*              # AWS Access Keys
password\s*=\s*     # Password assignments
api[_-]?key\s*=\s*  # API key assignments
secret\s*=\s*       # Secret assignments
token\s*=\s*        # Token assignments
```

### 4. Pliki które NIGDY nie powinny być w repo:

```
.env
.env.local
.env.production
*.pem
*.key
*_rsa
*_rsa.pub
credentials.json
secrets.json
config.local.json
tokens.json
```

### 5. Foldery które NIGDY nie powinny być w repo:

```
node_modules/
venv/
.venv/
__pycache__/
.aws/
.ssh/
```

## Automatyczny workflow:

```
1. User: zapisuje plik
2. Kiro: sprawdza czy są wrażliwe dane
3. Jeśli TAK: usuwa/ignoruje i ostrzega
4. Jeśli NIE: robi commit + push
```

## Przykład ostrzeżenia:

```
⚠️ UWAGA! Znalazłem API key w pliku config.py
Usunąłem przed commitem.
Dodałem config.py do .gitignore.
Użyj zmiennych środowiskowych zamiast hardcoded keys!
```
