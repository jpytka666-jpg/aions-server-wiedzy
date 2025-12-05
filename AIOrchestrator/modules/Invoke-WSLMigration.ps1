function Invoke-WSLMigration {
    [CmdletBinding(SupportsShouldProcess = $true)]
    param(
        [string]$Distribution,

        [string]$DestinationRoot = "E:\WSLExports",

        [switch]$Export
    )

    Set-StrictMode -Version 1
    $ErrorActionPreference = "Stop"

    Write-Host "Collecting WSL distribution data..." -ForegroundColor Cyan
    $wslRaw = & wsl.exe -l -v 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Unable to query WSL distributions. Ensure WSL is installed."
        return
    }

    $lines = @()
    foreach ($rawLine in ($wslRaw -split "`r?`n")) {
        $cleanLine = ($rawLine -replace "`0", "").TrimEnd()
        if (-not $cleanLine) {
            continue
        }
        if ($cleanLine -match "NAME\s+STATE\s+VERSION") {
            continue
        }
        $lines += $cleanLine
    }
    $distributions = @()
    foreach ($line in $lines) {
        $record = $line
        $isDefault = $false
        if ($record.TrimStart().StartsWith("*")) {
            $isDefault = $true
            $record = $record.Trim().Substring(1).TrimStart()
        } else {
            $record = $record.Trim()
        }

        if (-not $record) {
            continue
        }

        $parts = $record -split "\s{2,}"
        if ($parts.Count -lt 3) {
            continue
        }

        $distributions += [pscustomobject]@{
            Name      = $parts[0].Trim()
            State     = $parts[1].Trim()
            Version   = $parts[2].Trim()
            IsDefault = $isDefault
        }
    }

    if (-not $distributions) {
        Write-Warning "No WSL distributions detected."
        return
    }

    if (-not $Distribution) {
        $Distribution = ($distributions | Where-Object { $_.IsDefault } | Select-Object -First 1).Name
        if (-not $Distribution) {
            $Distribution = $distributions[0].Name
        }
    }

    $selected = $distributions | Where-Object { $_.Name -eq $Distribution } | Select-Object -First 1
    if (-not $selected) {
        Write-Warning ("Distribution '{0}' not found. Available: {1}" -f $Distribution, ($distributions.Name -join ", "))
        return
    }

    Write-Host ("Selected distribution: {0} (State: {1}, Version: {2})" -f $selected.Name, $selected.State, $selected.Version) -ForegroundColor Green

    $packagePath = Get-DistributionPackagePath -DistributionName $selected.Name
    if ($packagePath) {
        Write-Host ("Package path: {0}" -f $packagePath) -ForegroundColor Green
        $vhdxPath = Join-Path $packagePath "LocalState\ext4.vhdx"
        if (Test-Path $vhdxPath) {
            $vhd = Get-Item $vhdxPath
            $sizeGB = [Math]::Round($vhd.Length / 1GB, 2)
            Write-Host ("Virtual disk: {0} ({1} GB)" -f $vhd.FullName, $sizeGB) -ForegroundColor Green
        } else {
            Write-Warning "ext4.vhdx not found in LocalState. Distribution might be stored elsewhere."
        }
    } else {
        Write-Warning "Could not locate Store package directory. Distribution may have been imported manually."
    }

    Write-Host ""
    Write-Host "Suggested export/import workflow:" -ForegroundColor Cyan
    $exportDirSuggestion = (Join-Path $DestinationRoot $selected.Name)
    $exportFileSuggestion = (Join-Path $DestinationRoot ("{0}-{1}.tar" -f $selected.Name, (Get-Date -Format "yyyyMMdd_HHmmss")))
    $importTarget = (Join-Path "E:\WSL\" $selected.Name)
    Write-Host ("  # Export current distro            : wsl --export {0} ""{1}""" -f $selected.Name, $exportFileSuggestion)
    Write-Host ("  # Import to new location (example) : wsl --import {0} ""{1}"" ""{2}"" --version {3}" -f $selected.Name, $importTarget, $exportFileSuggestion, $selected.Version)
    Write-Host ("  # Set as default (optional)        : wsl --set-default {0}" -f $selected.Name)
    Write-Host ""

    if ($Export) {
        Ensure-Directory -Path $DestinationRoot
        $exportFile = Join-Path $DestinationRoot ("{0}-{1}.tar" -f $selected.Name, (Get-Date -Format "yyyyMMdd_HHmmss"))
        if ($selected.State -eq "Running") {
            if ($PSCmdlet.ShouldProcess($selected.Name, "Terminate running WSL distribution")) {
                Write-Host ("Stopping running instance of {0}..." -f $selected.Name) -ForegroundColor Yellow
                & wsl.exe --terminate $selected.Name | Out-Null
                Start-Sleep -Seconds 2
            } else {
                Write-Warning "Distribution is running. Export cancelled."
                return
            }
        }

        if ($PSCmdlet.ShouldProcess($selected.Name, ("Export distribution to {0}" -f $exportFile))) {
            Write-Host ("Exporting {0} → {1}" -f $selected.Name, $exportFile) -ForegroundColor Cyan
            & wsl.exe --export $selected.Name $exportFile
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Export completed successfully." -ForegroundColor Green
            } else {
                Write-Warning ("Export finished with exit code {0}." -f $LASTEXITCODE)
            }
        }
    } else {
        Write-Host "Run again with -Export to create an export tarball automatically." -ForegroundColor Yellow
    }
}

function Get-DistributionPackagePath {
    param([string]$DistributionName)

    $candidateRoot = Join-Path $env:LOCALAPPDATA "Packages"
    if (-not (Test-Path $candidateRoot)) {
        return $null
    }

    $matches = Get-ChildItem -Path $candidateRoot -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like "*$DistributionName*" } |
        Sort-Object LastWriteTime -Descending

    if ($matches) {
        return $matches[0].FullName
    }

    $lxssRoot = Join-Path $env:LOCALAPPDATA "lxss"
    if (Test-Path $lxssRoot) {
        return $lxssRoot
    }

    return $null
}

function Ensure-Directory {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}
