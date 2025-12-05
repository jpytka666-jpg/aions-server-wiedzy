function Invoke-ProvisioningReport {
    [CmdletBinding()]
    param ()

    Set-StrictMode -Version 1
    $ErrorActionPreference = "Stop"

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $snapshotRoot = Join-Path "C:\AIOrchestrator\snapshots\provisioning" $timestamp
    Ensure-Directory -Path $snapshotRoot

    $logs = @()

    $wingetExport = Join-Path $snapshotRoot "winget-packages.json"
    Write-Host "Exporting winget package list..." -ForegroundColor Cyan
    try {
        winget export --output $wingetExport --include-versions --accept-source-agreements --accept-package-agreements | Out-Null
        $logs += "winget export -> $wingetExport"
    } catch {
        Write-Warning ("winget export failed: {0}" -f $_.Exception.Message)
    }

    $pipxPath = Join-Path $snapshotRoot "pipx-list.txt"
    Write-Host "Collecting pipx packages..." -ForegroundColor Cyan
    $pipxCommand = Get-Command pipx -ErrorAction SilentlyContinue
    if ($pipxCommand) {
        try {
            & $pipxCommand.Source list | Set-Content -Path $pipxPath -Encoding UTF8
            $logs += "pipx list -> $pipxPath"
        } catch {
            Write-Warning ("pipx list failed: {0}" -f $_.Exception.Message)
        }
    } else {
        Write-Warning "pipx command not found on PATH. Skipping pipx export."
    }

    $pythonPath = Join-Path $snapshotRoot "python-freeze.txt"
    Write-Host "Collecting Python packages (python -m pip)..." -ForegroundColor Cyan
    try {
        python -m pip list --format=freeze | Set-Content -Path $pythonPath -Encoding UTF8
        $logs += "python pip list -> $pythonPath"
    } catch {
        Write-Warning ("python pip list failed: {0}" -f $_.Exception.Message)
    }

    $npmPath = Join-Path $snapshotRoot "npm-global.txt"
    Write-Host "Collecting global npm packages..." -ForegroundColor Cyan
    try {
        npm list -g --depth=0 | Set-Content -Path $npmPath -Encoding UTF8
        $logs += "npm list -> $npmPath"
    } catch {
        Write-Warning ("npm list failed: {0}" -f $_.Exception.Message)
    }

    $powershellModulesPath = Join-Path $snapshotRoot "powershell-modules.txt"
    Write-Host "Collecting installed PowerShell modules..." -ForegroundColor Cyan
    try {
        Get-InstalledModule | Sort-Object Name | Format-Table Name, Version -AutoSize | Out-String | Set-Content -Path $powershellModulesPath -Encoding UTF8
        $logs += "Get-InstalledModule -> $powershellModulesPath"
    } catch {
        Write-Warning ("Collecting PowerShell modules failed: {0}" -f $_.Exception.Message)
    }

    $reportPath = Join-Path $snapshotRoot "provisioning-summary.txt"
    $summary = @()
    $summary += "Provisioning snapshot created: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    $summary += "Snapshot folder: $snapshotRoot"
    $summary += ""
    $summary += "Artifacts:"
    foreach ($entry in $logs) {
        $summary += " - $entry"
    }

    $summary += ""
    $summary += "Next steps:"
    $summary += " 1. Review winget export for packages needing manual approval."
    $summary += " 2. Mirror pipx/python/npm lists to infrastructure as code (winget import, requirements.txt)."
    $summary += " 3. Enrich snapshot with private feeds once network approval is granted."

    $summary | Set-Content -Path $reportPath -Encoding UTF8

    Write-Host "Provisioning snapshot written to $snapshotRoot" -ForegroundColor Green
}

function Ensure-Directory {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}
