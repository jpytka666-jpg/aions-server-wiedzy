# Automation Roadmap (updated 2025-11-02)

- [x] Audyt systemu (CLI, WSL, IDE)
- [x] Ujednolicenie profili PowerShell / Windows Terminal
- [x] Automatyzacja środowiska deweloperskiego (Run-AI hub + provisioning snapshot)
- [x] Integracja Microsoft 365 / Azure moduły (Az, Microsoft.Graph)
- [x] AI Orchestration (Runner menu: QuickScan, WSLMigration, CloudPrep)
- [ ] Power Platform / Copilot flows (opcjonalne, lokalne scenariusze)
- [ ] Security / logging hardening (lokalne logi, zaszyfrowane sekrety)
- [ ] Observability (lokalne dashboardy, raporty)

Następne działania:
1. `Run-AI` -> Cloud Prep -> przejrzyj checklistę i doinstaluj brakujące narzędzia/rozszerzenia.
2. `Run-AI` -> WSL Migration -> eksport/import na `E:\WSL` wykonany – monitoruj przy kolejnych aktualizacjach.
3. Udokumentuj i zautomatyzuj lokalne flow (Power Automate / Task Scheduler) w `docs/telemetry_playbook.md`.
4. Utwórz repo dotfiles dla `C:\AIOrchestrator`, przygotuj skrypt bootstrap i lokalne logowanie/key store.