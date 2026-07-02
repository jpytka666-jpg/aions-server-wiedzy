# Test instalacji AIONS host na czystej VM Ubuntu

Milestone C — powtarzalna walidacja po `install_aions_host.sh` i `first_boot_setup.sh`.

## Wymagania VM

| Parametr | Wartość |
|----------|---------|
| Dystrybucja | Ubuntu Server **22.04 LTS** lub **24.04 LTS** |
| Architektura | `x86_64` lub `aarch64` (Oracle ARM) |
| RAM | min. 2 GB (4 GB zalecane przy venv + Chroma) |
| Dysk | min. 20 GB |
| Użytkownik | `aions` (uid 1000) — utwórz przed first-boot |
| Sieć | dostęp do `git` / mirrorów APT (opcjonalnie przy pełnym runtime) |

**Nie testuj na produkcyjnym WSL dev** — użyj osobnej VM (Hyper-V, VirtualBox, Multipass, cloud).

## Checklist (install → reboot → health green)

| # | Krok | Komenda / akcja | Oczekiwany wynik |
|---|------|-----------------|------------------|
| 1 | Przygotuj czystą VM | Ubuntu 22.04/24.04, aktualizacja APT | `apt update` OK |
| 2 | Utwórz użytkownika runtime | `sudo adduser --disabled-password --gecos "" aions` | `id aions` OK |
| 3 | Skopiuj repo / skrypty host | `git clone` lub `scp` katalog `runtime/host/` | pliki na VM |
| 4 | **Install** host layout | `sudo bash install_aions_host.sh` | exit 0, manifest pod `/var/lib/aions/` |
| 5 | Walidacja layout | `sudo bash validate_install.sh --phase layout` | `fail=0` |
| 6 | First-boot user-space | `sudo -u aions bash first_boot_setup.sh` | `~/aions/config/`, `first-boot.state` |
| 7 | **Reboot simulation** | `sudo bash validate_install.sh --phase reboot` | `CHROMA_PATH` / `AIONS_PATH` zgodne z manifestem |
| 8 | Pełna walidacja host | `sudo bash validate_install.sh --user aions` | `fail=0` (WARN dla pustego repo OK) |
| 9 | (Opcjonalnie) Deploy repo + venv | clone do `/opt/aions/repo`, `python3.11 -m venv`, `pip install -r requirements.txt` | venv aktywny |
| 10 | **Health green** | `sudo bash validate_install.sh --user aions --with-runtime --strict-health` | `runtime health gate GREEN` |
| 11 | Fizyczny reboot VM | `sudo reboot` | po logowaniu: kroki 8–10 nadal OK |

## Szybki start (Multipass / lokalna VM)

```bash
# Na hoście Windows (Multipass) lub Linux
multipass launch 22.04 --name aions-host-test --cpus 2 --memory 4G --disk 20G
multipass shell aions-host-test

# Montuj repo z E: lub D: (nie kopiuj dużych drzew na dysk VM / C:)
multipass mount "E:/server wiedzy" aions-host-test:/mnt/aions-repo
# alternatywa: multipass mount "D:/AIONS_DEV" aions-host-test:/mnt/aions-dev

# Logi testów na hoście Windows
mkdir "E:\server wiedzy\logs\milestone-c-multipass" -Force
multipass mount "E:/server wiedzy/logs/milestone-c-multipass" aions-host-test:/mnt/aions-logs
export LOG_DIR=/mnt/aions-logs
```

Na VM:

```bash
sudo apt-get update
sudo apt-get install -y git python3.11 python3.11-venv curl jq

# Użytkownik runtime
sudo adduser --disabled-password --gecos "" aions
sudo usermod -aG sudo aions   # opcjonalnie, tylko do testów

# Pobierz skrypty host (minimalny zestaw)
sudo mkdir -p /opt/aions/staging
cd /opt/aions/staging
# Wariant A: pełne repo
sudo git clone https://github.com/<org>/aions-server-wiedzy.git repo
cd repo/runtime/host

# Wariant B: tylko skrypty (scp z dev maszyny)
# scp install_aions_host.sh first_boot_setup.sh validate_install.sh user@vm:/tmp/

# === INSTALL ===
sudo bash install_aions_host.sh
sudo bash validate_install.sh --phase layout

# === FIRST BOOT ===
sudo -u aions bash first_boot_setup.sh

# === REBOOT SIM + HEALTH (host-only) ===
sudo bash validate_install.sh --user aions

# === Pełny runtime (gdy repo jest pod /opt/aions/repo) ===
# sudo rsync -a /opt/aions/staging/repo/ /opt/aions/repo/
# sudo chown -R aions:aions /opt/aions/repo
# sudo -u aions bash -lc 'cd /opt/aions/repo && python3.11 -m venv ~/aions/venv && ~/aions/venv/bin/pip install -r requirements-linux.txt'
# sudo bash validate_install.sh --user aions --with-runtime --strict-health
```

## Walidacja w chroot (bez pełnej VM)

Przydatne w CI lub przy budowie obrazu:

```bash
sudo mkdir -p /mnt/aions-root
sudo debootstrap jammy /mnt/aions-root   # lub noble dla 24.04

sudo chroot /mnt/aions-root bash -c '
  apt-get update && apt-get install -y python3 adduser
  adduser --disabled-password --gecos "" aions
'

sudo ROOT_PREFIX=/mnt/aions-root bash install_aions_host.sh /mnt/aions-root
sudo bash validate_install.sh --root /mnt/aions-root --phase layout
```

## Interpretacja wyników

| Status | Znaczenie |
|--------|-----------|
| `[PASS]` | warunek spełniony |
| `[WARN]` | oczekiwane na etapie host-only (np. pusty `AIONS_REPO`, brak venv) |
| `[FAIL]` | instalacja niekompletna lub regresja |

**Health green na czystym hoście (krok 8):** `fail=0`, ewentualne WARN — OK.

**Health green z runtime (krok 10):** `runtime health gate GREEN`, `fail=0`, bez FAIL przy `--strict-health`.

## Czego NIE ruszać w tym teście

- `install_aions_host.sh` — utrzymuje agent B
- `scripts/aions-ctl` i aktywne unity WSL (`aions-health.*`, `aions-mcp.service`)
- Ten dokument i `validate_install.sh` są bezpieczne do iteracji (Milestone C)

## Powiązane artefakty

- `validate_install.sh` — skrypt walidacji
- `build_host_image_notes.md` — co musi być w obrazie przed ISO (Milestone D prep)
- `templates/cloud-init-user-data.example.yaml` — przykład first-boot w chmurze
- `packer/aions-host.pkr.hcl` — stub buildera obrazu

