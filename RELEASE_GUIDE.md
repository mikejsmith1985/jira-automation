# 🚀 RELEASE INSTRUCTIONS

## How to Create a New Release

### **Automatic Release Process:**

When you push a version tag to GitHub, GitHub Actions automatically:
1. ✅ Builds the TypeScript
2. ✅ Packages the .exe file
3. ✅ Creates a GitHub Release
4. ✅ Uploads JiraAutomationAssistant.exe

---

## 📋 **Step-by-Step Release Guide**

### **1. Make Your Changes**
```bash
# Edit code, add features, fix bugs
git add .
git commit -m "Add new feature X"
```

### **2. Push to Main**
```bash
git push origin main
```

### **3. Create a Version Tag**

**Semantic Versioning:**
- `v1.0.0` - Major release (breaking changes)
- `v1.1.0` - Minor release (new features, backward compatible)
- `v1.0.1` - Patch release (bug fixes)

```bash
# Create tag
git tag v1.0.0

# Or with message
git tag -a v1.0.0 -m "Release version 1.0.0 - Initial release"
```

### **4. Push the Tag**
```bash
git push origin v1.0.0
```

### **5. Watch GitHub Actions Build**
1. Go to: https://github.com/mikejsmith1985/jira-automation/actions
2. Watch the build process (takes ~5-10 minutes)
3. Green checkmark = Success! ✅
4. Red X = Failed (check logs)

### **6. Download Your Release**
1. Go to: https://github.com/mikejsmith1985/jira-automation/releases
2. See your new release
3. Download `JiraAutomationAssistant.exe`
4. Test it!

---

## 🏷️ **Creating Your First Release**

```bash
cd C:\projectswin\jira-automation

# Create v1.0.0 tag
git tag -a v1.0.0 -m "Initial release - Complete Jira automation with documentation"

# Push tag
git push origin v1.0.0
```

**Then watch:** https://github.com/mikejsmith1985/jira-automation/actions

---

## 📦 **What Gets Built**

### **Build Output:**
- `JiraAutomationAssistant.exe` (~120MB)
- Standalone executable
- No installation required
- Includes Chromium + Node.js

### **Users Can:**
1. Download .exe
2. Run from any folder
3. No admin rights needed
4. Works immediately

---

## 🔧 **Testing Before Release**

### **Test Build Locally:**
```bash
npm install
npm run build
npm run package
```

**Check:** `release/JiraAutomationAssistant.exe` exists

**Test it:**
1. Run the .exe
2. Verify it works
3. Test core features
4. Then create release tag

---

## 📝 **Release Checklist**

Before creating a release:

- [ ] All code committed
- [ ] Tests passing (if you have tests)
- [ ] Version number decided (v1.0.0)
- [ ] CHANGELOG updated (optional)
- [ ] Documentation up to date
- [ ] Tested locally (`npm run package`)
- [ ] .exe runs successfully

Then:
- [ ] Create tag: `git tag v1.0.0`
- [ ] Push tag: `git push origin v1.0.0`
- [ ] Watch GitHub Actions build
- [ ] Download and test release .exe
- [ ] Share with team!

---

## 🐛 **Troubleshooting**

### **Build Failed on GitHub Actions?**

**Check the logs:**
1. Go to Actions tab
2. Click failed workflow
3. Expand failed step
4. Read error message

**Common issues:**
- Missing dependency → Update package.json
- TypeScript error → Fix code, test locally
- Build timeout → Might need to optimize build

**Fix and retry:**
```bash
# Fix the issue
git add .
git commit -m "Fix build issue"
git push origin main

# Create new tag
git tag v1.0.1
git push origin v1.0.1
```

### **Wrong File in Release?**

Delete tag and recreate:
```bash
# Delete local tag
git tag -d v1.0.0

# Delete remote tag
git push origin :refs/tags/v1.0.0

# Delete release on GitHub (manually via web UI)

# Create new tag
git tag v1.0.0
git push origin v1.0.0
```

---

## 📊 **Version History Example**

```
v1.0.0 - Initial release
  - Due date automation
  - Issue reading
  - Field updating
  - Complete documentation

v1.1.0 - PR linking feature
  - Add PR linking module
  - Add comment injection
  - Update documentation

v1.1.1 - Bug fixes
  - Fix date calculation bug
  - Improve error messages
  - Update dependencies
```

---

## 🎯 **Release Frequency**

**Suggested schedule:**
- **Major (1.0.0):** When architecture changes
- **Minor (1.1.0):** When adding new features (every 2-4 weeks)
- **Patch (1.1.1):** For bug fixes (as needed)

---

## 📢 **Announcing Releases**

### **In Release Notes:**
Include:
- What's new
- What's fixed
- Known issues
- Upgrade instructions (if any)

### **Example Release Note:**
```markdown
## 🎉 Version 1.1.0 - PR Linking Feature

### ✨ New Features
- GitHub PR linking and comment injection
- Automatic PR activity sync to Jira
- Configurable PR fields

### 🐛 Bug Fixes
- Fixed date calculation for cross-year ranges
- Improved error handling for missing fields

### 📚 Documentation
- Added PR linking guide
- Updated architecture diagrams

### 🔧 Technical
- Upgraded Electron to 28.0.0
- Added new TypeScript interfaces
```

---

## ✅ **You're All Set!**

**Create your first release:**
```bash
git tag v1.0.0 -m "Initial release"
git push origin v1.0.0
```

**Then visit:** https://github.com/mikejsmith1985/jira-automation/releases

**Your .exe will be ready in ~5-10 minutes!** 🎉
