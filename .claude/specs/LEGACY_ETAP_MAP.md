# Legacy Etap → Faza mapowanie

Mapowanie starej numeracji (Etap 0–9, Milestone A–D) na **AIONS OS Roadmap** (Faza 1–10).
Historia zachowana — nowe decyzje projektowe według Faz, nie Etapów.

| Legacy | Nowa Faza | Uwagi |
|--------|-----------|-------|
| Faza 0 (audyt) | — | Zamknięty; wyniki w roadmap v14 appendix |
| Etap 0 — Baseline | Faza 1 (część) | Windows MCP, Chroma, CBMS — baseline prod |
| Etap 1 — WSL staging | Faza 1 | D:\AIONS_DEV, user `aions`, mirror E:→D: |
| Etap 2 — systemd runtime | Faza 1 | `aions-ctl`, health/mcp/api units |
| Etap 3 — MCP Linux / API | Faza 1 + Faza 3 | Runtime slice → Faza 1; Control Plane → Faza 3 |
| Etap 4 — Chroma/CBMS Linux | Faza 2 + Faza 6 | Staging paths; distributed sync → Faza 6 |
| Etap 5 — Linux Index | Faza 1 | `aions-linux-index` — done |
| Etap 6 — Desktop Provider | Faza 1 (Linux slice) | `desktop_provider` linux-native |
| Etap 6.5 — Brain | **Faza 3** | Policy, Planner, Execution Manager |
| Etap 7 — Desktop Shell UI | Faza 4 + Faza 10 | Identity + ecosystem panel |
| Etap 8 — GPU/ML (legacy) | Faza 5 (opcjonalnie) | Nie mylić z **Faza 8 — AIONS Image** |
| Etap 9 — Oracle prod | Faza 2 + Faza 6 | Deploy + distributed |
| Milestone A | Faza 1 | Linux runtime stable |
| Milestone B | Faza 1 | `install_aions_host.sh` |
| Milestone C | Faza 2 | Reproducible VM validation — **PASS** Hyper-V 2026-07-02 |
| Milestone D | **Faza 8** | Packer, cloud-init, image artifacts |

## Nazewnictwo

- **Etap** — deprecated w nowych dokumentach
- **Milestone A–D** — historyczne kamienie runtime/install; zamknięte lub mapowane na Fazy
- **Faza 1–10** — aktywna roadmapa (pytanie: „co sprawi, że AIONS jest coraz bardziej własnym systemem?”)
