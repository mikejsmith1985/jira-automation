# 🚀 Jira Automation Assistant

A desktop application that automates Jira tasks through UI simulation - **no API access required**.

---

## ✨ Features

- ✅ **No Jira API needed** - Works through the web interface
- ✅ **Single .exe file** - No installation or admin rights required
- ✅ **Uses your session** - Inherits your SSO and permissions
- ✅ **Fully transparent** - Watch it work in real-time
- ✅ **Extensible** - Easy to add new automation types

---

## 📋 What Can It Do?

### Current Automation Types:

1. **Update Due Dates**
   - Sets due dates based on FixVersion release dates
   - Accounts for business days and holidays
   - Processes issues in bulk

2. **Link Pull Requests**
   - Associates GitHub/GitLab PRs with Jira issues
   - Injects PR comments into Jira

3. **Bulk Field Updates**
   - Update any field across multiple issues
   - Transition issues to new statuses

---

## 🏗️ Architecture

### The App Has 3 Main Parts:

```
┌─────────────────────────────────────────┐
│  RENDERER (React UI)                    │
│  - Forms and buttons                    │
│  - Progress display                     │
│  - Configuration editor                 │
└────────────────┬────────────────────────┘
                 │ IPC Messages
                 ↓
┌─────────────────────────────────────────┐
│  MAIN PROCESS (Electron)                │
│  - Window management                    │
│  - File I/O (config, logs)              │
│  - IPC coordination                     │
└────────────────┬────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────┐
│  AUTOMATION (Injected Scripts)          │
│  - Loads Jira in hidden window          │
│  - Simulates clicks and form fills      │
│  - Reports progress                     │
└─────────────────────────────────────────┘
```

**For detailed architecture explanation, see:** `DEVELOPER_WALKTHROUGH.md`

---

## 🛠️ Development Setup

### Prerequisites:

