# Jira Hygiene Assistant - Build Script
# Creates a standalone .exe using PyInstaller

Write-Host "Building GitHub-Jira Sync Tool..." -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Checking Python..." -ForegroundColor Yellow
$version = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python not found. Please install Python 3.10+" -ForegroundColor Red
    exit 1
}
Write-Host "Python version: $version" -ForegroundColor Green

# Install dependencies
Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet
if ($LASTEXITCODE -ne 0) {
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
$params = @(
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
    "--hidden-import=urllib3",
    "--hidden-import=extensions",
    "--hidden-import=extensions.jira",
    "--hidden-import=extensions.github",
    "--hidden-import=extensions.reporting",
    "--hidden-import=storage",
    "--hidden-import=trio",
    "--hidden-import=trio_websocket",
    "--hidden-import=nacl",
    "--hidden-import=jwt",
    "--hidden-import=cryptography",
    "--hidden-import=certifi",
    "--hidden-import=charset_normalizer",
    "--hidden-import=idna",
    "--hidden-import=deprecated",
    "--hidden-import=wrapt"
)

# Optional extensions hidden import - may fail if extensions folder structure is invalid
if (Test-Path "extensions\__init__.py") {
    $params += "--hidden-import=extensions"
}

if (Test-Path "assets\icon.ico") {
    $params += "--icon=assets\icon.ico"
}

$params += "app.py"

Write-Host "Running: python $params"
& python $params

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed" -ForegroundColor Red
    exit 1
}

$exePath = "dist\waypoint.exe"
if (Test-Path $exePath) {
    $size = [math]::Round((Get-Item $exePath).Length / 1MB, 1)
    Write-Host "Build successful! ($size MB)" -ForegroundColor Green
    Write-Host ""
    Write-Host "Executable location:" -ForegroundColor Cyan
    Write-Host "   $exePath" -ForegroundColor White
    Write-Host ""
    Write-Host "To run:" -ForegroundColor Cyan
    Write-Host "   .\dist\waypoint.exe" -ForegroundColor White
    Write-Host ""
    Write-Host "Creating release package..." -ForegroundColor Yellow
    
    # Create release folder
    $releaseDir = "release"
    if (Test-Path $releaseDir) { Remove-Item -Recurse -Force $releaseDir }
    New-Item -ItemType Directory -Path $releaseDir | Out-Null
    
    # Copy files
    Copy-Item $exePath -Destination $releaseDir
    Copy-Item "READY_TO_TEST.md" -Destination $releaseDir -ErrorAction SilentlyContinue
    Copy-Item "config.yaml" -Destination $releaseDir
    Copy-Item "requirements.txt" -Destination $releaseDir
    
    # Create zip
    $zipName = "waypoint-v1.2.27.zip"

    if (Test-Path $zipName) { Remove-Item -Force $zipName }
    
    # Compress release folder contents
    Compress-Archive -Path "$releaseDir\*" -DestinationPath $zipName
    
    $zipSize = [math]::Round((Get-Item $zipName).Length / 1MB, 1)
    Write-Host "Release package created: $zipName ($zipSize MB)" -ForegroundColor Green
    
} else {
    Write-Host "Executable not found" -ForegroundColor Red
    exit 1
}
