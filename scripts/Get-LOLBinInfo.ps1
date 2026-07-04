<#
.SYNOPSIS
    LOLBin Reference Tool - PowerShell CLI Lookup

.DESCRIPTION
    Standalone PowerShell script for terminal-based LOLBin lookup during
    authorized engagements. Uses the same JSON database as the Chrome extension.

.PARAMETER Name
    Search term to match against binary name, description, or ID.

.PARAMETER Os
    Filter by operating system: windows, linux, macos

.PARAMETER Category
    Filter by technique category.

.PARAMETER ListAll
    List all entries in the database.

.EXAMPLE
    ./Get-LOLBinInfo.ps1 -Name certutil

.EXAMPLE
    ./Get-LOLBinInfo.ps1 -Os windows -Category "Execution"
#>

param(
    [string]$Name,
    [ValidateSet("windows", "linux", "macos")]
    [string]$Os,
    [string]$Category,
    [switch]$ListAll
)

$dbPath = Join-Path $PSScriptRoot "..\extension\data\lolbin_db.json"

if (-not (Test-Path $dbPath)) {
    Write-Host "Database not found at $dbPath" -ForegroundColor Red
    exit 1
}

$db = Get-Content $dbPath -Raw | ConvertFrom-Json

$results = $db

if ($Os) {
    $results = $results | Where-Object { $_.os -eq $Os }
}

if ($Category) {
    $results = $results | Where-Object { $_.category -like "*$Category*" }
}

if ($Name -and -not $ListAll) {
    $results = $results | Where-Object {
        $_.name -like "*$Name*" -or
        $_.description -like "*$Name*" -or
        $_.id -like "*$Name*"
    }
}

if (-not $results -or $results.Count -eq 0) {
    Write-Host "No matching entries found." -ForegroundColor Red
    exit 0
}

foreach ($entry in $results) {
    Write-Host "`n=== $($entry.name) ($($entry.os)) ===" -ForegroundColor Cyan
    Write-Host "Category:    $($entry.category)" -ForegroundColor Gray
    Write-Host "Description: $($entry.description)"
    Write-Host "Example:     $($entry.example_command)" -ForegroundColor Yellow

    foreach ($alt in $entry.alt_commands) {
        Write-Host "Alt:         $alt" -ForegroundColor Yellow
    }

    if ($entry.detection_notes) {
        Write-Host "Detection:   $($entry.detection_notes)" -ForegroundColor Green
    }

    foreach ($ref in $entry.references) {
        Write-Host "Ref: $ref" -ForegroundColor DarkGray
    }
}

Write-Host "`n$($results.Count) result(s) found." -ForegroundColor Gray
