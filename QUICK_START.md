# ⚡ QUICK START GUIDE

## 🎯 Get Running in 5 Minutes

---

## Step 1: Install Dependencies (2 minutes)

```bash
cd jira-automation
npm install
```

**What this does:** Downloads Electron, TypeScript, and all required libraries

---

## Step 2: Build the Application (1 minute)

```bash
npm run build
```

**What this does:** Compiles TypeScript (.ts files) to JavaScript (.js files)

**Output:** `dist/` folder with compiled code

---

## Step 3: Run the Application (immediate)

```bash
npm run dev
```

**What happens:**
1. Electron window opens
2. Shows "Jira Automation Assistant"
3. Displays test UI
4. Ready to test!

---

## Step 4: Test It Works (1 minute)

**In the app window:**

1. Click **"Test IPC Communication"** button
2. Wait 2 seconds
3. Should see: **"✓ IPC working!"**

**✅ If you see this, everything is set up correctly!**

---

## Step 5: Configure Your Jira (optional)

Edit the config (created automatically on first run):

**Location:**
- Windows: `C:\Users\YourName\AppData\Roaming\jira-automation-assistant\config.json`
- Mac: `~/Library/Application Support/jira-automation-assistant/config.json`

**Edit:**
```json
{
  "jiraBaseUrl": "https://yourcompany.atlassian.net",
  ...
}
```

---

## 📖 Next: Read the Documentation

### **For Users:**
- `README.md` - How to use the app

### **For Developers:**
- `DEVELOPER_WALKTHROUGH.md` ⭐ **START HERE**
- `ARCHITECTURE.md` - System design
- `BUILD_COMPLETE.md` - What's been built

---

## 🔧 Development Workflow

### **Option 1: Auto-rebuild on changes**

**Terminal 1:**
```bash
npm run watch:ts
```
*(Watches for file changes, recompiles automatically)*

**Terminal 2:**
```bash
npm run start:electron
```
*(Runs the app)*

### **Option 2: Manual rebuild**

```bash
npm run build    # Rebuild after changes
npm run dev      # Run
```

---

## 📦 Build Distributable .exe

```bash
npm run package
```

**Output:** `release/JiraAutomationAssistant.exe`

**Size:** ~120MB (includes Chromium)

**Requirements:** None! Runs standalone.

---

## 🐛 Troubleshooting

### **"window.electron is undefined"**

**Fix:**
```bash
npm run build
```
*(Preload script needs to be compiled)*

---

### **"Cannot find module"**

**Fix:**
```bash
npm install
```
*(Dependencies not installed)*

---

### **Blank window**

**Check:**
1. Open DevTools (F12)
2. Look for errors in console
3. Check if `dist/` folder exists
4. Run `npm run build` again

---

### **App won't start**

**Try:**
```bash
npm run clean    # Remove old build
npm install      # Reinstall dependencies
npm run build    # Rebuild
npm run dev      # Run
```

---

## ✅ Success Checklist

- [ ] Ran `npm install` successfully
- [ ] Ran `npm run build` successfully
- [ ] App window opens
- [ ] Test button shows "✓ IPC working!"
- [ ] No errors in console (F12)

**All checked?** You're ready to go! 🎉

---

## 📚 Learn More

1. **Start with:** `DEVELOPER_WALKTHROUGH.md`
2. **Then read:** `ARCHITECTURE.md`
3. **Finally:** Explore the code files (all heavily commented)

---

## 💡 Quick Tips

### **See Console Logs:**
- **Main Process:** Terminal where you ran `npm run dev`
- **Renderer:** Press F12 in app window

### **Debug TypeScript:**
- Set breakpoints in .ts files
- Use VSCode debugger
- Or add `console.log()` statements

### **Hot Reload:**
- Use `npm run watch:ts` + `npm run start:electron`
- Changes rebuild automatically
- Restart app to see changes

---

## 🚀 You're All Set!

The app is running and ready for customization.

**Next Steps:**
- Customize for your Jira instance
- Add your JQL queries
- Test automation on real issues
- Deploy to your team

---

**Need Help?** Every file has detailed comments explaining what it does!
