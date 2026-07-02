# AIONS Host Layout (Milestone B)

Docelowy układ plików po `install_aions_host.sh` na Linux host (Oracle ARM, Ubuntu, WSL staging).

## Drzewo katalogów

```text
/opt/aions/                          # lub /srv/aions (--install-root srv)
├── repo/                            # skopiowane repo AIONS (kod + scripts/)
│   ├── .aions/python.env            # profil host-linux (venv + repo paths)
│   ├── scripts/aions-ctl            # wołany po instalacji
│   └── runtime/systemd/user/        # host-specific units (generowane)
└── venv/                            # Python 3.11 venv (requirements-linux.txt)

/var/lib/aions/                      # stan trwały (dane runtime)
├── install-manifest.json            # manifest instalacji
├── data/
│   ├── chroma/                      # ChromaDB embedded
│   └── cbms/                        # CBMS chunks
└── state/
    └── search/                      # indeks aions-linux-index

/var/log/aions/                      # logi systemowe instalacji / host
└── install-health.log               # wynik post-install health

/etc/aions/                          # env host-level (root:aions, 640)
├── aions-runtime.env                # profil host-linux
└── aions-mcp.env                    # env MCP

/home/aions/                         # użytkownik runtime
├── aions/
│   ├── config/
│   │   ├── aions-runtime.env        # kopia/synteza z /etc/aions
│   │   └── aions-mcp.env
│   ├── logs/                        # health.log, mcp.log (systemd user)
│   ├── bin/
│   │   ├── start_aions_mcp.sh
│   │   ├── start_aions_api.sh
│   │   └── aions-ctl -> repo/scripts/aions-ctl
│   ├── state/search/                # opcjonalny mirror user-space
│   └── first-boot.state
└── .config/systemd/user/
    ├── aions-health.service
    ├── aions-health.timer
    └── aions-mcp.service

/mnt/e/aions-repo -> /opt/aions/repo  # compat shim dla aions-ctl (bez zmian core)
```

## Odpowiedzialności

| Ścieżka | Właściciel | Rola |
|---------|------------|------|
| `/opt/aions/repo` | `aions:aions` | Kod aplikacji, niezmienny przez runtime |
| `/opt/aions/venv` | `aions:aions` | Izolowane zależności Python 3.11 |
| `/var/lib/aions` | `aions:aions` | Dane canonical (Chroma, CBMS, indeks) |
| `/var/log/aions` | `aions:aions` | Logi host-level |
| `/etc/aions` | `root:aions` | Konfiguracja referencyjna hosta |
| `~/aions/config` | `aions:aions` | Env aktywny dla systemd user units |
| `~/aions/logs` | `aions:aions` | Logi usług user-space |

## Profile deployment

| Profil | `AIONS_DEPLOYMENT_PROFILE` | Typowy host |
|--------|---------------------------|-------------|
| WSL dev | `wsl-dev` | Windows + WSL2, ścieżki `/mnt/e`, `/mnt/d` |
| Host Linux | `host-linux` | Oracle ARM, Ubuntu server |
| Oracle sample | `oracle-linux` | template w `runtime/systemd/templates/` |

Installer generuje profil `host-linux` z neutralnymi ścieżkami (bez `/mnt/*`).

## Systemd

| Unit | Typ | Opis |
|------|-----|------|
| `aions-health.timer` | timer | Co 15 min health gate |
| `aions-health.service` | oneshot | venv + chromadb verify |
| `aions-mcp.service` | simple | MCP stdio (always-on staging) |

Unity instalowane jako **systemd user** (`systemctl --user`), z `loginctl enable-linger`.

## Manifest

`/var/lib/aions/install-manifest.json` — źródło prawdy o ścieżkach po instalacji.
`first_boot_setup.sh` czyta manifest, jeśli zmienne env nie są ustawione.

## Test prefix (WSL / CI)

```bash
sudo ./install_aions_host.sh --prefix /tmp/aions-host-test --skip-runtime-up
```

Layout pod `/tmp/aions-host-test/opt/aions`, `/tmp/aions-host-test/var/lib/aions`, itd.
