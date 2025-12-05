# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Global System & Environment Guidelines

### Environment & Scope (NO WORKSPACE LIMITS)

- You are running on **Windows** inside:
  - `Administrator: Developer PowerShell for VS 2022`
- You may operate on **all local drives**:
  - `C:\`, `D:\`, `E:\` — read and write are allowed.
- Do **not** assume a single "workspace root".
  The user may point you to any path on these drives and you should treat it as valid.

When the user references a path, treat it literally:
- Respect exact directories and files they give you.
- You are allowed to move across directories when it makes sense (e.g. exploring related code, configs, logs).

### Shell & Tools

- Primary shell: **PowerShell** (Developer PowerShell for VS 2022).
- Do **not** switch to Bash / WSL / Git Bash unless the user explicitly asks for it.
- Assume the following tools are available and usable:
  - `git`
  - `python` (at least one 3.x install on PATH)
  - `node`
  - `go`
  - `dotnet` and Visual Studio Build Tools / MSBuild
  - Azure CLI and other VS-related SDKs if discovered on PATH
  - `oh-my-posh` (for prompt only, no logic dependence)
- When proposing commands:
  - Prefer PowerShell syntax.
  - Use tools directly from PATH (no hard-coded absolute paths unless necessary).

If a tool is missing at runtime, report the exact error and suggest a fix instead of silently changing the plan.

### Project & Code Handling

- You are allowed to work with **multiple projects** on different drives:
  - Repos and projects may live anywhere under `C:\`, `D:\`, `E:\`.
  - Use the directory the user is currently in as the default context **unless** they clearly indicate another path.

Typical operations you may perform when asked:
- Inspect and modify code (Python, C#, TS/JS, PowerShell, configs, etc.).
- Run project-specific commands:
  - `pytest`, `python -m ...`
  - `dotnet build`, `dotnet test`
  - `npm install`, `npm run ...`, `node ...`
  - `git status`, `git diff`, `git commit` (if the user asks for it).

Keep style consistent with existing code (PEP 8 for Python, Polish comments for PowerShell, etc.).

### Access, Approvals & Destructive Actions

#### Access
- You may **read** any file under `C:\`, `D:\`, `E:\`.
- You may **write / modify** files anywhere on these drives when the user asks for a change or it is the obvious next step in solving the task.

#### Approvals
- Assume you have permission to:
  - Edit code and configs.
  - Create new files (scripts, configs, docs).
  - Run build/test commands.
- For **high-impact / destructive** actions, you must slow down and be explicit:
  - Deleting or renaming many files or directories.
  - Modifying installation scripts (`install.ps1`, `.bat`, `.msi`, installers).
  - Changing system-wide settings, registry, or global config files.

In those cases:
- First describe what you intend to do.
- Show a summary of the impact (or a diff if editing text files).
- Proceed only when the user confirms or has clearly requested that exact action.

### File Reading & Context (ALWAYS FULL FILES)

When the user asks you to read, understand, or refactor a file:

1. **Read the entire file**, not just the header:
   - Work from the first line to the last line.
   - Do not make assumptions based only on the beginning of the file.

2. If the file is very large and cannot be handled in one go:
   - Process it in **explicit chunks** (e.g. "lines 1–200", "201–400", etc.).
   - Keep track of which parts you have already inspected.
   - Continue until the entire file has been covered, unless the user stops you.

3. For multi-file situations (e.g. code + config + tests):
   - Read **all relevant files** fully before proposing a final change.
   - Pay special attention to:
     - Configuration directories (`config`, JSON/JSONL files).
     - Data/spec files (`kernels`, `graphs`, `weights` metadata).
     - Existing tests.

### Changes, Diffs & Safety Margin

Even with full access, maintain basic discipline:

- Prefer **small, targeted changes** over huge rewrites.
- When editing text files (code, configs, docs):
  - Align with existing formatting and naming.
  - When possible, show diffs or clearly explain:
    - What changed,
    - Why it changed,
    - Which files were touched.

- For scripts and tools that run on the system (PowerShell, `.bat`, `installer.py`):
  - Explain what the script will do after your change.
  - Avoid introducing hidden side effects outside the described scope.

---

## Project Overview

Kodex ESI is a PowerShell tool for EVE Online ESI (Eve Swagger Interface) integration using OAuth PKCE flow. It allows players to:
- Authenticate with EVE Online ESI without requiring a client secret (PKCE public client)
- Store and manage OAuth tokens per character in `%APPDATA%\kodex-esi\tokens.json`
- Fetch character assets with pagination and retry logic
- Export asset data to CSV format

**Language**: PowerShell (Windows)
**Authentication**: OAuth 2.0 with PKCE (Proof Key for Code Exchange)
**API**: EVE Online ESI (https://esi.evetech.net/)

## Core Commands

### Running the Script

```powershell
# Dry-run mode (simulate operations without executing)
.\kodex-esi.ps1 -DryRun

