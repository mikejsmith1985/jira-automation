# Automated Version Sync System

## Problem Solved

**Before**: Code version and GitHub release version could get out of sync
- Developer updates `APP_VERSION = "1.2.41"` in app.py
- Forgets to create GitHub release v1.2.41
- Users see confusing version mismatches

**After**: Version automatically syncs from git tag
- Git tag is the source of truth
- app.py version updates automatically during build
- Impossible to have version mismatch

---

## How It Works

### 3-Layer Version Sync

1. **Local builds** (`build.ps1`)
   - Runs `sync_version.py` before building
   - Reads latest git tag (e.g., v1.2.41)
   - Updates `APP_VERSION` in app.py to match
   - Builds exe with correct version

2. **GitHub Actions** (`.github/workflows/manual-release.yml`)
   - When you push tag v1.2.41
   - Workflow extracts version from tag
   - Updates app.py automatically
   - Builds and releases with correct version

3. **Pre-release helper** (`pre_release_sync.ps1`)
   - Optional: Run manually before release
   - Updates app.py to target version
   - Ensures git commit has correct version

---

## Your Workflow (UNCHANGED)

Your Release Manager command **still works exactly the same**:

```powershell
cd "C:\projectswin\jira-automation"

# Step 1: Optionally pre-sync version (RECOMMENDED)
.\pre_release_sync.ps1 -Version "1.2.41"

# Step 2: Your existing Release Manager command (UNCHANGED)
$ver_success = $true
if (Test-Path package.json) { 
    npm version v1.2.41 --no-git-tag-version --allow-same-version
    $ver_success = $? 
}
if ($ver_success) { 
    $b = git branch --show-current
    git add -A
    git commit -m "Release v1.2.41" --allow-empty
    git push origin $b
    git checkout main
    git pull origin main
    git merge $b --no-edit
    git push origin main
    git push origin :refs/tags/v1.2.41 2>$null
    git tag -d v1.2.41 2>$null
    git tag v1.2.41
    git push origin v1.2.41  # <-- This triggers GitHub Actions
    git checkout $b
}
```

### What Changed?

**Nothing breaks**, but now you can optionally run `pre_release_sync.ps1` first:

```powershell
# OPTION A: Manual pre-sync (recommended)
.\pre_release_sync.ps1 -Version "1.2.41"
# Then run your Release Manager command

# OPTION B: Let build.ps1 sync automatically
# Just run build.ps1, it will sync from git tag

# OPTION C: Let GitHub Actions handle it
# Just push the tag, Actions will sync version
```

---

## How to Release v1.2.41 (Updated Process)

### Recommended Workflow

```powershell
# Step 1: Pre-sync version (ensures consistency)
.\pre_release_sync.ps1 -Version "1.2.41"

# Step 2: Review the change
git diff app.py
# Should show: APP_VERSION = "1.2.41"

# Step 3: Run your Release Manager command
# (Your existing command - no changes needed)
cd "C:\projectswin\jira-automation"
$ver_success = $true
if (Test-Path package.json) { 
    npm version v1.2.41 --no-git-tag-version --allow-same-version
    $ver_success = $? 
}
if ($ver_success) { 
    $b = git branch --show-current
    git add -A
    git commit -m "Release v1.2.41" --allow-empty
    git push origin $b
    git checkout main
    git pull origin main
    git merge $b --no-edit
    git push origin main
    git push origin :refs/tags/v1.2.41 2>$null
    git tag -d v1.2.41 2>$null
    git tag v1.2.41
    git push origin v1.2.41
    git checkout $b
    Write-Host "🚀 Release v1.2.41 triggered!" -ForegroundColor Green
}
```

### What Happens?

1. `pre_release_sync.ps1` updates app.py to v1.2.41
2. Your Release Manager command commits and pushes the change
3. Tag v1.2.41 is created and pushed
4. GitHub Actions triggers:
   - Verifies app.py version matches tag
   - Builds waypoint.exe
   - Creates GitHub release v1.2.41
   - Uploads waypoint-v1.2.41.exe

---

## Files Created

### 1. `sync_version.py`
Python script that:
- Reads latest git tag
- Extracts version (removes 'v' prefix)
- Updates APP_VERSION in app.py
- Verifies the change

**Used by**: `build.ps1` (automatic)

### 2. `pre_release_sync.ps1`
PowerShell script that:
- Takes version as parameter
- Updates app.py
- Updates package.json (if exists)
- Shows what changed

**Used by**: You, manually before release (optional but recommended)

### 3. `.github/workflows/manual-release.yml` (UPDATED)
GitHub Actions workflow that:
- Triggers on tag push
- Syncs app.py version from tag
- Builds executable
- Creates release

**Triggered by**: Your Release Manager command (when you push the tag)

### 4. `build.ps1` (UPDATED)
Build script that:
- Runs `sync_version.py` first
- Syncs version from git tag
- Builds executable
- Creates zip with correct version name

**Used by**: Local builds and GitHub Actions

---

## Benefits

### 1. Version Mismatch Prevention
- ✅ Git tag is source of truth
- ✅ app.py syncs automatically
- ✅ Build always uses correct version
- ✅ Release always matches code

### 2. Zero Breaking Changes
- ✅ Your Release Manager command unchanged
- ✅ Can still manually update versions
- ✅ Scripts are optional helpers
- ✅ Backward compatible

### 3. Multiple Sync Points
- ✅ Pre-release script (manual)
- ✅ Build script (automatic)
- ✅ GitHub Actions (automatic)
- ✅ Can't accidentally release wrong version

---

## Testing the System

### Test 1: Local Build
```powershell
# Create a test tag
git tag v1.2.99-test
git push origin v1.2.99-test

# Build locally
.\build.ps1

# Check version in exe
.\dist\waypoint.exe --version  # Should show 1.2.99-test
```

### Test 2: Pre-Release Sync
```powershell
# Sync to a specific version
.\pre_release_sync.ps1 -Version "1.2.42"

# Check app.py
Select-String -Path app.py -Pattern "APP_VERSION"
# Should show: APP_VERSION = "1.2.42"
```

### Test 3: GitHub Actions
```powershell
# Push a release tag
git tag v1.2.43
git push origin v1.2.43

# Check GitHub Actions:
# https://github.com/mikejsmith1985/jira-automation/actions

# Should:
# 1. Sync version
# 2. Build exe
# 3. Create release v1.2.43
```

---

## Troubleshooting

### "Version sync failed"
```powershell
# Manually check current version
Select-String -Path app.py -Pattern "APP_VERSION"

# Manually sync
python sync_version.py

# Or force version
.\pre_release_sync.ps1 -Version "1.2.41"
```

### "No git tags found"
```powershell
# Check tags
git tag -l

# Create initial tag if needed
git tag v1.0.0
git push origin v1.0.0
```

### "Build uses wrong version"
```powershell
# build.ps1 syncs from git tags, so:
# 1. Make sure you have a git tag
git tag v1.2.41

# 2. Build again
.\build.ps1

# The build will use v1.2.41
```

---

## Summary

**What you asked for**: Automate version control based on git tags without breaking your workflow

**What I delivered**:
1. ✅ `sync_version.py` - Auto-syncs from git tags
2. ✅ `pre_release_sync.ps1` - Pre-release helper
3. ✅ Updated `build.ps1` - Syncs before building
4. ✅ Updated GitHub Actions - Syncs during release
5. ✅ Fully backward compatible with your Release Manager workflow

**Your workflow**: UNCHANGED - just push tags as you always do

**Bonus**: Optional `pre_release_sync.ps1` for extra safety before release
