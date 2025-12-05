[CmdletBinding()]
param(
    [ValidateSet("Menu", "QuickScan", "SetupProfiles", "ProvisioningReport", "EnvironmentReport", "WSLMigration", "AutomationStatus", "CloudPrep")]
    [string]$Action = "Menu",

    [string[]]$Arguments
)

Set-StrictMode -Version 1
$ErrorActionPreference = "Stop"

function Initialize-RunnerContext {
    param(
        [Parameter(Mandatory)]
        [string]$Root
    )

    $paths = @{
        Root       = $Root
        Modules    = Join-Path $Root "modules"
        Logs       = Join-Path $Root "logs"
        Snapshots  = Join-Path $Root "snapshots"
        LogFile    = $null
        Transcript = $null
    }

    foreach ($dir in @($paths.Modules, $paths.Logs, $paths.Snapshots)) {
        if (-not (Test-Path $dir)) {
            New-Item -Path $dir -ItemType Directory -Force | Out-Null
        }
    }

    $dateStamp = Get-Date -Format "yyyy-MM-dd"
    $paths.LogFile = Join-Path $paths.Logs ("runner_app_{0}.log" -f $dateStamp)
    $paths.Transcript = Join-Path $paths.Logs ("runner_transcript_{0}.log" -f $dateStamp)

    foreach ($file in @($paths.LogFile, $paths.Transcript)) {
        if (-not (Test-Path $file)) {
            New-Item -ItemType File -Path $file -Force | Out-Null
        }
    }

    return $paths
}

