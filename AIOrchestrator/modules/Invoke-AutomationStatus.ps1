function Invoke-AutomationStatus {
    [CmdletBinding()]
    param ()

    Set-StrictMode -Version 1
    $ErrorActionPreference = "Stop"

    Write-Host '=== Local Automation Dashboard ===' -ForegroundColor Green
    Write-Host ''

    Show-ToolStatus
    Write-Host ''
    Show-ShellStatus
    Write-Host ''
    Show-WorkspaceStatus
    Write-Host ''
    Show-NextSteps
}

function Show-ToolStatus {
    Write-Host '[Tooling]' -ForegroundColor Cyan

    $checks = @(
        @{ Name = 'Visual Studio Build Tools'; Result = (Test-VisualStudio) },
        @{ Name = 'Visual Studio Code'; Command = 'code --version' },
        @{ Name = 'Git'; Command = 'git --version' },
        @{ Name = 'Python'; Command = 'python --version' },
        @{ Name = 'Node.js'; Command = 'node --version' },
        @{ Name = 'pipx'; Command = 'pipx --version' },
        @{ Name = 'WSL'; Result = (Test-WSLReady) }
    )

    foreach ($check in $checks) {
        if ($check.ContainsKey('Command')) {
            $version = Invoke-CommandVersion -Command $check.Command
            if ($version) {
                Write-Host (" - {0}: {1}" -f $check.Name, $version) -ForegroundColor DarkGreen
            } else {
                Write-Host (" - {0}: missing" -f $check.Name) -ForegroundColor Yellow
            }
        } else {
            if ($check.Result.Success) {
                Write-Host (" - {0}: {1}" -f $check.Name, $check.Result.Details) -ForegroundColor DarkGreen
            } else {
                Write-Host (" - {0}: {1}" -f $check.Name, $check.Result.Details) -ForegroundColor Yellow
            }
        }
    }
}

function Show-ShellStatus {
    Write-Host '[Shell profiles]' -ForegroundColor Cyan

    $profilePaths = @(
        $PROFILE,
        (Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'WindowsPowerShell\Microsoft.PowerShell_profile.ps1')
    )

    foreach ($path in $profilePaths) {
        if (Test-Path $path) {
            Write-Host (" - {0}: managed" -f $path) -ForegroundColor DarkGreen
        } else {
            Write-Host (" - {0}: missing (Run `Run-AI` -> SetupProfiles)" -f $path) -ForegroundColor Yellow
        }
    }
}

function Show-WorkspaceStatus {
    Write-Host '[Workspace]' -ForegroundColor Cyan

    $logDir = 'C:\AIOrchestrator\logs'
    $envReport = Get-ChildItem -Path $logDir -Filter 'environment_report_*.txt' -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($envReport) {
        Write-Host (" - Environment report : {0} ({1})" -f $envReport.Name, $envReport.LastWriteTime) -ForegroundColor DarkGreen
    } else {
        Write-Host ' - Environment report : missing (Run `Run-AI` -> Environment report)' -ForegroundColor Yellow
    }

    $quickScan = Get-ChildItem -Path $logDir -Filter 'quickscan_*.csv' -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($quickScan) {
        Write-Host (" - Quick scan export  : {0} ({1})" -f $quickScan.Name, $quickScan.LastWriteTime) -ForegroundColor DarkGreen
    } else {
        Write-Host ' - Quick scan export  : missing (Run `Run-AI` -> Quick Scan)' -ForegroundColor Yellow
    }

    $wslStatus = Test-WSLReady
    Write-Host (" - WSL distributions  : {0}" -f $wslStatus.Details) -ForegroundColor DarkGreen
}

function Show-NextSteps {
    Write-Host '[Suggested actions]' -ForegroundColor Cyan
    Write-Host ' 1. Zsynchronizuj VS Code rozszerzenia (`code --list-extensions > vscode-extensions.txt`).' -ForegroundColor Yellow
    Write-Host ' 2. Wykonaj backup Runnera (`git init` w `C:\AIOrchestrator` + README opisujacy workflow).' -ForegroundColor Yellow
    Write-Host ' 3. Dodaj lokalne logowanie (np. JSON w `C:\AIOrchestrator\logs`, Windows EventLog) wedlug playbooka.' -ForegroundColor Yellow
    Write-Host ' 4. Zautomatyzuj instalacje paczek (winget/pipx/npm) - patrz Provisioning report.' -ForegroundColor Yellow
}

function Invoke-CommandVersion {
    param([string]$Command)

    try {
        $output = Invoke-Expression $Command
        $line = ($output -split "`r?`n" | Where-Object { $_ -and $_.Trim() } | Select-Object -First 1)
        return $line.Trim()
    } catch {
        return $null
    }
}

function Test-VisualStudio {
    $vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
    if (-not (Test-Path $vswhere)) {
        return @{ Success = $false; Details = 'vswhere.exe not found' }
    }

    $info = & $vswhere -products * -format json | ConvertFrom-Json | Select-Object -First 1
    if ($info) {
        return @{ Success = $true; Details = $info.installationVersion }
    }

    return @{ Success = $false; Details = 'No Visual Studio instances detected' }
}

function Test-WSLReady {
    $output = & wsl.exe -l -v 2>$null
    if ($LASTEXITCODE -ne 0) {
        return @{ Success = $false; Details = 'WSL not configured' }
    }

    $clean = $output -replace "`0", ''
    $lines = $clean -split "`r?`n" | Where-Object { $_ -and ($_ -notmatch 'NAME\s+STATE') }
    if (-not $lines) {
        return @{ Success = $false; Details = 'No distributions' }
    }

    $names = $lines | ForEach-Object { ($_ -replace '\*', '').Trim() }
    return @{ Success = $true; Details = ($names -join ', ') }
}