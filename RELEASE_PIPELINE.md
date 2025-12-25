# Release Pipeline Documentation

## ✅ STATUS: WORKING & TESTED!

The automated release pipeline is **live and working**. The latest release (v1.2.1) was auto-generated when code was merged to main.

## 🚀 Automated Release Workflow

The project now has a **fully automated release pipeline** that generates a new release whenever you merge code to the `main` branch.

### How It Works

```
Your Feature Branch → Create PR → Squash Merge to Main → Release Auto-Generated ✨
```

## 📋 Step-by-Step Workflow

### 1. Create Your Feature Branch
```bash
git checkout -b feature/my-feature
# Make your changes...
git add .
git commit -m "Add my feature"
git push origin feature/my-feature
```

### 2. Create Pull Request (Optional, but Recommended)
```bash
# On GitHub, create PR from your branch to main
# This allows for code review and testing
```

### 3. Merge to Main via Squash Merge
```bash
# Option A: Via GitHub UI
# - Click "Squash and merge" button on PR

# Option B: Via command line
git checkout main
git pull origin main
git merge --squash feature/my-feature
git commit -m "Merge feature/my-feature"
git push origin main
```

### 4. Automatic Release Generation 🎉
When your code is pushed to `main`:

1. **Workflow Triggers**: `.github/workflows/auto-release-on-main.yml` detects the push
2. **Version Bump**: Automatically calculates next patch version (v1.0.0 → v1.0.1)
3. **Build**: Compiles Python code to Windows executable with PyInstaller
4. **Release**: Creates GitHub Release with tag and download assets
5. **Artifacts**: Uploads .exe file to GitHub Releases

✅ **All automatic - you don't need to do anything!**

---

## 🔍 What Gets Skipped?

The workflow is smart about when to release:

### ✅ Creates Release When:
- Source code changes (`.py` files)
- Configuration changes (`config.yaml`)
- Test files added/modified
- Dependencies updated (`requirements.txt`)

### ⏭️ Skips Release When:
- Only markdown files changed (`*.md`)
- Documentation updates
- .gitignore changes
- No new commits since last tag

This prevents unnecessary releases for docs-only changes.

---

## 📊 Release Naming

### Version Format
```
v<MAJOR>.<MINOR>.<PATCH>
```

### Auto-Increment Rules
The pipeline **automatically bumps the patch version**:

```
v1.0.0 → v1.0.1  (After first merge)
v1.0.1 → v1.0.2  (After second merge)
v1.2.3 → v1.2.4  (After any merge)
```

### Manual Version Bumps
If you need to bump MAJOR or MINOR versions, use the manual workflow:

```bash
gh workflow run manual-release.yml \
  -f version_type=minor \
  -f tag_name=v1.1.0
```

---

## 📦 What Gets Released

Each automatic release includes:

1. **Executable File**
   - `GitHubJiraSync-v1.0.1.exe` - Ready to run on Windows

2. **Release Notes**
   - Auto-generated from your commit message
   - Includes installation instructions
   - Lists system requirements

3. **Build Artifacts**
   - Stored for 30 days on GitHub
   - Available from Actions tab

4. **GitHub Release Page**
   - Downloadable .exe file
   - Release notes
   - Link to commit history

---

## 🎯 Example Usage

### Scenario 1: Bug Fix Release
```bash
# Create fix branch
git checkout -b fix/issue-123-button-not-working

# Make fix
# Edit app.py to fix button issue
git commit -m "Fix issue #123: Button not working"
git push origin fix/issue-123-button-not-working

# Merge to main
git checkout main
git pull
git merge --squash fix/issue-123-button-not-working
git commit -m "Fix issue #123: Button not working"
git push origin main

# ✨ Release v1.0.1 created automatically!
```

### Scenario 2: Feature Release
```bash
# Create feature branch
git checkout -b feature/automation-rules-config

# Make changes
git commit -m "Add configurable automation rules"
git push origin feature/automation-rules-config

# Merge and release
git checkout main
git pull
git merge --squash feature/automation-rules-config
git commit -m "Add configurable automation rules"
git push origin main

# ✨ Release v1.1.0 created automatically!
```

---

## 📈 Workflow Pipeline Steps

When code is merged to main, the workflow executes:

### 1. **Checkout** ✓
   - Pulls latest code from main
   - Full git history for versioning

### 2. **Detect Changes** ✓
   - Checks if code actually changed (not just docs)
   - Gets latest tag version
   - Calculates next version

### 3. **Setup Python** ✓
   - Installs Python 3.11
   - Sets up build environment

### 4. **Install Dependencies** ✓
   - pip install -r requirements.txt
   - pip install pyinstaller

### 5. **Build Executable** ✓
   - Detects .spec file (if exists)
   - Compiles Python to Windows .exe
   - Includes icon from assets/