function Set-RunnerEnvironment {
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

    foreach ($candidate in $pathAdditions) {
        if ($candidate -and (Test-Path $candidate)) {
            $escaped = [regex]::Escape($candidate)
            if ($env:PATH -notmatch "(?i)(^|;)$escaped(;|$)") {
                $env:PATH = "$candidate;$env:PATH"
            }
        }
    }

    $pacRoot = Join-Path $env:USERPROFILE ".nuget\packages\microsoft.powerapps.cli"
    if (Test-Path $pacRoot) {
        $pacVersion = Get-ChildItem -Path $pacRoot -Directory -ErrorAction SilentlyContinue |
            Sort-Object Name -Descending | Select-Object -First 1
        if ($pacVersion) {
            $pacTools = Join-Path $pacVersion.FullName "tools"
            if (Test-Path $pacTools) {
                $escapedPac = [regex]::Escape($pacTools)
                if ($env:PATH -notmatch "(?i)(^|;)$escapedPac(;|$)") {
                    $env:PATH = "$pacTools;$env:PATH"
                }
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
}

function Start-RunnerTranscript {
    param(
        [Parameter(Mandatory)]
        [string]$Path
    )

    if (-not (Test-Path variable:global:RunnerTranscriptActive)) {
        $global:RunnerTranscriptActive = $false
    }

    if (-not $global:RunnerTranscriptActive) {
        try {
            Start-Transcript -Path $Path -Append | Out-Null
            $global:RunnerTranscriptActive = $true
        } catch {
            Write-Warning ("Failed to start transcript: {0}" -f $_.Exception.Message)
        }
    }
}

function Stop-RunnerTranscript {
    if ((Test-Path variable:global:RunnerTranscriptActive) -and $global:RunnerTranscriptActive) {
        try {
            Stop-Transcript | Out-Null
        } catch {
            Write-Warning ("Failed to stop transcript: {0}" -f $_.Exception.Message)
        } finally {
            $global:RunnerTranscriptActive = $false
        }
    }
}

function Write-Log {
    param(
        [Parameter(Mandatory)]
        [ValidateSet("INFO", "WARN", "ERROR")]
        [string]$Level,

        [Parameter(Mandatory)]
        [string]$Message,

        [string]$LogFile
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[{0}] {1} {2}" -f $Level, $timestamp, $Message

    if ($LogFile) {
        Add-Content -Path $LogFile -Value $line
    }

    switch ($Level) {
        "INFO" { Write-Host $line -ForegroundColor Cyan }
        "WARN" { Write-Warning $Message }
        "ERROR" { Write-Error $Message }
    }
}

function Invoke-RunnerAction {
    param(
        [Parameter(Mandatory)]
        [ValidateSet("QuickScan", "SetupProfiles", "ProvisioningReport", "EnvironmentReport", "WSLMigration", "AutomationStatus", "CloudPrep")]
        [string]$Name,

        [object[]]$Arguments,

        [string]$LogFile
    )

    $commandName = switch ($Name) {
        "QuickScan"          { "Invoke-QuickScan" }
        "SetupProfiles"      { "Invoke-SetupPowerShell" }
        "ProvisioningReport" { "Invoke-ProvisioningReport" }
        "EnvironmentReport"  { "Invoke-EnvironmentReport" }
        "WSLMigration"       { "Invoke-WSLMigration" }
        "AutomationStatus"   { "Invoke-AutomationStatus" }
        "CloudPrep"          { "Invoke-CloudPrep" }
    }

    $command = Get-Command -Name $commandName -ErrorAction SilentlyContinue
    if (-not $command) {
        Write-Log -Level "ERROR" -Message ("Module '{0}' is not available." -f $commandName) -LogFile $LogFile
        return
    }

    Write-Log -Level "INFO" -Message ("Running action '{0}'." -f $Name) -LogFile $LogFile
    try {
        if ($Arguments -and $Arguments.Count -eq 1 -and $Arguments[0] -is [hashtable]) {
            & $command @($Arguments[0])
        } elseif ($Arguments) {
            & $command @Arguments
        } else {
            & $command
        }
        Write-Log -Level "INFO" -Message ("Action '{0}' completed." -f $Name) -LogFile $LogFile
    } catch {
        Write-Log -Level "ERROR" -Message ("Action '{0}' failed: {1}" -f $Name, $_.Exception.Message) -LogFile $LogFile
    }
}

function Show-RunnerMenu {
    param(
        [string]$LogFile
    )

    do {
        Write-Host ""
        Write-Host "=== AI Orchestrator Runner ===" -ForegroundColor Green
        Write-Host "[1] Quick Scan drive E:"
        Write-Host "[2] Configure PowerShell/Terminal profiles"
        Write-Host "[3] Provisioning report (winget/pipx/npm)"
        Write-Host "[4] Environment report"
        Write-Host "[5] WSL migration helper"
        Write-Host "[6] Automation status dashboard"
        Write-Host "[7] Cloud & automation bootstrap"
        Write-Host "[Q] Quit"
        Write-Host ""

        $choice = Read-Host "Select option"
        $normalized = if ($choice) { $choice.ToUpperInvariant() } else { "" }

        switch ($normalized) {
            "1" {
                $scanPath = Read-Host "Directory to scan [E:\]"
                if ([string]::IsNullOrWhiteSpace($scanPath)) {
                    $scanPath = "E:\"
                }

                $patternInput = Read-Host "Patterns (comma or semicolon separated) [*.zip;*.exe]"
                if ([string]::IsNullOrWhiteSpace($patternInput)) {
                    $patterns = @("*.zip", "*.exe")
                } else {
                    $patterns = $patternInput -split "[,;]" | ForEach-Object { $_.Trim() } | Where-Object { $_ }
                    if (-not $patterns) {
                        $patterns = @("*.zip", "*.exe")
                    }
                }

                $depthInput = Read-Host "Max depth (-1 for unlimited) [3]"
                $depth = 3
                if (-not [string]::IsNullOrWhiteSpace($depthInput)) {
                    if (-not [int]::TryParse($depthInput, [ref]$depth)) {
                        Write-Log -Level "WARN" -Message "Invalid depth provided. Using default value 3." -LogFile $LogFile
                        $depth = 3
                    }
                }

                $hashPrompt = Read-Host "Compute SHA256 hashes? (y/N)"
                $hashFlag = $hashPrompt -match '^[Yy]'

                $args = @{
                    Path      = $scanPath
                    Patterns  = $patterns
                    MaxDepth  = $depth
                }
                if ($hashFlag) {
                    $args.HashCheck = $true
                }

                Invoke-RunnerAction -Name "QuickScan" -Arguments @($args) -LogFile $LogFile
            }
            "2" { Invoke-RunnerAction -Name "SetupProfiles" -LogFile $LogFile }
            "3" { Invoke-RunnerAction -Name "ProvisioningReport" -LogFile $LogFile }
            "4" { Invoke-RunnerAction -Name "EnvironmentReport" -LogFile $LogFile }
            "5" { Invoke-RunnerAction -Name "WSLMigration" -LogFile $LogFile }
            "6" { Invoke-RunnerAction -Name "AutomationStatus" -LogFile $LogFile }
            "7" { Invoke-RunnerAction -Name "CloudPrep" -LogFile $LogFile }
            "Q" { return }
            default { Write-Log -Level "WARN" -Message ("Unknown option: {0}" -f $choice) -LogFile $LogFile }
        }
    } while ($true)
}

function Test-IsElevated {
    try {
        $current = [Security.Principal.WindowsIdentity]::GetCurrent()
        $principal = New-Object Security.Principal.WindowsPrincipal($current)
        return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    } catch {
        return $false
    }
}

function Assert-Elevation {
    if (-not (Test-IsElevated)) {
        throw "Runner requires administrator privileges."
    }
}

$script:RunnerPaths = Initialize-RunnerContext -Root (Split-Path -Parent $PSCommandPath)
Start-RunnerTranscript -Path $script:RunnerPaths.Transcript
Set-RunnerEnvironment

$script:LoadedRunnerModules = @()
if (Test-Path $script:RunnerPaths.Modules) {
    foreach ($file in Get-ChildItem -Path $script:RunnerPaths.Modules -Filter "*.ps1" -File -ErrorAction SilentlyContinue) {
        try {
            . $file.FullName
            $script:LoadedRunnerModules += $file.BaseName
            Write-Verbose ("Loaded module: {0}" -f $file.Name)
        } catch {
            Write-Warning ("Failed to load module {0}: {1}" -f $file.Name, $_.Exception.Message)
        }
    }
}

try {
    Assert-Elevation

    if ($Action -eq "Menu") {
        Show-RunnerMenu -LogFile $script:RunnerPaths.LogFile
    } else {
        Invoke-RunnerAction -Name $Action -Arguments $Arguments -LogFile $script:RunnerPaths.LogFile
    }
} catch {
    Write-Log -Level "ERROR" -Message $_.Exception.Message -LogFile $script:RunnerPaths.LogFile
    throw
} finally {
    Stop-RunnerTranscript
}