# Normal mode
.\kodex-esi.ps1
```

### Main Functions

```powershell
# Authenticate with EVE ESI (opens browser, receives OAuth callback)
Login-Esi

# Fetch basic assets for a character
Get-EsiAssets -CharacterId 12345678

# Fetch assets with type names (expanded data)
Get-EsiAssetsExpanded -CharacterId 12345678

# List all stored character tokens
List-CharactersFromTokens

# Display help
Show-Help
```

## Architecture

### OAuth PKCE Flow

The authentication flow follows OAuth 2.0 PKCE standard:

1. **Generate PKCE challenge** (`New-Pkce`): Creates code_verifier and code_challenge (SHA256)
2. **Open browser** with authorization URL including code_challenge
3. **Local callback listener** (`Start-LocalListenerAndWaitForCode`): Starts HttpListener on port 8721 to receive authorization code
4. **Exchange code for token** (`Exchange-CodeForToken`): Trades authorization code for access/refresh tokens
5. **Store tokens** in `%APPDATA%\kodex-esi\tokens.json` keyed by character_id

### Token Management

- **Storage**: `%APPDATA%\kodex-esi\tokens.json` - JSON file with character_id as keys
- **Structure**: Each entry contains refresh_token, access_token, expires_at, fetched_at, character_name
- **Auto-refresh**: `Get-AccessTokenForChar` checks token expiration and refreshes if needed (60s before expiry)
- **Retry logic**: Token refresh attempts 3 times with exponential backoff

### Asset Fetching

- **Pagination**: `Get-EsiAssets` loops through pages (ESI returns max ~1000 items per page)
- **Retry logic**: `Invoke-EsiGet` retries failed requests 3 times with exponential backoff
- **Type expansion**: `Get-EsiAssetsExpanded` batches type_ids (100 per batch) to fetch names from `/universe/names/`
- **Output**: CSV files with columns: item_id, type_id, location_id, location_type, quantity, singleton, is_blueprint

## Configuration

### Required Setup (in kodex-esi.ps1)

```powershell
# Line 20: MUST be edited before first use
$Global:ESI_ClientId = "<TU_WKLEJ_CLIENT_ID>"

# Line 22: Redirect URI (must match CCP registration)
$Global:RedirectUri = "http://127.0.0.1:8721/callback"

# Line 24: Local callback port
$Global:CallbackPort = 8721

