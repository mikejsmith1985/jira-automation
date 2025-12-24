# Jira Hygiene Assistant - Build Script
# Creates a standalone .exe using PyInstaller

Write-Host "🔨 Building Jira Hygiene Assistant..." -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "📋 Checking Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Python not found. Please install Python 3.10+" -ForegroundColor Red
    exit 1
}
Write-Host "✓ $pythonVersion" -ForegroundColor Green

# Install dependencies
Write-Host ""
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Dependencies installed" -ForegroundColor Green

# Install Playwright browsers
Write-Host ""
Write-Host "🌐 Installing Playwright browsers..." -ForegroundColor Yellow
playwright install chromium
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to install Playwright browsers" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Playwright browsers installed" -ForegroundColor Green

# Build with PyInstaller
Write-Host ""
Write-Host "🏗️ Building executable..." -ForegroundColor Yellow

pyinstaller --clean `
    --name "JiraHygieneAssistant" `
    --onefile `
    --noconsole `
    --icon=NONE `
    app.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Build failed" -ForegroundColor Red
    exit 1
}

$exePath = "dist\JiraHygieneAssistant.exe"
if (Test-Path $exePath) {
    $size = [math]::Round((Get-Item $exePath).Length / 1MB, 1)
    Write-Host "✓ Build successful! ($size MB)" -ForegroundColor Green
    Write-Host ""
    Write-Host "📦 Executable location:" -ForegroundColor Cyan
    Write-Host "   $exePath" -ForegroundColor White
    Write-Host ""
    Write-Host "🚀 To run:" -ForegroundColor Cyan
    Write-Host "   .\dist\JiraHygieneAssistant.exe" -ForegroundColor White
} else {
    Write-Host "✗ Executable not found" -ForegroundColor Red
    exit 1
}
