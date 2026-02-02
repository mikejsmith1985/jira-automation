# Release Script for Jira Automation
# Usage: .\release.ps1 -Version "1.4.0"

param(
    [Parameter(Mandatory=$true)]
    [string]$Version
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting release process for v$Version..." -ForegroundColor Cyan

# Step 1: Verify clean working directory (except ignored files)
Write-Host "`n📋 Checking git status..." -ForegroundColor Yellow
$status = git status --porcelain
$tracked_changes = $status | Where-Object { $_ -notmatch 'selenium_profile|playwright_profile|__pycache__|\.pyc' }

if ($tracked_changes) {
    Write-Host "❌ Error: You have uncommitted changes:" -ForegroundColor Red
    $tracked_changes | ForEach-Object { Write-Host "  $_" }
    Write-Host "`nPlease commit or stash changes first." -ForegroundColor Yellow
    exit 1
}

# Step 2: Update package.json version (manually to avoid npm hanging)
if (Test-Path package.json) {
    Write-Host "`n📦 Updating package.json to v$Version..." -ForegroundColor Yellow
    $pkg = Get-Content package.json -Raw | ConvertFrom-Json
    $pkg.version = $Version
    $pkg | ConvertTo-Json -Depth 100 | Set-Content package.json
    Write-Host "✅ Updated package.json" -ForegroundColor Green
}

# Step 3: Update app.py version
Write-Host "`n🐍 Updating app.py version..." -ForegroundColor Yellow
$app_content = Get-Content app.py -Raw
$app_content = $app_content -replace "APP_VERSION = `"[\d\.]+`"", "APP_VERSION = `"$Version`""
Set-Content app.py -Value $app_content -NoNewline
Write-Host "✅ Updated app.py to v$Version" -ForegroundColor Green

# Step 4: Get current branch
$current_branch = git branch --show-current
Write-Host "`n🌿 Current branch: $current_branch" -ForegroundColor Cyan

# Step 5: Stage and commit version bump
Write-Host "`n📝 Staging version changes..." -ForegroundColor Yellow
git add package.json app.py 2>&1 | Out-Null
git commit -m "Release v$Version" --allow-empty

if (-not $?) {
    Write-Host "❌ Commit failed" -ForegroundColor Red
    exit 1
}

# Step 6: Push to current branch
Write-Host "`n⬆️  Pushing to origin/$current_branch..." -ForegroundColor Yellow
git push origin $current_branch

if (-not $?) {
    Write-Host "❌ Push failed" -ForegroundColor Red
    exit 1
}

# Step 7: Merge to main (if not already on main)
if ($current_branch -ne "main") {
    Write-Host "`n🔀 Switching to main branch..." -ForegroundColor Yellow
    git checkout main
    
    Write-Host "📥 Pulling latest main..." -ForegroundColor Yellow
    git pull origin main
    
    Write-Host "🔀 Merging $current_branch into main..." -ForegroundColor Yellow
    git merge $current_branch --no-edit
    
    if (-not $?) {
        Write-Host "❌ Merge failed" -ForegroundColor Red
        git checkout $current_branch
        exit 1
    }
    
    Write-Host "⬆️  Pushing to origin/main..." -ForegroundColor Yellow
    git push origin main
    
    if (-not $?) {
        Write-Host "❌ Push to main failed" -ForegroundColor Red
        git checkout $current_branch
        exit 1
    }
}

# Step 8: Create and push tag
Write-Host "`n🏷️  Creating tag v$Version..." -ForegroundColor Yellow

# Delete existing tag if present (locally and remotely)
git push origin ":refs/tags/v$Version" 2>$null | Out-Null
git tag -d "v$Version" 2>$null | Out-Null

# Create new tag
git tag "v$Version"

if (-not $?) {
    Write-Host "❌ Tag creation failed" -ForegroundColor Red
    if ($current_branch -ne "main") { git checkout $current_branch }
    exit 1
}

Write-Host "⬆️  Pushing tag v$Version..." -ForegroundColor Yellow
git push origin "v$Version"

if (-not $?) {
    Write-Host "❌ Tag push failed" -ForegroundColor Red
    if ($current_branch -ne "main") { git checkout $current_branch }
    exit 1
}

# Step 9: Return to original branch (if not main)
if ($current_branch -ne "main") {
    Write-Host "`n🔙 Returning to $current_branch..." -ForegroundColor Yellow
    git checkout $current_branch
}

# Step 10: Success!
Write-Host "`n✅ Release v$Version complete!" -ForegroundColor Green
Write-Host "🎉 GitHub Actions will now build the release." -ForegroundColor Cyan
Write-Host "`nRelease URL: https://github.com/mikejsmith1985/jira-automation/releases/tag/v$Version" -ForegroundColor Cyan
