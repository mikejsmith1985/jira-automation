# GitHub Actions Workflows

This directory contains automated workflows for building and releasing the application.

## Available Workflows

### 1. Build and Release (Automated Version Bump)

**File:** `build-and-release.yml`

**Trigger:** Manual (workflow_dispatch)

**What it does:**
1. Automatically calculates the next version based on the latest tag
2. Builds the Windows executable with PyInstaller
3. Creates a new Git tag
4. Creates a GitHub Release with the executable
5. Uploads build artifacts

**How to use:**
```bash
# Via GitHub CLI
gh workflow run build-and-release.yml

# Or via GitHub UI:
# 1. Go to Actions tab
# 2. Select "Build and Release"
# 3. Click "Run workflow"
# 4. Choose version bump type (major/minor/patch)
# 5. Optionally mark as pre-release
```

**Version Bump Types:**
- `major`: 1.0.0 → 2.0.0 (breaking changes)
- `minor`: 1.0.0 → 1.1.0 (new features)
- `patch`: 1.0.0 → 1.0.1 (bug fixes)

---

### 2. Manual Release (Specify Version)

**File:** `manual-release.yml`

**Trigger:** Manual (workflow_dispatch)

**What it does:**
1. Accepts a specific tag name (e.g., v1.2.0)
2. Validates tag format and checks if it exists
3. Builds the Windows executable
4. Creates the Git tag
5. Creates a GitHub Release
6. Uploads build artifacts

**How to use:**
```bash
# Via GitHub CLI
gh workflow run manual-release.yml -f tag_name=v1.2.0

# Or via GitHub UI:
# 1. Go to Actions tab
# 2. Select "Manual Release"
# 3. Click "Run workflow"
# 4. Enter tag name (e.g., v1.2.0)
# 5. Optionally add custom release notes
```

---

## Quick Start

### First Time Setup

1. **Ensure you have a spec file:**
   - The workflow looks for `GitHubJiraSync.spec` or `JiraAutomationAssistant.spec`
   - If not found, it creates one automatically

2. **Run your first release:**
   ```bash
   # For automatic version bump (recommended)
   gh workflow run build-and-release.yml
   
   # Or specify version manually
   gh workflow run manual-release.yml -f tag_name=v1.2.0
   ```

### Creating a New Release

**For the feedback system (v1.2.0):**

```bash
# Option 1: Let GitHub Actions calculate version
gh workflow run build-and-release.yml -f version_type=minor

# Option 2: Specify exact version
gh workflow run manual-release.yml -f tag_name=v1.2.0 -f release_notes="Feedback system with screenshot and video capture"
```

---

## Workflow Outputs

### What gets created:

1. **Git Tag**
   - Format: `v1.2.0`
   - Automatically pushed to repository

2. **GitHub Release**
   - Includes the executable (`.exe`)
   - Includes release notes
   - Includes documentation files
   - Marked as pre-release if specified

3. **Build Artifacts**
   - Uploaded to GitHub Actions
   - Available for 90 days
   - Can be downloaded separately

---

## Troubleshooting

### Workflow fails with "Tag already exists"
**Solution:** Delete the tag or use a different version:
```bash
git tag -d v1.2.0
git push origin :refs/tags/v1.2.0
```

### Executable not building
**Solution:** Check if PyInstaller spec file exists:
```bash
ls *.spec
```

### Release notes empty
**Solution:** Provide custom notes or ensure `IMPLEMENTATION_COMPLETE.md` exists

---

## Advanced Usage

### Running workflow with all options:

```bash
gh workflow run build-and-release.yml \
  -f version_type=minor \
  -f pre_release=true
```

### Checking workflow status:

```bash
# List recent workflow runs
gh run list

# Watch a specific run
gh run watch

# View logs
gh run view
```

### Downloading release artifacts:

```bash
# Download latest release
gh release download

# Download specific version
gh release download v1.2.0
```

---

## Best Practices

1. **Use semantic versioning:**
   - Major: Breaking changes
   - Minor: New features (backward compatible)
   - Patch: Bug fixes

2. **Tag format:**
   - Always use `v` prefix: `v1.2.0`
   - Follow format: `vMAJOR.MINOR.PATCH`

3. **Release notes:**
   - Use descriptive notes
   - Link to PR or issues
   - List breaking changes

4. **Pre-releases:**
   - Use for beta/alpha versions
   - Test before final release

---

## GitHub CLI Commands

### Install GitHub CLI (if needed):
```powershell
winget install GitHub.cli
```

### Authenticate:
```bash
gh auth login
```

### Common commands:
```bash
# List workflows
gh workflow list

# Run workflow
gh workflow run <workflow-name>

# View workflow runs
gh run list

# Create release manually (alternative)
gh release create v1.2.0 dist/*.exe --title "Release v1.2.0" --notes "Release notes here"
```

---

## Integration with CI/CD

These workflows can be triggered:
- Manually via GitHub UI
- Manually via GitHub CLI
- Programmatically via GitHub API
- From other workflows (workflow_call)

For automatic releases on merge to main, add:
```yaml
on:
  push:
    branches:
      - main
```

---

## Questions?

- See workflow logs in GitHub Actions tab
- Check `.github/workflows/*.yml` for workflow definitions
- Use `gh workflow view <workflow-name>` for details
