# 🏛️ ARCHITECTURE SUMMARY

**A comprehensive overview of the Jira Automation Assistant architecture**

---

## 📊 VISUAL OVERVIEW

### System Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│                          USER INTERFACE (You)                            │
│                                                                          │
│  • Click "Start Automation" button                                       │
│  • View progress updates                                                 │
│  • See logs and results                                                  │
│                                                                          │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │
                                 │ User Actions (clicks, form inputs)
                                 ↓
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│                        RENDERER PROCESS (React)                          │
│                                                                          │
│  Components:                                                             │
│  ┌────────────────┐  ┌─────────────────┐  ┌──────────────────┐          │
│  │  ControlPanel  │  │ ProgressMonitor │  │   LogViewer     │          │
│  │                │  │                 │  │                  │          │
│  │  - JQL input   │  │  - Progress bar │  │  - Issue list    │          │
│  │  - Start/Stop  │  │  - Current item │  │  - Status colors │          │
│  │  - Settings    │  │  - Stats        │  │  - Timestamps    │          │
│  └────────────────┘  └─────────────────┘  └──────────────────┘          │
│                                                                          │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │
                                 │ IPC Messages (Inter-Process Communication)
                                 │
                    ┌────────────┴────────────┐
                    │                         │
         Sends:     │                         │     Receives:
         • START_AUTOMATION                   │     • PROGRESS_UPDATE
         • STOP_AUTOMATION                    │     • AUTOMATION_COMPLETE
         • SAVE_CONFIG                        │     • AUTOMATION_ERROR
         • LOAD_CONFIG                        │     • CONFIG_LOADED
                    │                         │
                    ↓                         ↑
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│                    PRELOAD SCRIPT (Security Bridge)                      │
│                                                                          │
│  • Validates IPC channel names                                           │
│  • Prevents unauthorized access                                          │
│  • Exposes safe API: window.electron.send() / .on()                      │
│                                                                          │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │
                                 ↓
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│                        MAIN PROCESS (Electron)                           │
│                                                                          │
│  Responsibilities:                                                       │
│  • Create and manage windows                                             │
│  • Load/save configuration from disk                                     │
│  • Coordinate IPC messages                                               │
│  • Launch Jira automation window                                         │
│                                                                          │
│  Files:                                                                  │
│  • main.ts: App lifecycle, window management                             │
│  • config.json: User settings (saved to disk)                            │
│                                                                          │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │
                                 │ Creates & Controls
                                 ↓
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│                    JIRA AUTOMATION WINDOW (Hidden)                       │
│                                                                          │
│  • Loads actual Jira website                                             │
│  • Inherits your SSO session                                             │
│  • Runs injected automation scripts                                      │
│                                                                          │
│  Automation Flow:                                                        │
│  1. Find issues (via JQL results page)                                   │
│  2. Loop through each issue                                              │
│  3. Click "Edit" button                                                  │
│  4. Fill in fields                                                       │
│  5. Click "Save"                                                         │
│  6. Report progress                                                      │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 🗂️ FILE ORGANIZATION & PURPOSE

### Configuration Files (Project Root)

| File | Purpose | You Need To Touch It? |
|------|---------|----------------------|
| `package.json` | Defines dependencies, scripts, build settings | Only when adding npm packages |
| `tsconfig.json` | TypeScript compiler configuration | Rarely (pre-configured) |
| `electron-builder.yml` | Instructions for building .exe file | Only when changing app name/icon |
| `.gitignore` | Files to exclude from version control | Rarely |

---

### Shared Code (`src/shared/`)

**Used by BOTH main process and renderer**

| File | Purpose | What's Inside |
|------|---------|---------------|
| `ipc-channels.ts` | IPC channel name constants | Channel names like "automation:start" |
| `interfaces/IAutomationTask.ts` | Task structure definition | TaskType enum, task configs |
| `interfaces/IProgressUpdate.ts` | Progress reporting structure | UpdateStatus enum, progress tracking |
| `interfaces/IAppConfig.ts` | App configuration structure | Settings, throttling, retry policy |

**Why separate shared code?**
- TypeScript imports work from both main and renderer
- Single source of truth for data structures
- Changes automatically reflected everywhere

---

### Main Process (`src/main/`)

**The "Boss" - Manages everything**

| File | Lines of Code | Key Functions | Purpose |
|------|--------------|---------------|---------|
| `main.ts` | ~200 | `createMainWindow()`, `startAutomation()`, `loadConfig()` | Entry point, window management, IPC handlers |
| `preload.ts` | ~150 | `contextBridge.exposeInMainWorld()` | Security bridge between main and renderer |

**Flow in main.ts:**

```
App Starts
    ↓
Load config.json from disk
    ↓
Create main window (UI)
    ↓
Set up IPC handlers
    ↓
Wait for user actions
    ↓
User clicks "Start"
    ↓
Create Jira window
    ↓
Load Jira URL
    ↓
Inject automation script
    ↓
Forward progress updates to UI
    ↓
Display results
```

---

### Renderer / UI (`src/renderer/`)

**What the user sees and clicks**

