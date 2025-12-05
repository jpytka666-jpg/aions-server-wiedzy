function Invoke-QuickScan {
    [CmdletBinding()]
    param(
        [string]$Path = "E:\",

        [string[]]$Patterns = @("*"),

        [switch]$HashCheck,

        [int]$MaxDepth = 3
    )

    Set-StrictMode -Version 1
    $ErrorActionPreference = "Stop"

    if (-not (Test-Path $Path)) {
        Write-Host ("Path {0} does not exist." -f $Path) -ForegroundColor Yellow
        return
    }

    $root = Get-Item -LiteralPath $Path
    if (-not $root.PSIsContainer) {
        throw "Quick scan path must be a directory."
    }

    $logDir = Join-Path "C:\AIOrchestrator" "logs"
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $reportPath = Join-Path $logDir ("quickscan_{0}.csv" -f $timestamp)

    $depthLabel = if ($MaxDepth -eq -1) { "unlimited" } else { $MaxDepth }
    Write-Host ("Scanning {0} (max depth {1}) for patterns: {2}" -f $root.FullName, $depthLabel, ($Patterns -join ", ")) -ForegroundColor Cyan

    $results = Search-Directory -Root $root.FullName -Patterns $Patterns -MaxDepth $MaxDepth

    if (-not $results.Count) {
        Write-Host "No matching files detected." -ForegroundColor Yellow
        return
    }

    if ($HashCheck) {
        Write-Host "Hash check requested. Computing SHA256..." -ForegroundColor Cyan
        foreach ($item in $results) {
            try {
                $hash = Get-FileHash -Algorithm SHA256 -LiteralPath $item.FullName
                $item.Hash = $hash.Hash
            } catch {
                $item.Hash = "hash-error"
                Write-Warning ("Failed to hash {0}: {1}" -f $item.FullName, $_.Exception.Message)
            }
        }
    }

    $results |
        Select-Object Name,
                      @{ Name = "Folder"; Expression = { $_.Directory } },
                      @{ Name = "SizeMB"; Expression = { [Math]::Round($_.Length / 1MB, 2) } },
                      LastWriteTime,
                      Hash |
        Export-Csv -Path $reportPath -NoTypeInformation -Encoding UTF8

    $summary = $results | Group-Object -Property Name | Select-Object Name, Count

    Write-Host ""
    Write-Host ("Found {0} files across {1} directories." -f $results.Count, ($results | Select-Object -ExpandProperty Directory -Unique).Count) -ForegroundColor Green
    Write-Host ("Report written to {0}" -f $reportPath) -ForegroundColor Green
    Write-Host ""
    Write-Host "Top duplicates by name:"
    $summary | Sort-Object Count -Descending | Select-Object -First 10 | Format-Table -AutoSize
}

function Search-Directory {
    param(
        [Parameter(Mandatory)] [string]$Root,
        [Parameter(Mandatory)] [string[]]$Patterns,
        [int]$MaxDepth = 3
    )

    $queue = New-Object System.Collections.Generic.Queue[psobject]
    $queue.Enqueue([pscustomobject]@{ Path = $Root; Depth = 0 })

    $matches = New-Object System.Collections.Generic.List[psobject]

    while ($queue.Count -gt 0) {
        $current = $queue.Dequeue()
        $currentPath = $current.Path
        $depth = $current.Depth

        try {
            $files = Get-ChildItem -LiteralPath $currentPath -File -ErrorAction Stop
            foreach ($file in $files) {
                if (Test-PatternMatch -FileName $file.Name -Patterns $Patterns) {
                    $matches.Add([pscustomobject]@{
                        Name         = $file.Name
                        FullName     = $file.FullName
                        Directory    = $file.DirectoryName
                        Length       = $file.Length
                        LastWriteTime = $file.LastWriteTime
                        Hash         = $null
                    }) | Out-Null
                }
            }

            if ($MaxDepth -eq -1 -or $depth -lt $MaxDepth) {
                $directories = Get-ChildItem -LiteralPath $currentPath -Directory -ErrorAction Stop
                foreach ($dir in $directories) {
                    $queue.Enqueue([pscustomobject]@{ Path = $dir.FullName; Depth = $depth + 1 })
                }
            }
        } catch {
            Write-Warning ("Skipping {0}: {1}" -f $currentPath, $_.Exception.Message)
        }
    }

    return $matches
}

function Test-PatternMatch {
    param(
        [Parameter(Mandatory)] [string]$FileName,
        [Parameter(Mandatory)] [string[]]$Patterns
    )

    foreach ($pattern in $Patterns) {
        if ($FileName -like $pattern) {
            return $true
        }
    }
    return $false
}
