function Invoke-SetupPowerShell {
    [CmdletBinding()]
    param ()

    Set-StrictMode -Version 1
    $ErrorActionPreference = "Stop"

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupRoot = Join-Path "C:\AIOrchestrator\snapshots\profiles" $timestamp
    if (-not (Test-Path $backupRoot)) {
        New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
    }

    $profileTargets = Get-ProfileTargets

    foreach ($target in $profileTargets) {
        Ensure-Directory -Path (Split-Path $target.Path -Parent)
        $originalContent = ""
        if (Test-Path $target.Path) {
            $originalContent = Get-Content -Path $target.Path -Raw -ErrorAction SilentlyContinue
            Backup-File -Source $target.Path -BackupRoot $backupRoot
        }

        $sanitizedContent = Remove-LegacySnippets -Content $originalContent
        $managedBlock = Get-ManagedProfileBlock -ProfileName $target.Name
        $updated = Merge-ManagedBlock -ExistingContent $sanitizedContent -ManagedBlock $managedBlock
        Set-Content -Path $target.Path -Value $updated -Encoding UTF8

        Write-Host ("Updated {0} profile at {1}" -f $target.Name, $target.Path) -ForegroundColor Green
    }

    Update-TerminalSettings -BackupRoot $backupRoot
}

function Get-ProfileTargets {
    $docsCandidates = New-Object System.Collections.Generic.List[string]
    $baseCandidates = @(
        [Environment]::GetFolderPath("MyDocuments")
        (Join-Path $env:USERPROFILE "Documents")
        (Join-Path $env:USERPROFILE "OneDrive\Documents")
        (Join-Path $env:USERPROFILE "OneDrive - Global Banking School\Documents")
    )

    foreach ($candidate in $baseCandidates) {
        if ($candidate -and (Test-Path $candidate) -and -not $docsCandidates.Contains($candidate)) {
            $docsCandidates.Add($candidate) | Out-Null
        }
    }

    if ($docsCandidates.Count -eq 0) {
        $fallbackDoc = [Environment]::GetFolderPath("MyDocuments")
        if ($fallbackDoc) {
            $docsCandidates.Add($fallbackDoc) | Out-Null
        }
    }

    $psCandidates = $docsCandidates | ForEach-Object { Join-Path $_ "PowerShell" }
    $wpsCandidates = $docsCandidates | ForEach-Object { Join-Path $_ "WindowsPowerShell" }

    $psDir = Get-FirstExistingPath -Candidates $psCandidates
    $wpsDir = Get-FirstExistingPath -Candidates $wpsCandidates -Fallback (Join-Path $env:USERPROFILE "Documents\WindowsPowerShell")

    @(
        @{
            Name = "PowerShell 7"
            Path = Join-Path $psDir "Microsoft.PowerShell_profile.ps1"
        },
        @{
            Name = "Windows PowerShell"
            Path = Join-Path $wpsDir "Microsoft.PowerShell_profile.ps1"
        }
    )
}