| File | Purpose | Contains |
|------|---------|----------|
| `index.html` | HTML shell | Root `<div id="root">`, loads CSS/JS |
| `styles/app.css` | Visual styling | Colors, layouts, buttons, forms |
| `App.tsx` | Root React component | Combines all UI components |
| `components/ControlPanel.tsx` | Control panel UI | Start/stop buttons, settings form |
| `components/ProgressMonitor.tsx` | Progress display | Progress bar, current status |
| `components/LogViewer.tsx` | Log display | Scrolling list of processed issues |

**Component Hierarchy:**

```
App.tsx (Root)
    │
    ├── ControlPanel
    │       ├── JQL Query Input
    │       ├── Task Type Selector
    │       ├── Configuration Fields
    │       └── Start/Stop Buttons
    │
    ├── ProgressMonitor
    │       ├── Progress Bar (X / Y complete)
    │       ├── Current Status (Processing ABC-123...)
    │       └── Statistics (Success: 30, Failed: 2)
    │
    └── LogViewer
            └── Log Entry List
                    ├── ABC-120: ✓ Success
                    ├── ABC-121: ✗ Failed
                    └── ABC-122: ⏭ Skipped
```

---

### Automation Engine (`src/automation/`)

**The "Robot" - Clicks buttons in Jira**

| File | Purpose | What It Does |
|------|---------|--------------|
| `jira-injector.ts` | Main automation engine | Injected into Jira page, orchestrates automation |
| `modules/issue-reader.ts` | Issue extraction | Reads issue list from JQL results |
| `modules/field-updater.ts` | Field manipulation | Clicks edit, fills fields, saves |
| `modules/date-calculator.ts` | Date math | Calculates working days, skips holidays |
| `utils/retry-handler.ts` | Error handling | Retry logic with exponential backoff |
| `utils/throttle-manager.ts` | Human simulation | Random delays between actions |

**Automation Flow (Simplified):**

```typescript
// 1. Find all issues matching JQL
const issues = await findIssues(jqlQuery);

// 2. Loop through each issue
for (const issue of issues) {
    // 3. Open issue in edit mode
    await clickEditButton(issue.key);
    
    // 4. Fill in fields
    await setField('duedate', calculatedDate);
    
    // 5. Save
    await clickSaveButton();
    
    // 6. Report progress
    sendProgressUpdate(issue.key, 'SUCCESS');
    
    // 7. Wait (human-like)
    await randomDelay(500, 2000);
}

// 8. Done!
sendAutomationComplete();
```

---

## 📡 DATA FLOW EXAMPLES

### Example 1: User Starts Automation

```
Step 1: User clicks "Start" button
    ↓
    [ControlPanel.tsx]
    onClick={() => {
        window.electron.send(IPC_CHANNELS.START_AUTOMATION, {
            taskId: "task_123",
            config: { jqlQuery: "project = ABC", ... }
        });
    }}

Step 2: Message sent to Main Process
    ↓
    [preload.ts]
    Validates channel is allowed → ipcRenderer.send(...)

Step 3: Main Process receives message
    ↓
    [main.ts]
    ipcMain.on(IPC_CHANNELS.START_AUTOMATION, (event, payload) => {
        startAutomation(payload.taskId, payload.config);
    });

Step 4: Main creates Jira window
    ↓
    [main.ts]
    createJiraWindow(config.jiraBaseUrl, visible);

Step 5: Jira loads, automation script runs
    ↓
    [jira-injector.ts]
    const issues = await findIssues(config.jqlQuery);
    processIssues(issues);

Step 6: Automation reports progress
    ↓
    [jira-injector.ts]
    ipcRenderer.send(IPC_CHANNELS.PROGRESS_UPDATE, {
        processedIssues: 1,
        totalIssues: 50,
        ...
    });

Step 7: Main forwards to Renderer
    ↓
    [main.ts]
    mainWindow.webContents.send(IPC_CHANNELS.PROGRESS_UPDATE, progress);

Step 8: UI updates
    ↓
    [ProgressMonitor.tsx]
    useEffect(() => {
        window.electron.on(IPC_CHANNELS.PROGRESS_UPDATE, (progress) => {
            setProgress(progress);  // React re-renders with new data
        });
    }, []);
```

**Result:** Progress bar updates, log shows "ABC-123: ✓ Success"

---

### Example 2: Configuration Save

```
Step 1: User changes Jira URL and clicks "Save"
    ↓
    [ControlPanel.tsx]
    const handleSave = () => {
        const newConfig = {
            ...config,
            jiraBaseUrl: "https://new-url.atlassian.net"
        };
        window.electron.send(IPC_CHANNELS.SAVE_CONFIG, newConfig);
    };

Step 2: Main Process receives config
    ↓
    [main.ts]
    ipcMain.on(IPC_CHANNELS.SAVE_CONFIG, (event, newConfig) => {
        currentConfig = newConfig;
        saveConfig(newConfig);  // Writes to disk
    });

Step 3: Save to disk
    ↓
    [main.ts]
    function saveConfig(config) {
        const configPath = app.getPath('userData') + '/config.json';
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    }
```

**Result:** Config persists, loads next time app starts

---

## 🔐 SECURITY MODEL

