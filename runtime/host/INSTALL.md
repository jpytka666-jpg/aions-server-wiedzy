# AIONS Host Installer — INSTALL.md

Milestone B: jedno polecenie do postawienia runtime AIONS na Linux host.

## Wymagania

- Linux (Ubuntu 22.04+, Oracle ARM, WSL2 ze `systemd=true`)
- `python3.11` + `python3.11-venv`
- `rsync` (opcjonalnie, przyspiesza kopiowanie)
- Root / sudo
- Użytkownik docelowy: `aions` (tworzony automatycznie)

## Szybki start (produkcja)

```bash
cd /path/to/aions-repo/runtime/host
sudo ./install_aions_host.sh --source-repo /path/to/aions-repo
```

Po instalacji:

```bash
sudo -u aions /opt/aions/repo/scripts/aions-ctl status
sudo -u aions /opt/aions/repo/scripts/aions-ctl run-health
```

Oczekiwany wynik: health GREEN (chromadb + python 3.11 OK).

## Opcje instalatora

| Opcja | Opis |
|-------|------|
| `--dry-run` | Pokaż kroki bez wykonania |
| `--skip-runtime-up` | Pomiń `aions-ctl up` (testy layoutu) |
| `--source-repo PATH` | Źródło repo (domyślnie: 2 poziomy nad `runtime/host`) |
| `--install-root opt\|srv` | `/opt/aions` (domyślnie) lub `/srv/aions` |
| `--user NAME` | Użytkownik runtime (domyślnie: `aions`) |
| `--prefix PATH` | Prefiks ścieżek, np. `/tmp/aions-host-test` |
| `--allow-user-install` | Instalacja bez root w `ROOT_PREFIX` (tylko testy `/tmp`) |

## Co robi instalator

1. Tworzy użytkownika `aions` (jeśli brak)
2. Tworzy katalogi: `/opt/aions`, `/var/lib/aions`, `/var/log/aions`, `/etc/aions`
3. Kopiuje repo do `/opt/aions/repo`
4. Tworzy Python 3.11 venv w `/opt/aions/venv`
5. `pip install -r requirements-linux.txt`
6. Generuje `.aions/python.env` (profil host-linux)
7. Zapisuje env w `/etc/aions/`
8. Generuje host-specific systemd user units w repo
9. Zapisuje manifest w `/var/lib/aions/install-manifest.json`
10. Tworzy compat symlink `/mnt/e/aions-repo` (shim dla `aions-ctl`)
11. Uruchamia `first_boot_setup.sh` jako `aions`
12. Woła `aions-ctl up` + health verify

## First-boot (user-space)

`first_boot_setup.sh` — uruchamiany automatycznie przez instalator:

- `~/aions/config/` — env dla systemd user
- `~/aions/logs/` — logi usług
- `~/aions/bin/` — launchery + symlink `aions-ctl`
- `~/.config/systemd/user/` — unity health + mcp
- `loginctl enable-linger aions`

Ręczne uruchomienie:

```bash
sudo -u aions AIONS_HOST_ENV=/etc/aions/aions-runtime.env \
  /opt/aions/repo/runtime/host/first_boot_setup.sh
```

## Test w WSL (bez produkcji)

### Dry-run

```bash
bash runtime/host/install_aions_host.sh --dry-run
```

### Layout test w /tmp (bez sudo)

```bash
bash runtime/host/install_aions_host.sh \
  --prefix /tmp/aions-host-test \
  --skip-runtime-up \
  --allow-user-install \
  --source-repo "$(pwd)"
```

Weryfikacja (WSL 2026-07-02 — PASS):

```bash
TEST=/tmp/aions-host-test
cat "$TEST/var/lib/aions/install-manifest.json"
"$TEST/opt/aions/venv/bin/python" -c "import chromadb; print(chromadb.__version__)"
CHROMA_PATH="$TEST/var/lib/aions/data/chroma" \
  "$TEST/opt/aions/repo/scripts/aions_python.sh" \
  "$TEST/opt/aions/repo/scripts/verify_python_env.py"
```

### Layout test w /tmp (z sudo)

```bash
sudo bash runtime/host/install_aions_host.sh \
  --prefix /tmp/aions-host-test \
  --skip-runtime-up \
  --source-repo "$(pwd)"
```

Weryfikacja:

```bash
ls -la /tmp/aions-host-test/opt/aions/
cat /tmp/aions-host-test/var/lib/aions/install-manifest.json
/tmp/aions-host-test/opt/aions/venv/bin/python -c "import chromadb; print('ok')"
```

### Pełny test WSL (wymaga systemd user)

```bash
sudo bash runtime/host/install_aions_host.sh --source-repo "$(pwd)"
sudo -u aions /opt/aions/repo/scripts/aions-ctl up
```

## Layout

Szczegóły ścieżek: [LAYOUT.md](./LAYOUT.md)

## Zasady

- **Nie edytuj** `aions-ctl` core — installer woła go po instalacji
- **Nie ruszaj** Windows prod (`start_aions_mcp.bat`, `venv` na `E:\`)
- Installer jest **idempotentny** tam, gdzie sensowne (user, katalogi, venv skip)
- `requirements-linux.txt` — bez `pywin32` / `pywinauto`

## Rozwiązywanie problemów

| Problem | Rozwiązanie |
|---------|-------------|
| Brak `python3.11` | `sudo apt install python3.11 python3.11-venv` |
| `systemd user` niedostępny | WSL: `[boot] systemd=true` w `/etc/wsl.conf`, `wsl --shutdown` |
| `aions-ctl up` fail na symlink | Sprawdź `/mnt/e/aions-repo` → `/opt/aions/repo` |
| Health RED | `sudo -u aions /opt/aions/repo/scripts/aions-ctl run-health` |
| MCP nie startuje | `sudo -u aions /opt/aions/repo/scripts/aions-ctl mcp-logs` |

## Milestone C — co dalej

Po Milestone B brakuje m.in.:

- `aions-api.service` w domyślnym `aions-ctl up`
- Timery `aions-scanner` / `aions-index`
- Oracle Cloud provisioning + SSE/HTTP MCP
- Migracja canonical Chroma/CBMS z Windows
- Backup, logrotate, alerting
- Usunięcie compat shim `/mnt/e/aions-repo` po refaktorze `aions-ctl`