function Get-FirstExistingPath {
    param(
        [Parameter(Mandatory)]
        [string[]]$Candidates,

        [string]$Fallback
    )

    foreach ($candidate in $Candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    $target = $Candidates[0]
    if (-not $target -and $Fallback) {
        $target = $Fallback
    }

    if (-not (Test-Path $target)) {
        New-Item -ItemType Directory -Path $target -Force | Out-Null
    }

    return $target
}

function Ensure-Directory {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Backup-File {
    param(
        [Parameter(Mandatory)] [string]$Source,
        [Parameter(Mandatory)] [string]$BackupRoot
    )

    if (-not (Test-Path $Source)) {
        return
    }

    $relative = $Source
    if ($Source.StartsWith($env:USERPROFILE)) {
        $relative = $Source.Substring($env:USERPROFILE.Length).TrimStart("\")
    }

    $destination = Join-Path $BackupRoot $relative
    Ensure-Directory -Path (Split-Path $destination -Parent)
    Copy-Item -Path $Source -Destination $destination -Force
}

function Remove-LegacySnippets {
    param([string]$Content)

    return ""
}

function Get-ManagedProfileBlock {
    param([string]$ProfileName)

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $blockTemplate = @'
# >>> AI_ORCHESTRATOR >>>
# Managed block updated {{timestamp}} for {{profileName}}

chcp 65001 > $null
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$pathAdditions = @(
    (Join-Path $env:USERPROFILE ".local\bin"),
    (Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links"),
    "C:\Users\User\AppData\Local\Programs\Python\Python311",
    "C:\Users\User\AppData\Local\Programs\Python\Python311\Scripts",
    "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin",
    "C:\Program Files\Kubernetes\kubectl",
    "C:\Program Files\Amazon\AWSCLIV2",
    "C:\Program Files\Google\Cloud SDK\google-cloud-sdk\bin"
)

$pacRoot = Join-Path $env:USERPROFILE ".nuget\packages\microsoft.powerapps.cli"
if (Test-Path $pacRoot) {
    $pacVersion = Get-ChildItem -Path $pacRoot -Directory -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending | Select-Object -First 1
    if ($pacVersion) {
        $pacTools = Join-Path $pacVersion.FullName "tools"
        if (Test-Path $pacTools) {
            $pathAdditions += $pacTools
        }
    }
}

foreach ($candidate in $pathAdditions) {
    if ($candidate -and (Test-Path $candidate)) {
        $escaped = [regex]::Escape($candidate)
        if ($env:PATH -notmatch "(?i)(^|;)$escaped(;|$)") {
            $env:PATH = "$candidate;$env:PATH"
        }
    }
}

$moduleRoots = @(
    (Join-Path ([Environment]::GetFolderPath("MyDocuments")) "PowerShell\Modules"),
    (Join-Path ([Environment]::GetFolderPath("MyDocuments")) "WindowsPowerShell\Modules"),
    (Join-Path $env:USERPROFILE "Documents\PowerShell\Modules"),
    (Join-Path $env:USERPROFILE "Documents\WindowsPowerShell\Modules")
)

foreach ($root in $moduleRoots) {
    if ($root -and (Test-Path $root)) {
        $escapedRoot = [regex]::Escape($root)
        if ($env:PSModulePath -notmatch "(?i)(^|;)$escapedRoot(;|$)") {
            $env:PSModulePath = "$root;$env:PSModulePath"
        }
    }
}

if ($PSVersionTable.PSVersion.Major -ge 6 -and (Get-Command oh-my-posh -ErrorAction SilentlyContinue)) {
    $themeRoot = if ($env:POSH_THEMES_PATH) { $env:POSH_THEMES_PATH } else { Join-Path $env:LOCALAPPDATA "Programs\oh-my-posh\themes" }
    $themePath = Join-Path $themeRoot "jandedobbeleer.omp.json"
    if (Test-Path $themePath) {
        oh-my-posh init pwsh --config $themePath | Invoke-Expression
    } else {
        oh-my-posh init pwsh | Invoke-Expression
    }
} elseif ($PSVersionTable.PSVersion.Major -lt 6) {
    function Prompt { "PS " + $(Get-Location) + "> " }
}

if (-not (Get-Module -Name PSReadLine -ErrorAction SilentlyContinue)) {
    Import-Module PSReadLine -ErrorAction SilentlyContinue | Out-Null
}

if (Get-Command Set-PSReadLineOption -ErrorAction SilentlyContinue) {
    try {
        Set-PSReadLineOption -EditMode Windows
        Set-PSReadLineOption -PredictionSource HistoryAndPlugin
        Set-PSReadLineOption -PredictionViewStyle ListView
        Set-PSReadLineOption -BellStyle None
        Set-PSReadLineKeyHandler -Chord Ctrl+Space -Function MenuComplete
        Set-PSReadLineKeyHandler -Chord Alt+d -Function DeleteWord
    } catch {
        Write-Verbose "PSReadLine options not applied: $($_.Exception.Message)"
    }
}

function Enter-AIONS {
    param()
    $workspace = Join-Path $env:USERPROFILE "AIONS"
    if (Test-Path $workspace) {
        Set-Location $workspace
        $activation = Join-Path $workspace ".venv\Scripts\Activate.ps1"
        if (Test-Path $activation) {
            & $activation
        }
    } else {
        Write-Host "AIONS workspace not found at $workspace" -ForegroundColor Yellow
    }
}

function Enter-CBMS {
    param()
    $workspace = Join-Path $env:USERPROFILE "_check_2025-09-23\extracted\SOLO_CBMS_RELEASE_V01_2025-09-23"
    if (Test-Path $workspace) {
        Set-Location $workspace
    } else {
        Write-Host "CBMS workspace not found at $workspace" -ForegroundColor Yellow
    }
}

Set-Alias cbms Enter-CBMS -Scope Global
Set-Alias aions Enter-AIONS -Scope Global

if (-not (Get-Command Run-AI -ErrorAction SilentlyContinue)) {
    function Run-AI {
        Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File C:\AIOrchestrator\Runner.ps1" -Verb RunAs
    }
}
# <<< AI_ORCHESTRATOR <<<
'@

    $block = $blockTemplate.Replace("{{timestamp}}", $timestamp).Replace("{{profileName}}", $ProfileName)
    return $block
}

function Merge-ManagedBlock {
    param(
        [string]$ExistingContent,
        [string]$ManagedBlock
    )

    $managedPattern = "# >>> AI_ORCHESTRATOR >>>.*?# <<< AI_ORCHESTRATOR <<<"
    $options = [System.Text.RegularExpressions.RegexOptions]::Singleline

    if ([string]::IsNullOrWhiteSpace($ExistingContent)) {
        return $ManagedBlock
    }

    if ([regex]::IsMatch($ExistingContent, $managedPattern, $options)) {
        return [regex]::Replace($ExistingContent, $managedPattern, $ManagedBlock, $options)
    }

    return ($ExistingContent.TrimEnd() + "`r`n`r`n" + $ManagedBlock)
}

function Update-TerminalSettings {
    param([string]$BackupRoot)

    $settingsPath = Join-Path $env:LOCALAPPDATA "Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json"
    if (-not (Test-Path $settingsPath)) {
        Write-Host "Windows Terminal settings.json not found. Skipping terminal configuration." -ForegroundColor Yellow
        return
    }

    Backup-File -Source $settingsPath -BackupRoot $BackupRoot

    $json = Get-Content -Path $settingsPath -Raw | ConvertFrom-Json

    $desiredDefaultProfile = "{574e775e-4f2a-5b96-ac1e-a2962a402336}"
    $changed = $false

    if ($json.copyOnSelect -ne $true) {
        $json.copyOnSelect = $true
        $changed = $true
    }

    if ($json.defaultProfile -ne $desiredDefaultProfile) {
        $json.defaultProfile = $desiredDefaultProfile
        $changed = $true
    }

    if (-not $json.profiles.defaults) {
        $json.profiles.defaults = @{}
    }

    $defaultsObject = $json.profiles.defaults
    if ($defaultsObject -isnot [hashtable]) {
        $defaults = @{}
        foreach ($prop in $defaultsObject.PSObject.Properties) {
            $defaults[$prop.Name] = $prop.Value
        }
        $json.profiles.defaults = $defaults
        $defaultsObject = $json.profiles.defaults
        $changed = $true
    }

    if (-not $defaultsObject.ContainsKey("startingDirectory") -or $defaultsObject.startingDirectory -ne "%USERPROFILE%") {
        $defaultsObject.startingDirectory = "%USERPROFILE%"
        $changed = $true
    }

    if (-not $defaultsObject.ContainsKey("useAcrylic") -or $defaultsObject.useAcrylic -ne $false) {
        $defaultsObject.useAcrylic = $false
        $changed = $true
    }

    if (-not $json.schemes) {
        $json.schemes = @()
    }

    if ($changed) {
        $json | ConvertTo-Json -Depth 8 | Set-Content -Path $settingsPath -Encoding UTF8
        Write-Host ("Windows Terminal settings updated at {0}" -f $settingsPath) -ForegroundColor Green
    } else {
        Write-Host "Windows Terminal settings already aligned." -ForegroundColor DarkGreen
    }
}

