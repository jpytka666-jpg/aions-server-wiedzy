function Invoke-EnvironmentReport {
    [CmdletBinding()]
    param ()

    Set-StrictMode -Version 1
    $ErrorActionPreference = "Stop"

    $logDir = Join-Path "C:\AIOrchestrator" "logs"
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $reportPath = Join-Path $logDir ("environment_report_{0}.txt" -f $timestamp)

    $report = New-Object System.Collections.Generic.List[string]
    $report.Add("Environment report generated $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
    $report.Add("")

    $report.Add("PowerShell versions:")
    $report.Add((" - pwsh.exe : {0}" -f (Get-CommandVersion "pwsh.exe" @("-NoLogo", "-NoProfile", "-Command", '$PSVersionTable.PSVersion.ToString()'))))
    $report.Add((" - powershell.exe : {0}" -f (Get-CommandVersion "powershell.exe" @("-NoLogo", "-Command", '$PSVersionTable.PSVersion.ToString()'))))
    $report.Add("")

    $report.Add("CLIs and toolchains:")
    $report.Add((" - Git            : {0}" -f (Get-CommandVersion "git" @("--version"))))
    $report.Add((" - Python         : {0}" -f (Get-CommandVersion "python" @("--version"))))
    $report.Add((" - Node.js        : {0}" -f (Get-CommandVersion "node" @("--version"))))
    $report.Add((" - npm            : {0}" -f (Get-CommandVersion "npm" @("--version"))))
    $report.Add((" - pipx           : {0}" -f (Get-CommandVersion "pipx" @("--version"))))
    $report.Add((" - oh-my-posh     : {0}" -f (Get-CommandVersion "oh-my-posh" @("--version"))))
    $report.Add((" - Azure CLI      : {0}" -f (Get-CommandVersion "az" @("--version"))))
    $report.Add((" - AWS CLI        : {0}" -f (Get-CommandVersion "aws" @("--version"))))
    $report.Add((" - Google Cloud   : {0}" -f (Get-CommandVersion "gcloud" @("--version"))))
    $report.Add("")

    $report.Add("WSL distributions:")
    $wslInfo = Get-WSLStatus
    foreach ($line in $wslInfo) {
        $report.Add(" - $line")
    }
    if (-not $wslInfo) {
        $report.Add(" - (no WSL distributions registered)")
    }
    $report.Add("")

    $report.Add("One-liner shortcuts:")
    $report.Add(" - Run-AI -> C:\AIOrchestrator\Runner.ps1")
    $report.Add(" - Enter-AIONS / Enter-CBMS (defined in profiles)")
    $report.Add("")

    $report.Add("Profile files:")
    $report.Add((" - PowerShell 7 profile : {0}" -f (Join-Path ([Environment]::GetFolderPath("MyDocuments")) "PowerShell\Microsoft.PowerShell_profile.ps1")))
    $report.Add((" - Windows PowerShell   : {0}" -f (Join-Path ([Environment]::GetFolderPath("MyDocuments")) "WindowsPowerShell\Microsoft.PowerShell_profile.ps1")))
    $report.Add("")

    $report.Add("Next actions:")
    $report.Add(" 1. Use provisioning snapshot (Invoke-ProvisioningReport) before network installs.")
    $report.Add(" 2. Sync snapshot with version control or secure storage.")
    $report.Add(" 3. Prepare approval list for additional CLI/tools (kubectl, Azure modules, Microsoft.Graph).")

    $report | Set-Content -Path $reportPath -Encoding UTF8

    Write-Host ("Environment report saved to {0}" -f $reportPath) -ForegroundColor Green
}

function Get-CommandVersion {
    param(
        [Parameter(Mandatory)] [string]$Command,
        [string[]]$Arguments
    )

    try {
        $candidatePaths = New-Object System.Collections.Generic.List[string]

        $primary = Get-Command $Command -ErrorAction SilentlyContinue
        if ($primary) {
            $candidatePaths.Add($primary.Source) | Out-Null
        }

        foreach ($ext in @(".exe", ".cmd", ".bat")) {
            $alt = Get-Command ($Command + $ext) -ErrorAction SilentlyContinue
            if ($alt) {
                if (-not $candidatePaths.Contains($alt.Source)) {
                    $candidatePaths.Add($alt.Source) | Out-Null
                }
            }
        }

        if ($candidatePaths.Count -eq 0) {
            $whereResult = try { & where.exe $Command 2>$null } catch { @() }
            if ($whereResult) {
                foreach ($path in $whereResult) {
                    if ($path) {
                        $normalized = $path.Trim()
                        if (-not [string]::IsNullOrWhiteSpace($normalized) -and -not $candidatePaths.Contains($normalized)) {
                            $candidatePaths.Add($normalized) | Out-Null
                        }
                    }
                }
            }
        }

        if ($candidatePaths.Count -eq 0) {
            return "not installed"
        }

        $executable = $candidatePaths[0]

        if ($env:AI_RUNNER_DEBUG -eq "1") {
            Write-Host ("Executing {0} {1}" -f $executable, ($Arguments -join " ")) -ForegroundColor DarkYellow
        }

        $previousEAP = $ErrorActionPreference
        $ErrorActionPreference = "SilentlyContinue"
        try {
            $output = & $executable @Arguments 2>&1
        } finally {
            $ErrorActionPreference = $previousEAP
        }
        if (-not $output) {
            return "no output"
        }
        $line = ($output -split "`r?`n" | Where-Object { $_ -and $_.Trim() } | Select-Object -First 1)
        if (-not $line) {
            return "no output"
        }
        if ($env:AI_RUNNER_DEBUG -eq "1") {
            Write-Host ("Output captured: {0}" -f $line.Trim()) -ForegroundColor DarkCyan
        }
        return $line.Trim()
    } catch {
        return "not available"
    }
}

function Get-WSLStatus {
    try {
        $output = wsl.exe -l -v 2>$null
        if ($LASTEXITCODE -ne 0) {
            return @()
        }
        $lines = $output -split "`r?`n"
        return $lines |
            ForEach-Object { ($_ -replace "`0", "").Trim() } |
            Where-Object { $_ -and ($_ -notlike "NAME*") }
    } catch {
        return @()
    }
}

