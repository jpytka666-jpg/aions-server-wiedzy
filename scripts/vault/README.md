# AIONS — lokalny vault sekretów (DPAPI)

Offline, bez płatnego KMS. Szyfrowanie: **Windows DPAPI (CurrentUser)** — odszyfrowanie tylko po zalogowaniu tego samego użytkownika Windows co operator (Marcin). Bez loginu operatora nikt nie odczyta blobów.

## Gdzie co leży

| Co | Ścieżka | Git |
|----|---------|-----|
| Skrypty seal/open | `scripts/vault/` | ✅ tracked |
| Zaszyfrowane bloby + index | `runtime/secrets/vault/` | ❌ gitignored |
| Marker operatora | `runtime/secrets/vault/.aions_operator.key` | ❌ gitignored |
| CBMS (tylko meta) | chunk `KVAULTMETA001` | ✅ bez sekretów |

**Nigdy** nie commituj `client_secret.json`, tokenów OAuth ani zawartości vault.

## Szybki start (Marcin)

1. Pobierz z Google Cloud Console plik OAuth Desktop → np. `client_secret.json`.
2. **Zasealuj** (pierwsze uruchomienie tworzy marker DPAPI):

```powershell
cd "E:\server wiedzy"
.\scripts\aions_python.ps1 scripts\vault\seal_secret.py `
  --input C:\Users\User\Downloads\client_secret.json `
  --vault-id google_oauth_client `
  --label "Google OAuth Desktop — Gmail+Calendar"
```

3. **Usuń** oryginalny plik z Pobranych / przenieś poza repo.
4. **Otwórz** do pliku używanego przez integracje (tylko lokalnie):

```powershell
.\scripts\aions_python.ps1 scripts\vault\open_secret.py `
  --vault-id google_oauth_client `
  --out runtime\secrets\gmail_oauth.json
```

5. Skopiuj ten sam plik jako `google_calendar_oauth.json` jeśli jeden klient obsługuje oba API.
6. Uruchom flow OAuth (`oauth_skeleton.py`) — token trafi do `runtime/secrets/*_token.json`.

## Lista wpisów (bez sekretów)

```powershell
.\scripts\aions_python.ps1 scripts\vault\open_secret.py --list
```

## control_plane / agenci

- CBMS chunk **`KVAULTMETA001`** wskazuje `vault_id` i komendy — **bez plaintext**.
- Integracje czytają `runtime/secrets/*.json` po lokalnym `open_secret.py`.
- **Agenci Cursor/MCP: nigdy nie echo'uj** stdout `open_secret.py` ani zawartości JSON do czatu.
- Przy braku credentials: `NotConfiguredError` — nie zgaduj sekretów.

## Bezpieczeństwo

- DPAPI `CurrentUser` + entropy `AIONS_LOCAL_VAULT_V1`.
- Marker `.aions_operator.key` — dodatkowa brama przed odszyfrowaniem blobów.
- Fallback: `dpapi.ps1` (PowerShell `ProtectedData`) gdy ctypes DPAPI zawiedzie.
- Pliki wyjściowe: chmod `0600` gdzie OS pozwala.

## Id vault (przykłady)

| vault_id | Cel |
|----------|-----|
| `google_oauth_client` | client_secret.json (Gmail + Calendar) |
| `gmail_token` | opcjonalnie seal istniejącego tokena |
| `google_calendar_token` | j.w. |

Nowe id wybieraj stabilnie — index trzyma metadane, blob = `{vault_id}.enc.json`.
