#Requires -Version 5.1
<#
.SYNOPSIS
    DPAPI protect/unprotect fallback for AIONS vault (CurrentUser, offline).
.PARAMETER Action
    protect | unprotect
.PARAMETER PayloadB64
    Base64-encoded input bytes
.PARAMETER EntropyB64
    Optional base64 entropy (AIONS_LOCAL_VAULT_V1)
#>
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet('protect', 'unprotect')]
    [string]$Action,

    [Parameter(Mandatory = $true, Position = 1)]
    [string]$PayloadB64,

    [Parameter(Mandatory = $false, Position = 2)]
    [string]$EntropyB64
)

$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.Security

function Get-EntropyBytes {
    param([string]$B64)
    if ([string]::IsNullOrWhiteSpace($B64)) { return $null }
    return [Convert]::FromBase64String($B64)
}

$payload = [Convert]::FromBase64String($PayloadB64)
$entropy = Get-EntropyBytes -B64 $EntropyB64
$scope = [System.Security.Cryptography.DataProtectionScope]::CurrentUser

if ($Action -eq 'protect') {
    $out = [System.Security.Cryptography.ProtectedData]::Protect($payload, $entropy, $scope)
} else {
    $out = [System.Security.Cryptography.ProtectedData]::Unprotect($payload, $entropy, $scope)
}

[Convert]::ToBase64String($out)
