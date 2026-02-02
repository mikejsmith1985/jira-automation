# Pre-Release Version Sync Script
# Run this before using the Release Manager command

param(
    [Parameter(Mandatory=$true)]
    [string]$Version
)

Write-Host "Pre-Release Version Sync" -ForegroundColor Cyan
Write-Host "Target version: $Version" -ForegroundColor Yellow
Write-Host ""

# Remove 'v' prefix if present
$cleanVersion = $Version -replace '^v', ''

# Update app.py
Write-Host "Updating app.py..." -ForegroundColor Yellow
$appContent = Get-Content "app.py" -Raw -Encoding UTF8
# Match: APP_VERSION = "x.y.z" or APP_VERSION = 'x.y.z'
$appContent = $appContent -replace 'APP_VERSION\s*=\s*["''][^"'']+["'']', "APP_VERSION = `"$cleanVersion`""
$appContent | Set-Content "app.py" -Encoding UTF8 -NoNewline
Write-Host "  APP_VERSION = `"$cleanVersion`"" -ForegroundColor Green

# Update package.json if it exists
if (Test-Path "package.json") {
    Write-Host "Updating package.json..." -ForegroundColor Yellow
    $packageJson = Get-Content "package.json" -Raw | ConvertFrom-Json
    $packageJson.version = $cleanVersion
    $packageJson | ConvertTo-Json -Depth 100 | Set-Content "package.json" -Encoding UTF8
    Write-Host "  version: `"$cleanVersion`"" -ForegroundColor Green
}

Write-Host ""
Write-Host "Version sync complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Review changes: git diff app.py" -ForegroundColor White
Write-Host "  2. Run your Release Manager command" -ForegroundColor White
Write-Host ""
