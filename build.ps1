# Jira Hygiene Assistant - Build Script
# Creates a standalone .exe using PyInstaller

Write-Host "Building GitHub-Jira Sync Tool..." -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Checking Python..." -ForegroundColor Yellow
 = python --version 2>&1
if (0 -ne 0) {
    Write-Host "Python not found. Please install Python 3.10+" -ForegroundColor Red
    exit 1
}
Write-Host "Python version: " -ForegroundColor Green

# Install dependencies
Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet
if (0 -ne 0) {
    Write-Host "Failed to install dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "Dependencies installed" -ForegroundColor Green

# Build with PyInstaller
Write-Host ""
Write-Host "Building executable..." -ForegroundColor Yellow

# Clean previous builds
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "*.spec") { Remove-Item -Force "*.spec" }

# Build parameters
 = @(
    "-m", "PyInstaller",
    "--clean",
    "--name", "waypoint",
    "--onefile",
    "--noconsole",
    "--add-data", "config.yaml;.",
    "--add-data", "modern-ui.html;.",
    "--add-data", "assets;assets",
    "--hidden-import=selenium",
    "--hidden-import=yaml",
    "--hidden-import=schedule",
    "--hidden-import=github",
    "--hidden-import=packaging",
    "--hidden-import=requests",
    "--hidden-import=urllib3"
)

# Optional extensions hidden import - may fail if extensions folder structure is invalid
if (Test-Path "extensions\__init__.py") {
     += "--hidden-import=extensions"
}

if (Test-Path "assets\icon.ico") {
     += "--icon=assets\icon.ico"
}

 += "app.py"

Write-Host "Running: python "
& python 

if (0 -ne 0) {
    Write-Host "Build failed" -ForegroundColor Red
    exit 1
}

 = "dist\waypoint.exe"
if (Test-Path ) {
     = [math]::Round((Get-Item ).Length / 1MB, 1)
    Write-Host "Build successful! ( MB)" -ForegroundColor Green
    Write-Host ""
    Write-Host "Executable location:" -ForegroundColor Cyan
    Write-Host "   " -ForegroundColor White
    Write-Host ""
    Write-Host "To run:" -ForegroundColor Cyan
    Write-Host "   .\dist\waypoint.exe" -ForegroundColor White
    Write-Host ""
    Write-Host "Creating release package..." -ForegroundColor Yellow
    
    # Create release folder
     = "release"
    if (Test-Path ) { Remove-Item -Recurse -Force  }
    New-Item -ItemType Directory -Path  | Out-Null
    
    # Copy files
    Copy-Item  -Destination 
    Copy-Item "READY_TO_TEST.md" -Destination  -ErrorAction SilentlyContinue
    Copy-Item "config.yaml" -Destination 
    Copy-Item "requirements.txt" -Destination 
    
    # Create zip
     = "waypoint-v1.2.24.zip"
    if (Test-Path ) { Remove-Item -Force  }
    Compress-Archive -Path "\*" -DestinationPath 
    
     = [math]::Round((Get-Item ).Length / 1MB, 1)
    Write-Host "Release package created:  ( MB)" -ForegroundColor Green
    
} else {
    Write-Host "Executable not found" -ForegroundColor Red
    exit 1
}
