# Script to build the Jira Hygiene Assistant extension and create distribution zip
Write-Host "Building Jira Hygiene Assistant Extension v0.0.1..." -ForegroundColor Cyan

$extDir = "jira-hygiene-extension"
$zipFile = "jira-hygiene-extension.zip"

# Check if extension files exist
if (-not (Test-Path "$extDir\popup.html")) {
    Write-Host "Error: Extension source files not found in $extDir" -ForegroundColor Red
    Write-Host "Required files: popup.html, popup.js, content.js, manifest.json, icon.png, README.md" -ForegroundColor Yellow
    exit 1
}

# Remove old zip if exists
if (Test-Path $zipFile) {
    Remove-Item $zipFile -Force
    Write-Host "✓ Removed old zip file" -ForegroundColor Green
}

# Create zip file
Write-Host "Creating zip package..." -ForegroundColor Cyan
Compress-Archive -Path "$extDir\*" -DestinationPath $zipFile -Force

Write-Host "✓ Created $zipFile" -ForegroundColor Green
Write-Host ""
Write-Host "Extension package ready for distribution!" -ForegroundColor Green
Write-Host "Users can:" -ForegroundColor Cyan
Write-Host "  1. Download $zipFile" -ForegroundColor White
Write-Host "  2. Extract it" -ForegroundColor White
Write-Host "  3. Load unpacked extension in Chrome/Edge" -ForegroundColor White
