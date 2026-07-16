<#
.SYNOPSIS
  Audyt źródeł CBMS przed/po kanonicznym przeniesieniu na E:

.DESCRIPTION
  Porównuje trzy lokalizacje chunków CBMS:
    - E:\server wiedzy\aions_core\memory\  (kanoniczny AIONS_PATH)
    - E:\server wiedzy\AIONS_CATALOG\chunks\
    - E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\chunks_unified\  (tylko count jeśli istnieje)

  Zapisuje JSON z liczbami plików, próbkami ścieżek i informacjami z manifestu.

.PARAMETER OutputPath
  Ścieżka pliku wynikowego JSON (domyślnie: logs\cbms_audit_YYYYMMDD.json w repo).

.EXAMPLE
  .\scripts\audit_cbms_sources.ps1
  .\scripts\audit_cbms_sources.ps1 -OutputPath "E:\server wiedzy\logs\cbms_audit_20260703.json"
#>
param(
    [string]$OutputPath = "",
    [int]$SampleCount = 5,
    [int]$HugeThreshold = 10000
)

$ErrorActionPreference = "Stop"

$repoRoot = "E:\server wiedzy"
if (-not $OutputPath) {
    $stamp = Get-Date -Format "yyyyMMdd"
    $OutputPath = Join-Path $repoRoot "logs\cbms_audit_$stamp.json"
}

$sources = [ordered]@{
    operational_memory = "E:\server wiedzy\aions_core\memory"
    catalog_chunks     = Join-Path $repoRoot "AIONS_CATALOG\chunks"
    chunks_unified     = "E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\chunks_unified"
}

function Get-DirAudit {
    param(
        [string]$Path,
        [string]$Label,
        [switch]$CountOnlyIfHuge
    )

    $result = [ordered]@{
        label      = $Label
        path       = $Path
        exists     = $false
        file_count = $null
        dir_count  = $null
        total_bytes = $null
        sample_files = @()
        note       = $null
    }

    if (-not (Test-Path -LiteralPath $Path)) {
        $result.note = "path_not_found"
        return $result
    }

    $result.exists = $true

    if ($CountOnlyIfHuge) {
        # Szybki count bez pełnej enumeracji próbek — tylko jeśli katalog istnieje
        $files = Get-ChildItem -LiteralPath $Path -Recurse -File -ErrorAction SilentlyContinue
        $count = @($files).Count
        $result.file_count = $count
        $result.dir_count = (Get-ChildItem -LiteralPath $Path -Recurse -Directory -ErrorAction SilentlyContinue).Count
        if ($count -le $HugeThreshold) {
            $result.sample_files = @($files | Select-Object -First $SampleCount | ForEach-Object { $_.FullName })
            $result.total_bytes = ($files | Measure-Object -Property Length -Sum).Sum
        }
        else {
            $result.note = "count_only_huge ($count files > threshold $HugeThreshold)"
            # Próbka tylko z pierwszego poziomu
            $result.sample_files = @(Get-ChildItem -LiteralPath $Path -File -ErrorAction SilentlyContinue |
                Select-Object -First $SampleCount |
                ForEach-Object { $_.FullName })
        }
        return $result
    }

    $files = Get-ChildItem -LiteralPath $Path -Recurse -File -ErrorAction SilentlyContinue
    $count = @($files).Count
    $result.file_count = $count
    $result.dir_count = (Get-ChildItem -LiteralPath $Path -Recurse -Directory -ErrorAction SilentlyContinue).Count
    $result.total_bytes = if ($count -gt 0) { ($files | Measure-Object -Property Length -Sum).Sum } else { 0 }
    $result.sample_files = @($files | Select-Object -First $SampleCount | ForEach-Object { $_.FullName })
    return $result
}

function Get-ManifestInfo {
    param([string]$ManifestPath)

    $info = [ordered]@{
        path = $ManifestPath
        exists = $false
        total_chunks = $null
        version = $null
        created = $null
        chunk_index_keys = $null
    }

    if (-not (Test-Path -LiteralPath $ManifestPath)) {
        return $info
    }

    $info.exists = $true
    try {
        $manifest = Get-Content -LiteralPath $ManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $info.version = $manifest.version
        $info.created = $manifest.created
        if ($null -ne $manifest.total_chunks) {
            $info.total_chunks = [int]$manifest.total_chunks
        }
        if ($manifest.chunk_index) {
            $info.chunk_index_keys = @($manifest.chunk_index.PSObject.Properties.Name).Count
        }
    }
    catch {
        $info.note = "parse_error: $($_.Exception.Message)"
    }
    return $info
}

