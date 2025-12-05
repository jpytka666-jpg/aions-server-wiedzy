# Runner.ps1 – automation hub

## Goals
- Central launchpad dla zadań automatyzacji Windows / dev / AI.
- Przejrzyste menu tekstowe, obsługa zarówno interaktywna, jak i wiersz poleceń.
- Logowanie wszystkich akcji do `.\logs\YYYY-MM-DD.log`.
- Łatwe dodawanie nowych modułów (ps1 w `.\modules\`).

## Struktura
```
C:\AIOrchestrator\
 ├── Runner.ps1
 ├── modules\
 │    ├── Invoke-QuickScan.ps1
 │    ├── Invoke-SetupPowerShell.ps1
 │    └── ...
 ├── incoming\
 └── logs\
```

## Flow interakcji
1. Główna funkcja `Invoke-AIRunner`:
   - Ładuje moduły z `.\modules`.
   - Sprawdza wymagane uprawnienia (elevated flag).
   - Ustawia `Transcript` do pliku logu.
   - Prezentuje menu:
     ```
     [1] Quick Scan E:
     [2] Konfiguruj profile PowerShell/Terminal
     [3] Provisioning (winget/pipx/npm)
     [4] Raport środowiskowy
     [Q] Wyjście
     ```
   - Przyjmuje wybór użytkownika i uruchamia odpowiednią funkcję.

2. Obsługa parametrów:
   - `Runner.ps1 -Action QuickScan` – bez menu, bezpośrednio uruchamia moduł.
   - `Runner.ps1 -Action Report -Verbose` – wspiera standardowe przełączniki.

3. Logowanie:
   - `Start-Transcript -Path ".\logs\$(Get-Date -Format yyyy-MM-dd).log" -Append`.
   - Po wykonaniu `Stop-Transcript`.
   - Dodatkowo funkcja `Write-Log` (timestamp, poziom: INFO/WARN/ERROR) z zapisem do pliku + ekranu.

4. Obsługa błędów:
   - `try { … } catch { Write-Log -Level Error -Message $_.Exception.Message; }`.
   - W menu powrót po błędzie z informacją.

## Moduły startowe
1. `Invoke-QuickScan.ps1`
   - Parametry: `-Path "E:\" -Patterns @("*.exe", "*.zip") -HashCheck $false`.
   - Działa w 2 trybach:
     - szybkie wyszukiwanie po nazwie (`Get-ChildItem`).
     - opcja pełnego skanowania hashy (na później).
   - Zwraca listę istniejących plików + brakujące.

2. `Invoke-SetupPowerShell.ps1`
   - Konfiguruje profile (PowerShell 5/7, Windows Terminal):
     - Dodaje `oh-my-posh` init, `PSReadLine` ustawienia, aliasy (AIONS, CBMS).
     - Zapewnia idempotencję (sprawdza przed dopisaniem).
   - Eksportuje aktualną konfigurację do `.\snapshots\profiles\date`.

3. `Invoke-ProvisioningReport.ps1`
   - Zbiera `winget list`, `pipx list`, `wsl -l -v`, `Get-ChildItem` profili.
   - Generuje raport tekstowy w `.\logs\system_report_yyyyMMdd_HHmm.txt`.

4. `Invoke-EnvironmentReport.ps1`
   - Krótkie podsumowanie (PS wersje, WSL, CLI narzędzia).

## Rozszerzenia przyszłe
- Integracja z Power Automate Desktop (uruchamianie flow: `Start-Process "C:\Program Files\Power Automate Desktop\PAD.Console.Host.exe"`).
- Integracja Azure/GitHub: `Invoke-AzLogin`, `gh auth status`.
- Menu dynamiczne (na podstawie modułów).
- Web UI (np. z `PSHTML` lub prostym serverem HTTP).

## Wymagania
- PowerShell 5.1+ (działa w Windows PowerShell i Core).
- Uprawnienia administratora (wykorzystujemy `-Verb RunAs` w `Run-AI`).
- Foldery `logs/`, `modules/`, `snapshots/` – Runner tworzy je, jeśli brak.

## Kroki implementacji
1. Utworzyć foldery + szkielet `Runner.ps1`.
2. Zaimplementować narzędzia wspólne (`Write-Log`, `Start-RunnerTranscript`, loader modułów).
3. Dodać moduły Quick Scan i Setup PowerShell (pierwsze funkcje).
4. Przetestować w Developer PowerShell (admin) + PowerShell 7 (`pwsh`).
5. Dodać guardy przed ponowną konfiguracją/prowizją i zapis snapshotów.
6. Dokumentacja w README runnera.