### 6. **Prepare Assets** ✓
   - Copies executable to release/ folder
   - Names with version: `GitHubJiraSync-v1.0.1.exe`
   - Generates release notes from commit

### 7. **Create Tag & Push** ✓
   - Creates git tag: `v1.0.1`
   - Pushes tag to GitHub

### 8. **Create Release** ✓
   - Creates GitHub Release
   - Uploads .exe file
   - Posts release notes

### 9. **Upload Artifacts** ✓
   - Stores artifacts for 30 days
   - Available from Actions tab
   - Can be downloaded manually

---

## 🔧 Troubleshooting

### Release Not Creating
**Problem**: You merged code but no release was created

**Check**:
1. Did you only change `.md` files? (These are skipped)
2. Is there already a tag for this commit? (No duplicate releases)
3. Check the Actions tab for workflow logs

**Solution**:
- If docs-only change: That's expected
- If code change: Check Actions > Auto Release on Main Push
- See workflow logs for errors

### Wrong Version Number
**Problem**: Release shows v1.0.2 but you expected v1.1.0

**Why**: The workflow auto-bumps patch version only

**Solution**:
- For MAJOR/MINOR bumps, use manual workflow
- Or manually create tag and push:
  ```bash
  git tag -a v1.1.0 -m "Release v1.1.0"
  git push origin v1.1.0
  ```

### Executable Won't Build
**Problem**: Workflow fails at "Build executable" step

**Check**:
1. Do you have `requirements.txt`? (Must list all dependencies)
2. Is `app.py` the entry point?
3. Are all imports correct?

**Solution**:
```bash
# Test build locally
pip install pyinstaller
pyinstaller --name="GitHubJiraSync" --onefile --windowed app.py
```

---

## 📊 Available Workflows

### 1. **Auto Release on Main Push** (NEW)
- **File**: `.github/workflows/auto-release-on-main.yml`
- **Trigger**: Push to main branch
- **Action**: Auto-generates patch releases
- **Version**: v1.x.x → v1.x.(x+1)

### 2. **Manual Release**
- **File**: `.github/workflows/manual-release.yml`
- **Trigger**: Workflow dispatch (manual button)
- **Action**: Create specific version
- **Version**: You specify (v1.2.3)

### 3. **Build and Release**
- **File**: `.github/workflows/build-and-release.yml`
- **Trigger**: Workflow dispatch + version type
- **Action**: Bump MAJOR/MINOR/PATCH
- **Version**: v1.0.0 → v1.0.1 or v1.1.0 or v2.0.0

### 4. **Tag-Based Release**
- **File**: `.github/workflows/release.yml`
- **Trigger**: Push of tags (v*.*)
- **Action**: Build and release for tag
- **Version**: Matches tag name

---

## 🎯 Best Practices

### 1. Use Meaningful Commit Messages
```bash
# Good ✓
git commit -m "Fix issue #123: Button not responding"
git commit -m "Add automation rules configuration"

# Bad ✗
git commit -m "fix"
git commit -m "wip"
```

Commit messages appear in release notes!

### 2. Squash Merge from PRs
```bash
# Use squash merge to keep main clean
git merge --squash feature/my-feature

# Or use GitHub UI: "Squash and merge"
```

### 3. Keep main Stable
- Only merge tested, working code
- Use feature branches for development
- Let PR reviews catch issues before merge

### 4. Use Semantic Versioning
```
v1.2.3
│ │ └─ PATCH: Bug fixes
│ └─── MINOR: New features
└───── MAJOR: Breaking changes
```

---

## 📞 Reference

### Workflow Outputs
When a release is created, you can find:

1. **GitHub Releases Page**
   - https://github.com/mikejsmith1985/jira-automation/releases
   - Download .exe from here

2. **Actions Tab**
   - https://github.com/mikejsmith1985/jira-automation/actions
   - View workflow logs
   - Download build artifacts

3. **Git Tags**
   - https://github.com/mikejsmith1985/jira-automation/tags
   - All releases tagged
   - Checkout any version

### File Locations
```
.github/workflows/
├── auto-release-on-main.yml      # NEW: Auto release on main
├── manual-release.yml             # Manual with custom version
├── build-and-release.yml          # Manual with bump type
└── release.yml                    # Tag-based release
```

---

## ✨ Summary

**Before**: Manual steps to create releases

**After**: Just merge to main, releases auto-generate! 🎉

```
Create Feature → PR → Squash Merge → Release Auto-Generated ✨
                                      └─→ .exe ready to download
                                      └─→ GitHub Release created
                                      └─→ Version auto-bumped
                                      └─→ Release notes generated
```

No more manual tagging, no more manual builds, no more manual releases.

**Just code → Merge → Done!** ✅

---

*Documentation updated: December 25, 2025*