$operationalMemory = $sources.operational_memory
$chunkDirs = @(
    (Join-Path $operationalMemory "chunks"),
    (Join-Path $sources.catalog_chunks ""),
    (Join-Path $sources.chunks_unified "")
) | Where-Object { $_ }

$chunkFileCounts = @{}
foreach ($dir in $chunkDirs) {
    if (Test-Path -LiteralPath $dir) {
        $chunkFileCounts[$dir] = (Get-ChildItem -LiteralPath $dir -Recurse -File -Filter "*.json" -ErrorAction SilentlyContinue).Count
    }
    else {
        $chunkFileCounts[$dir] = $null
    }
}

$canonicalTarget = Join-Path $repoRoot "aions_core"
$canonicalMemory = Join-Path $canonicalTarget "memory"

$report = [ordered]@{
    audit_timestamp = (Get-Date).ToString("o")
    audit_script    = "scripts/audit_cbms_sources.ps1"
    repo_canonical  = $repoRoot
    aions_path_current = $env:AIONS_PATH
    aions_path_expected = $canonicalTarget
    sources = [ordered]@{
        operational_memory = Get-DirAudit -Path $operationalMemory -Label "D operational memory"
        catalog_chunks     = Get-DirAudit -Path $sources.catalog_chunks -Label "E AIONS_CATALOG chunks"
        chunks_unified     = Get-DirAudit -Path $sources.chunks_unified -Label "E chunks_unified" -CountOnlyIfHuge
    }
    chunk_json_counts = $chunkFileCounts
    manifests = [ordered]@{
        operational = Get-ManifestInfo -ManifestPath (Join-Path $operationalMemory "knowledge_manifest.json")
        canonical   = Get-ManifestInfo -ManifestPath (Join-Path $canonicalMemory "knowledge_manifest.json")
        catalog     = Get-ManifestInfo -ManifestPath (Join-Path $repoRoot "AIONS_CATALOG\indices\knowledge_manifest.json")
    }
    junction = [ordered]@{
        path = "D:\AIONS_DEV\cbms"
        exists = (Test-Path -LiteralPath "D:\AIONS_DEV\cbms")
        is_reparse_point = $false
        target = $null
    }
    summary = [ordered]@{
        operational_chunk_files = $chunkFileCounts[(Join-Path $operationalMemory "chunks")]
        manifest_total_chunks   = $null
        catalog_chunk_files     = $chunkFileCounts[$sources.catalog_chunks]
        chunks_unified_files    = $chunkFileCounts[$sources.chunks_unified]
    }
}

if ($report.manifests.operational.total_chunks) {
    $report.summary.manifest_total_chunks = $report.manifests.operational.total_chunks
}
elseif ($report.manifests.canonical.total_chunks) {
    $report.summary.manifest_total_chunks = $report.manifests.canonical.total_chunks
}

if (Test-Path -LiteralPath "D:\AIONS_DEV\cbms") {
    $item = Get-Item -LiteralPath "D:\AIONS_DEV\cbms" -Force
    $report.junction.is_reparse_point = [bool]($item.Attributes -band [IO.FileAttributes]::ReparsePoint)
    if ($report.junction.is_reparse_point) {
        try {
            $report.junction.target = $item.Target
            if ($report.junction.target -is [array]) {
                $report.junction.target = $report.junction.target -join "; "
            }
        }
        catch {
            $report.junction.target = "unknown"
        }
    }
}

$outDir = Split-Path -Parent $OutputPath
if (-not (Test-Path -LiteralPath $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

$json = $report | ConvertTo-Json -Depth 8
Set-Content -LiteralPath $OutputPath -Value $json -Encoding UTF8

Write-Host "CBMS audit written to: $OutputPath" -ForegroundColor Green
Write-Host "  operational memory files : $($report.sources.operational_memory.file_count)"
Write-Host "  operational chunk JSON   : $($report.summary.operational_chunk_files)"
Write-Host "  manifest total_chunks    : $($report.summary.manifest_total_chunks)"
Write-Host "  catalog chunks           : $($report.summary.catalog_chunk_files)"
Write-Host "  chunks_unified           : $($report.summary.chunks_unified_files)"

exit 0
