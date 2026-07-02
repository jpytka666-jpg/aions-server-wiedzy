# AIONS Host — Milestone C + D prep (tasks)

## Milestone C — reproducible install validation

- [x] `runtime/host/validate_install.sh` — post-install validation (layout / reboot / health)
- [x] Checklist install → reboot simulation → health green (`test_install_in_vm.md`)
- [x] Dokumentacja testów na czystej VM Ubuntu 22.04/24.04 (`test_install_in_vm.md`)

## Milestone D prep — host image groundwork

- [x] `runtime/host/build_host_image_notes.md` — wymagania obrazu przed ISO
- [x] `runtime/host/packer/aions-host.pkr.hcl` — Packer stub
- [x] `runtime/host/templates/cloud-init-user-data.example.yaml` — przykład cloud-init

## Zasady (nie naruszone)

- [x] Bez edycji `install_aions_host.sh`
- [x] Bez edycji `aions-ctl` i aktywnych systemd units