- Node.js 18+ ([Download here](https://nodejs.org/))
- npm (comes with Node.js)
- Windows, Mac, or Linux

### Installation:

```bash
# 1. Clone or download this project
cd jira-automation

# 2. Install dependencies
npm install

# 3. Build TypeScript
npm run build

# 4. Run the app
npm run dev
```

### Development Workflow:

```bash
# Terminal 1: Watch TypeScript files (auto-compile on save)
npm run watch:ts

# Terminal 2: Run Electron
npm run start:electron
```

---

## 📦 Building for Distribution

Create a standalone `.exe` file:

```bash
npm run package
```

Output: `release/JiraAutomationAssistant.exe`

**Distribution notes:**
- Single file, no installer needed
- No admin rights required
- Can run from USB drive or network share
- Size: ~120MB (includes Chromium engine)

---

## 📂 Project Structure

```
jira-automation/
│
├── src/
│   ├── main/                    # Electron main process
│   │   ├── main.ts              # Entry point
│   │   └── preload.ts           # Security bridge
│   │
│   ├── renderer/                # React UI
│   │   ├── index.html           # Main HTML
│   │   ├── App.tsx              # Root component
│   │   ├── components/          # UI components
│   │   └── styles/              # CSS files
│   │
│   ├── automation/              # Automation scripts
│   │   ├── jira-injector.ts     # Main automation engine
│   │   └── modules/             # Task-specific automation
│   │
│   └── shared/                  # Code used by multiple parts
│       ├── ipc-channels.ts      # IPC channel definitions
│       └── interfaces/          # TypeScript interfaces
│
├── package.json                 # Dependencies & scripts
├── tsconfig.json                # TypeScript configuration
├── electron-builder.yml         # Build configuration
├── README.md                    # This file
└── DEVELOPER_WALKTHROUGH.md     # Detailed architecture guide
```

---

## 🎓 Learning Resources

### For Beginners:

1. **Start here:** `DEVELOPER_WALKTHROUGH.md`
   - Explains every file and why it exists
   - Detailed code comments
   - Clear analogies and examples

2. **Read the code files** in this order:
   - `src/shared/ipc-channels.ts` - Communication channels
   - `src/shared/interfaces/` - Data structures
   - `src/main/main.ts` - Main process
   - `src/main/preload.ts` - Security bridge
   - `src/renderer/index.html` - UI shell

3. **Official Documentation:**
   - [Electron Docs](https://www.electronjs.org/docs/latest/)
   - [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
   - [React Tutorial](https://react.dev/learn)

---

## 🔧 Configuration

### First Run:

1. Launch the app
2. Set your Jira URL (e.g., `https://company.atlassian.net`)
3. Configure a task:
   - Choose task type (e.g., "Update Due Dates")
   - Enter JQL query (e.g., `project = ABC AND status = "To Do"`)
   - Set parameters (e.g., "10 days before FixVersion")
4. Click "Start"

### Configuration File Location:

- **Windows:** `C:\Users\YourName\AppData\Roaming\jira-automation-assistant\config.json`
- **Mac:** `~/Library/Application Support/jira-automation-assistant/config.json`
- **Linux:** `~/.config/jira-automation-assistant/config.json`

### Configuration Options:

```typescript
{
  "jiraBaseUrl": "https://company.atlassian.net",
  "throttling": {
    "minDelayMs": 500,      // Min wait between actions
    "maxDelayMs": 2000,     // Max wait (randomized for human-like behavior)
    "pageLoadTimeoutMs": 30000
  },
  "retryPolicy": {
    "maxRetries": 3,
    "backoffMultiplier": 2   // Exponential backoff: 1s, 2s, 4s
  },
  "ui": {
    "showBrowserWindow": true,  // Show Jira window during automation
    "darkMode": false
  },
  "tasks": [/* Your automation tasks */]
}
```

---

## 🚨 Troubleshooting

### App won't start:

**Problem:** "window.electron is undefined"
```bash
# Solution: Rebuild the project
npm run build
# Then restart the app
```

**Problem:** Blank white screen
```bash
# Check the terminal for errors
# Common cause: TypeScript not compiled
npm run build
```

### Automation not working:

**Problem:** Can't find Jira elements
- **Cause:** Jira's HTML structure changed
- **Solution:** Update selectors in `src/automation/modules/`

**Problem:** Session expired
- **Cause:** You're not logged into Jira
- **Solution:** Log in manually in the Jira window, then resume automation

### Build errors:

**Problem:** `npm run package` fails
```bash
# Solution: Clean and rebuild
npm run clean
npm install
npm run build
npm run package
```

---

## 🔐 Security & Compliance

### Why This Approach Is Safe:

✅ **No credential storage** - Uses your existing browser session
✅ **Transparent operation** - You can watch it work
✅ **Auditable** - All code is reviewable
✅ **Local only** - No cloud components or external calls
✅ **Respects permissions** - Uses YOUR Jira access rights

### Enterprise Considerations:

- ✅ No browser extension installation required
- ✅ No elevated privileges needed
- ✅ Equivalent to Selenium/RPA tools
- ✅ Can be code-signed for Windows SmartScreen
- ✅ Runs in user space only

---

## 🤝 Contributing

### Adding New Features:

See `DEVELOPER_WALKTHROUGH.md` - Section: "How To Add New Features"

Quick steps:
1. Add new TaskType enum value
2. Create interface for task config
3. Write automation module
4. Wire it up in jira-injector.ts

### Code Style:

- ✅ Use TypeScript strict mode
- ✅ Add detailed comments explaining WHY, not just WHAT
- ✅ Follow existing naming conventions
- ✅ Test with real Jira instance before committing

---

## 📝 Changelog

### Version 1.0.0 (Current)

- ✅ Initial project structure
- ✅ Electron + TypeScript setup
- ✅ IPC communication framework
- ✅ Configuration management
- ✅ Basic UI shell
- ⏳ React components (in progress)
- ⏳ Automation engine (in progress)

### Planned Features:

- [ ] Due date automation (based on FixVersion)
- [ ] PR linking and comment injection
- [ ] Bulk field updates
- [ ] Scheduled automation (cron-like)
- [ ] Multi-task parallel execution
- [ ] Detailed logging and reporting
- [ ] Task templates library

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🆘 Support

### Documentation:

- **Architecture Guide:** `DEVELOPER_WALKTHROUGH.md`
- **Code Comments:** Every file is heavily commented
- **Inline Help:** Check console logs for debugging info

### Getting Help:

1. Check `DEVELOPER_WALKTHROUGH.md` first
2. Look for `Developer Notes` comments in code files
3. Check console output (F12 in Electron window)
4. Review the Troubleshooting section above

---

## 🎯 Quick Start Checklist

- [ ] Install Node.js 18+
- [ ] Run `npm install`
- [ ] Run `npm run build`
- [ ] Run `npm run dev`
- [ ] Set Jira URL in the app
- [ ] Configure your first task
- [ ] Click "Start" and watch it work!

---

**Built with ❤️ for teams who need Jira automation without API access**
