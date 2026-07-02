# Build host image — notatki (Milestone D prep)

**Status:** groundwork / stub — **nie** gotowy ISO ani produkcyjny obraz.

Cel: zdefiniować minimalną zawartość VM **zanim** powstanie pełny pipeline Packer/ISO dla Oracle Cloud / on-prem Linux host.

## Co musi być w obrazie VM (pre-ISO)

### Warstwa OS (bazowa)

| Element | Ubuntu 22.04 / 24.04 | Uwagi |
|---------|----------------------|-------|
| `systemd` | tak (domyślnie) | user units + `loginctl enable-linger` |
| `python3.11` + `venv` | pakiet distro lub deadsnakes PPA | zgodność z `.aions/python.env` |
| `git`, `curl`, `jq` | tak | bootstrap repo / walidacja JSON |
| `adduser` / cloud-init | tak | użytkownik `aions` uid 1000 |
| Firewall | `ufw` allow 22 (SSH), opcjonalnie 8765 localhost-only | prod: tylko SSH z bastion |

### Warstwa AIONS host (z `install_aions_host.sh`)

Po pierwszym uruchomieniu instalatora host layout:

```
/opt/aions/repo/              # docelowo: git checkout AIONS (pusta na starcie OK)
/var/lib/aions/
  install-manifest.json
  data/chroma/
  data/cbms/
  state/search/
/var/log/aions/
/etc/aions/aions-runtime.env
```

### Warstwa user first-boot (`first_boot_setup.sh`)

```
/home/aions/aions/config/aions-runtime.env   # kopia z /etc/aions/…
/home/aions/aions/logs/
/home/aions/aions/first-boot.state
/home/aions/.config/systemd/user/            # puste; unity z templates później
```

### Opcjonalnie w obrazie (nie w minimalnym slice)

| Element | Kiedy dodawać |
|---------|----------------|
| Pełne repo AIONS w `/opt/aions/repo` | gdy obraz ma być „runtime-ready” od razu |
| `~/aions/venv` + `requirements-linux.txt` | po stabilizacji ścieżek Chroma/CBMS |
| Unity z `runtime/systemd/templates/` | **nie** kopiować aktywnych unitów WSL dev |
| Chroma/CBMS dane | Etap 4 — migracja canonical; na start puste katalogi |

## Kolejność budowy obrazu (zalecana)

```text
1. Base Ubuntu cloud image (22.04 lub 24.04)
2. cloud-init: user aions, SSH key, packages
3. Copy runtime/host/*.sh → /usr/local/lib/aions/host/
4. install_aions_host.sh (as root)
5. first_boot_setup.sh (as aions) — via cloud-init runcmd lub packer provisioner
6. validate_install.sh --user aions (gate)
7. (opcjonalnie) git clone + venv + validate --with-runtime --strict-health
8. Sysprep / packer cleanup (cloud-init logs, machine-id)
```

## Walidacja przed „zamrożeniem” obrazu

```bash
sudo /usr/local/lib/aions/host/validate_install.sh --user aions
# z runtime:
sudo /usr/local/lib/aions/host/validate_install.sh --user aions --with-runtime --strict-health
```

Exit code `0` = obraz gotowy do snapshot / ISO pipeline.

## Packer stub

Minimalny szkielet: `packer/aions-host.pkr.hcl`

- **Nie uruchamiaj** bez dostosowania `source` i ścieżek repo.
- Provisionery wołają tylko skrypty z `runtime/host/` — bez modyfikacji `aions-ctl`.

## cloud-init

Przykład: `templates/cloud-init-user-data.example.yaml`

- tworzy `aions`
- instaluje pakiety
- kopiuje skrypty (zakłada `aions-host-scripts.tar.gz` w `#cloud-config` include lub `write_files`)
- uruchamia install + first-boot + validate

## Oracle Cloud / ARM — uwagi

| Temat | Rekomendacja |
|-------|----------------|
| Obraz bazowy | Ubuntu 22.04/24.04 aarch64 Canonical |
| Ścieżki | użyj `aions-runtime.oracle.env.example` jako wzorca env (nie kopiuj WSL paths) |
| Chroma | `CHROMA_PATH=/var/lib/aions/data/chroma` lub `/home/aions/aions/data/chroma` po migracji |
| MCP / API | localhost-only; publiczny endpoint dopiero po hardeningu Etap 9 |
| Desktop | `DESKTOP_ENABLED=false` w obrazie host |

## Świadomie poza scope (Milestone D prep)

- Brak gotowego ISO / OCI custom image upload
- Brak automatycznej migracji Chroma z Windows
- Brak modyfikacji `install_aions_host.sh` (agent B)
- Brak podmiany aktywnych unitów WSL dev

## Następny krok (pełny Milestone D)

1. Podpiąć `packer/aions-host.pkr.hcl` do CI (manual trigger)
2. Opublikować base image do OCI / wewnętrznego registry
3. Runbook: VM z obrazu → `validate_install.sh` → Etap 9 deploy checklist
