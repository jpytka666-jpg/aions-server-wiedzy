function Invoke-CloudPrep {
    [CmdletBinding()]
    param ()

    Set-StrictMode -Version 1
    $ErrorActionPreference = "Stop"

    Write-Host "=== Local Automation Bootstrap ===" -ForegroundColor Green
    Write-Host ""

    Show-ToolingChecklist
    Write-Host ""
    Show-PowerShellEnhancements
    Write-Host ""
    Show-IDERecommendations
    Write-Host ""
    Show-NextSteps
}

function Show-ToolingChecklist {
    Write-Host "[Core tooling]" -ForegroundColor Cyan

    $tools = @(
        @{ Name = "Visual Studio Build Tools"; Test = { Test-VisualStudio } ; Hint = "Install via Visual Studio Installer (Build Tools workload)" },
        @{ Name = "Visual Studio Code"; Command = "code" ; Hint = "winget install Microsoft.VisualStudioCode" },
        @{ Name = "Git"; Command = "git" ; Hint = "winget install Git.Git" },
        @{ Name = "Python 3.11+"; Command = "python" ; Hint = "winget install Python.Python.3.11" },
        @{ Name = "Node.js 18+"; Command = "node" ; Hint = "winget install OpenJS.NodeJS" },
        @{ Name = "WSL (Ubuntu)"; Test = { Test-WSLReady } ; Hint = "Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux" }
    )

    foreach ($tool in $tools) {
        $isOk = $false
        $details = ""

        if ($tool.ContainsKey("Command")) {
            $cmd = Get-Command $tool.Command -ErrorAction SilentlyContinue
            if ($cmd) {
                $isOk = $true
                $details = $cmd.Source
            }
        } elseif ($tool.ContainsKey("Test")) {
            $result = & $tool.Test
            $isOk = $result.Success
            $details = $result.Details
        }

        if ($isOk) {
            Write-Host (" - {0}: ready ({1})" -f $tool.Name, $details) -ForegroundColor DarkGreen
        } else {
            Write-Host (" - {0}: missing ({1})" -f $tool.Name, $tool.Hint) -ForegroundColor Yellow
        }
    }
}

function Show-PowerShellEnhancements {
    Write-Host "[Shell enhancements]" -ForegroundColor Cyan

    $enhancers = @("PSReadLine", "oh-my-posh", "Terminal-Icons")
    foreach ($name in $enhancers) {
        $module = Get-Module -Name $name -ListAvailable | Select-Object -First 1
        if ($module) {
            Write-Host (" - {0}: {1}" -f $name, $module.Version) -ForegroundColor DarkGreen
        } else {
            Write-Host (" - {0}: not installed (Install-Module {0})" -f $name) -ForegroundColor Yellow
        }
    }

    Write-Host ""
    Write-Host "Profile path: $PROFILE" -ForegroundColor DarkCyan
    Write-Host "Managed block maintained by Invoke-SetupPowerShell (`Run-AI` -> option 2)." -ForegroundColor DarkCyan
}

function Show-IDERecommendations {
    Write-Host "[IDE / tooling profile]" -ForegroundColor Cyan

    $vsConfigPath = Join-Path $env:USERPROFILE ".config\vs\offline-dev.vsconfig"
    Write-Host (" - vsconfig template: {0}" -f $vsConfigPath) -ForegroundColor DarkCyan
    Write-Host '   (Use vswhere.exe + vs_installer.exe modify --installPath <path> --config <vsconfig>)' -ForegroundColor DarkGray

    Write-Host ""
    Write-Host "Suggested VS Code extensions:" -ForegroundColor DarkCyan
    Write-Host "   ms-python.python, ms-vscode.powershell, esbenp.prettier-vscode, streetsidesoftware.code-spell-checker"
    Write-Host "Export current list with `code --list-extensions > vscode-extensions.txt`." -ForegroundColor DarkGray
}

function Show-NextSteps {
    Write-Host "[Automation ideas]" -ForegroundColor Cyan
    Write-Host " 1. Utworz repo dotfiles dla `C:\AIOrchestrator` (Runner + moduly) i dodaj skrypt bootstrap (kopiuje profile, ustawia PATH)." -ForegroundColor Yellow
    Write-Host " 2. Uzyj `Run-AI` -> Quick Scan, aby monitorowac archiwa / instalatory na E: przed pobraniami." -ForegroundColor Yellow
    Write-Host " 3. Zautomatyzuj instalacje IDE/VS Code rozszerzen (np. `Install-VSCodeExtension.ps1`)." -ForegroundColor Yellow
    Write-Host " 4. Dodaj lokalne logowanie (np. JSON log + Windows Event Log) zamiast zewnetrznych uslug." -ForegroundColor Yellow
}

function Test-VisualStudio {
    $vswhere = Join-Path ${env:ProgramFiles(x86)} "Microsoft Visual Studio\Installer\vswhere.exe"
    if (-not (Test-Path $vswhere)) {
        return @{ Success = $false; Details = "vswhere.exe not found" }
    }

    $info = & $vswhere -products * -format json | ConvertFrom-Json | Select-Object -First 1
    if ($info) {
        return @{ Success = $true; Details = $info.installationVersion }
    }

    return @{ Success = $false; Details = "No VS instances detected" }
}

function Test-WSLReady {
    $output = & wsl.exe -l -v 2>$null
    if ($LASTEXITCODE -ne 0) {
        return @{ Success = $false; Details = "WSL not configured" }
    }

    $clean = $output -replace "`0", ""
    $lines = $clean -split "`r?`n" | Where-Object { $_ -and $_ -notmatch "NAME\s+STATE" }
    $names = $lines | ForEach-Object { ($_ -replace "\*", "").Trim() }

    if ($names) {
        return @{ Success = $true; Details = ($names -join ", ") }
    }

    return @{ Success = $false; Details = "No distributions registered" }
}