# Line 26: ESI scopes (can be expanded)
$Global:Scopes = @("esi-characters.read_assets.v1")
```

### CCP Developer Registration

Required before using the tool:
1. Register application at https://developers.eveonline.com/
2. Set Callback URL to exactly: `http://127.0.0.1:8721/callback` (not localhost, not https)
3. Select scope: `esi-assets.read_assets.v1`
4. Copy Client ID (NOT Client Secret - PKCE doesn't use it)
5. Paste Client ID into `$Global:ESI_ClientId` in kodex-esi.ps1 line 20

Detailed step-by-step guide available in CCP-REGISTRATION-GUIDE.md

## File Structure

```
.
├── kodex-esi.ps1                  # Main script (EDIT Client ID here)
├── README.md                      # Full documentation (Polish)
├── QUICK-START.md                 # 5-minute quick start guide
├── CCP-REGISTRATION-GUIDE.md      # Detailed CCP registration walkthrough
├── USAGE-EXAMPLES.md              # 13 practical usage scenarios
├── PROJECT-FILES.md               # File structure documentation
└── tokens.example.json            # Example token file structure

Generated files:
%APPDATA%\kodex-esi\tokens.json    # Stored OAuth tokens (DO NOT SHARE)
assets_<character_id>.csv          # Basic asset export
assets_expanded_<character_id>.csv # Asset export with type names
```

## Security Considerations

- **PKCE flow**: No client secret required or stored (public client)
- **Token storage**: Refresh tokens stored locally in `%APPDATA%\kodex-esi\tokens.json`
- **Scope**: Default scope is read-only (`esi-assets.read_assets.v1`)
- **Important**: `tokens.json` contains long-lived refresh tokens - protect this file
- **HttpListener**: Runs temporarily on 127.0.0.1:8721 during login (300s timeout)

## Common Tasks

### Adding a New ESI Scope

1. Edit line 26 in kodex-esi.ps1 to add scope
2. Update CCP application registration to include new scope
3. Delete existing tokens.json
4. Run `Login-Esi` to re-authorize with new scopes

### Multi-Character Management

```powershell
# Login multiple characters (run Login-Esi multiple times)
$char1 = Login-Esi  # Authorize first character in browser
$char2 = Login-Esi  # Authorize second character in browser

# Fetch assets for all stored characters
$tokens = Load-Tokens
foreach ($id in $tokens.PSObject.Properties.Name) {
    Get-EsiAssets -CharacterId $id
}
```

### Automation with Task Scheduler

See USAGE-EXAMPLES.md Scenario 6 for Task Scheduler setup.
Key points:
- Create wrapper script that loads kodex-esi.ps1
- Use existing tokens (no interactive login during automation)
- Tokens auto-refresh if expired

## Dry-Run Mode

Use `-DryRun` parameter for testing without executing real operations:

```powershell
.\kodex-esi.ps1 -DryRun
Login-Esi  # Shows OAuth URL but doesn't open browser or listen
Get-EsiAssets -CharacterId 12345678  # Shows what would be fetched
```

Useful for:
- Verifying OAuth URL construction
- Testing logic without API calls
- Checking configuration before real use

## Troubleshooting

### "ESI_ClientId jest pusty"
Edit line 20 in kodex-esi.ps1 to paste your Client ID

### "Nie udało się uruchomić HttpListener"
- Check if port 8721 is available: `netstat -an | findstr 8721`
- May need admin privileges for HttpListener
- Check Windows Firewall settings

### "State mismatch"
Callback URL in CCP registration must exactly match `$Global:RedirectUri` (http://127.0.0.1:8721/callback)

### "Brak tokenów dla characterId"
Run `Login-Esi` first to authenticate the character

### Token refresh failures
- Check if refresh token is valid (not revoked in EVE settings)
- Verify Client ID hasn't changed
- Check network connectivity to login.eveonline.com

## Important Notes for Code Modifications

- **Line 20 is user-configurable**: Never hardcode Client ID in commits
- **Pagination logic**: ESI assets endpoint returns variable page sizes; loop until empty response
- **Token expiration**: Refresh tokens 60 seconds before expiry to avoid race conditions
- **State parameter**: Always validate OAuth state to prevent CSRF attacks
- **Error handling**: Most ESI calls have 3-retry exponential backoff
- **Encoding**: CSV exports use UTF-8 encoding for international character names
- **HttpListener security**: Only listens on 127.0.0.1 (localhost), times out after 300s

## Documentation

All documentation is in Polish (target audience is Polish EVE Online players).

- **README.md**: Complete project documentation, FAQ, troubleshooting
- **QUICK-START.md**: Fast 5-minute getting started guide
- **CCP-REGISTRATION-GUIDE.md**: Step-by-step CCP developer portal registration
- **USAGE-EXAMPLES.md**: 13 practical scenarios including SQLite export, automation, data analysis
- **PROJECT-FILES.md**: File structure reference

## Testing

No automated test suite. Manual testing workflow:

1. Test dry-run mode: `.\kodex-esi.ps1 -DryRun`
2. Test login: `Login-Esi` (opens browser, completes OAuth flow)
3. Test basic fetch: `Get-EsiAssets -CharacterId <id>`
4. Test expanded fetch: `Get-EsiAssetsExpanded -CharacterId <id>`
5. Verify CSV output: `Import-Csv assets_<id>.csv`