### Electron Security Layers

```
┌────────────────────────────────────────────────┐
│  RENDERER (React UI)                           │
│  • Sandboxed                                   │
│  • Cannot access Node.js directly             │
│  • Cannot read/write files                    │
│  • Can only use window.electron API            │
└────────────────┬───────────────────────────────┘
                 │
                 │ Only allowed through Preload
                 ↓
┌────────────────────────────────────────────────┐
│  PRELOAD SCRIPT                                │
│  • Validates all IPC channel names             │
│  • Whitelists allowed channels                 │
│  • Strips dangerous event objects              │
│  • Exposes minimal safe API                    │
└────────────────┬───────────────────────────────┘
                 │
                 │ Controlled access
                 ↓
┌────────────────────────────────────────────────┐
│  MAIN PROCESS                                  │
│  • Full Node.js access                         │
│  • File system access                          │
│  • Can create windows                          │
│  • Can run shell commands                      │
└────────────────────────────────────────────────┘
```

**Key Security Principles:**

1. **Context Isolation** - Renderer can't access main process directly
2. **Channel Whitelisting** - Only specific IPC channels allowed
3. **No Node Integration** - Renderer can't require('fs') or require('child_process')
4. **Event Stripping** - Dangerous event.sender methods not passed to renderer

---

## 📦 BUILD & DISTRIBUTION

### Development Build Process

```
TypeScript Source (.ts files)
    ↓
    [tsc - TypeScript Compiler]
    ↓
JavaScript (.js files in dist/)
    ↓
    [electron - Electron Runtime]
    ↓
Running Application
```

### Production Build Process

```
Source Code (src/)
    ↓
    [npm run build - Compile TypeScript]
    ↓
JavaScript (dist/)
    ↓
    [electron-builder - Package]
    ↓
Single .exe File (release/)
    │
    ├── Includes Chromium engine
    ├── Includes Node.js runtime
    ├── Includes all dependencies
    └── No installation required
```

**Final Output:**
- `JiraAutomationAssistant.exe` (~120MB)
- Portable (can run from USB)
- No admin rights needed
- Works immediately

---

## 🎯 DESIGN DECISIONS

### Why Electron?

| Requirement | Electron Solution |
|-------------|-------------------|
| Single .exe file | ✅ electron-builder packages everything |
| No API access needed | ✅ Can load Jira website directly |
| Inherits user session | ✅ Uses system cookies automatically |
| Cross-platform | ✅ Works on Windows, Mac, Linux |
| Extensible | ✅ Easy to add new features |

### Why TypeScript?

| Benefit | Example |
|---------|---------|
| Catches errors early | Typos in variable names caught at compile time |
| Better autocomplete | IDE suggests available functions |
| Self-documenting | Types show what data looks like |
| Refactoring safety | Rename across entire codebase |

### Why Separate Processes?

| Process | Runs On | Can Access | Purpose |
|---------|---------|------------|---------|
| Main | Main thread | Everything | Boss / Coordinator |
| Renderer | Separate thread | Sandboxed | UI / User input |
| Automation | Separate window | Sandboxed (but in Jira) | Click buttons |

**Benefits:**
- UI stays responsive during automation
- Security (renderer can't access file system)
- Crash isolation (if one crashes, others survive)

---

## 🔄 LIFECYCLE SUMMARY

### App Startup Sequence

1. `main.ts` runs (main process starts)
2. Load `config.json` from disk
3. Create main window (UI)
4. Load `preload.js` (security bridge)
5. Load `index.html` (renderer)
6. Render React components
7. Request config from main process
8. Display UI with loaded settings
9. Ready for user input

### Automation Sequence

1. User configures task (JQL, settings)
2. User clicks "Start"
3. Renderer sends START_AUTOMATION message
4. Main process creates Jira window
5. Jira loads (uses user's existing session)
6. Main injects automation script
7. Script finds issues (JQL results)
8. Script loops through issues:
   - Click edit
   - Fill fields
   - Click save
   - Report progress
9. Script sends AUTOMATION_COMPLETE
10. Main forwards to renderer
11. UI shows final results

### App Shutdown Sequence

1. User closes main window
2. `window-all-closed` event fires
3. Main process cleans up:
   - Close Jira window
   - Save any unsaved data
4. App quits

---

## ✅ QUALITY CHECKLIST

### Code Quality

- ✅ Every file has detailed comments
- ✅ TypeScript strict mode enabled
- ✅ Interfaces define all data structures
- ✅ Error handling throughout
- ✅ No hardcoded values (use config)

### Security

- ✅ Context isolation enabled
- ✅ Node integration disabled in renderer
- ✅ IPC channels whitelisted
- ✅ No credentials stored
- ✅ Uses user's existing session

### Scalability

- ✅ Modular task system (easy to add new types)
- ✅ Separate automation modules
- ✅ Config-driven behavior
- ✅ Plugin-ready architecture

### User Experience

- ✅ Progress updates in real-time
- ✅ Error messages are helpful
- ✅ Can pause/stop automation
- ✅ Logs for debugging
- ✅ Settings persist

---

**This architecture is production-ready and extensible. You can now confidently build new features!**
