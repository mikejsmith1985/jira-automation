# 🎓 DEVELOPER WALKTHROUGH - Jira Automation Assistant

**Welcome!** This document explains the ENTIRE application architecture like you're 5 years old (but with code examples).

---

## 📚 TABLE OF CONTENTS

1. [What Is This App?](#what-is-this-app)
2. [The Big Picture](#the-big-picture)
3. [File-by-File Walkthrough](#file-by-file-walkthrough)
4. [How Data Flows](#how-data-flows)
5. [How To Run It](#how-to-run-it)
6. [How To Add New Features](#how-to-add-new-features)
7. [Common Problems & Solutions](#common-problems--solutions)

---

## 🎯 WHAT IS THIS APP?

**The Problem:**
- You have 500 Jira issues that need updating
- Clicking each one manually takes FOREVER
- You don't have API access (company policy)

**The Solution:**
- This app pretends to be YOU
- It opens Jira in a browser window
- It clicks buttons and fills in fields automatically
- Just like you would, but 100x faster

**Key Features:**
- ✅ No Jira API needed (works through the web UI)
- ✅ Single .exe file (no installation required)
- ✅ No admin rights needed
- ✅ Uses YOUR session (your SSO, your permissions)
- ✅ Completely transparent (you can watch it work)

---

## 🏗️ THE BIG PICTURE

### Think of the app like a RESTAURANT:

```
┌─────────────────────────────────────────────────────────┐
│  YOU (The Customer)                                      │
│  - Click buttons in the UI                               │
│  - See progress updates                                  │
└────────────────┬────────────────────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────────────────┐
│  MAIN PROCESS (The Manager)                            │
│  - Manages windows                                      │
│  - Saves/loads config files                             │
│  - Coordinates between UI and automation                │
└────────────────┬────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ↓                 ↓
┌───────────────┐  ┌──────────────────┐
│  RENDERER     │  │  JIRA WINDOW     │
│  (The Menu)   │  │  (The Kitchen)   │
│  - React UI   │  │  - Loads Jira    │
│  - Forms      │  │  - Clicks buttons│
│  - Buttons    │  │  - Updates fields│
└───────────────┘  └──────────────────┘
```

### The Three "Worlds" of Electron:

1. **MAIN PROCESS** (`src/main/main.ts`)
   - The "boss" of the app
   - Can access files, create windows, etc.
   - Runs Node.js code
   - ONE instance for the whole app

2. **RENDERER PROCESS** (`src/renderer/`)
   - The pretty interface you see
   - Runs React (like a website)
   - Sandboxed for security (can't access files directly)
   - ONE instance per window

3. **PRELOAD SCRIPT** (`src/main/preload.ts`)
   - The "bouncer" between Main and Renderer
   - Controls what the UI can access
   - Security layer
   - Runs before the Renderer loads

---

## 📁 FILE-BY-FILE WALKTHROUGH

### 🔧 **Configuration Files** (Project Setup)

#### `package.json`
**What it is:** The "recipe card" for your app
**What it contains:**
- App name and version
- List of dependencies (libraries you need)
- Scripts to run the app (`npm run dev`, `npm run build`)
- Build instructions for electron-builder

**When you need it:**
- Adding new npm packages: `npm install package-name` updates this file
- Changing app name/version: Edit the `name` and `version` fields
- Adding new scripts: Add to the `scripts` section

---

#### `tsconfig.json`
**What it is:** Instructions for TypeScript compiler
**What it contains:**
- Which JavaScript version to output (ES2020)
- Where source files are (`src/`)
- Where compiled files go (`dist/`)
- Strict type-checking rules

**When you need it:**
- Rarely! It's pre-configured correctly
- If you get weird TypeScript errors, check this file

---

#### `electron-builder.yml`
**What it is:** Instructions for building the .exe file
**What it contains:**
- Output file name ("Jira Automation Assistant.exe")
- What files to include in the build
- Icon for the app (you'll need to create icon.ico)
- Build target: "portable" (no installer needed)

**When you need it:**
- When you run `npm run package` to create the .exe
- To change the app icon or name

---

### 🧱 **Shared Code** (Used by Multiple Parts)

#### `src/shared/ipc-channels.ts`
**What it is:** The "walkie-talkie frequency list"
**What it does:** Defines message channel names

**Why we need it:**
```typescript
// ❌ BAD: Easy to typo
ipcRenderer.send("automation:start", data);
ipcMain.on("automaton:start", ...);  // Typo! Won't work

// ✅ GOOD: TypeScript catches mistakes
ipcRenderer.send(IPC_CHANNELS.START_AUTOMATION, data);
ipcMain.on(IPC_CHANNELS.START_AUTOMATION, ...);  // Same constant = works
```

**Channels we have:**
- `START_AUTOMATION`: User clicks "Start" button
- `STOP_AUTOMATION`: User clicks "Stop" button
- `PROGRESS_UPDATE`: Automation reports progress
- `AUTOMATION_ERROR`: Something went wrong
- ...and more (see the file for full list)

---

#### `src/shared/interfaces/IAutomationTask.ts`
**What it is:** Defines what an automation task looks like
**What it contains:**

```typescript
interface IAutomationTask {
  id: string;              // Unique identifier
  type: TaskType;          // What kind of task? (UPDATE_DUE_DATE, LINK_PR, etc.)
  name: string;            // Display name
  enabled: boolean;        // Is it active?
  config: ITaskConfig;     // Task-specific settings
}
```

**Why we need it:**
Without this, you could create a task with wrong fields and TypeScript wouldn't catch it.

**Example usage:**
```typescript
const myTask: IAutomationTask = {
  id: "task_123",
  type: TaskType.UPDATE_DUE_DATE,
  name: "Set Due Dates",
  enabled: true,
  config: {
    jqlQuery: "project = ABC",
    daysBeforeFixVersion: 10
  }
};
```

---

#### `src/shared/interfaces/IProgressUpdate.ts`
**What it is:** Defines progress update structure
**What it contains:**

```typescript
interface IProgressUpdate {
  taskId: string;           // Which task is this for?
  totalIssues: number;      // How many total?
  processedIssues: number;  // How many done?
  currentIssue?: { ... };   // What's being processed now?
  issues: [ ... ];          // History of all processed issues
}
```

**Why we need it:**
The UI needs to show:
- Progress bar: 30/50 = 60%
- Current status: "Processing ABC-123..."
- Log window: List of all processed issues

**Example usage:**
```typescript
const progress: IProgressUpdate = {
  taskId: "task_123",
  totalIssues: 50,
  processedIssues: 30,
  currentIssue: {
    issueKey: "ABC-123",
    status: UpdateStatus.IN_PROGRESS,
    timestamp: new Date()
  },
  issues: [/* ... */]
};

// Send to UI
mainWindow.webContents.send(IPC_CHANNELS.PROGRESS_UPDATE, progress);
```

---

#### `src/shared/interfaces/IAppConfig.ts`
**What it is:** Defines all app settings
**What it contains:**

```typescript
interface IAppConfig {
  jiraBaseUrl: string;           // Where is Jira?
  throttling: { ... };           // How fast to run?
  retryPolicy: { ... };          // How to handle failures?
  ui: { ... };                   // UI preferences
  tasks: IAutomationTask[];      // User's automation tasks
}
```

**Why we need it:**
All settings in one place, saved to disk, loaded on startup.

**Where it's saved:**
- Windows: `C:\Users\YourName\AppData\Roaming\jira-automation-assistant\config.json`
- Mac: `~/Library/Application Support/jira-automation-assistant/config.json`

---

### 🎛️ **Main Process** (The Boss)

#### `src/main/main.ts`
**What it is:** The entry point - first file that runs
**What it does:**

1. **Creates windows:**
   ```typescript
   createMainWindow();  // The UI you see
   createJiraWindow();  // Hidden window that loads Jira
   ```

2. **Manages config:**
   ```typescript
   loadConfig();   // Read from disk
   saveConfig();   // Write to disk
   ```

3. **Handles IPC messages:**
   ```typescript
   ipcMain.on(IPC_CHANNELS.START_AUTOMATION, (event, payload) => {
     // User clicked "Start" - begin automation
   });
   ```

4. **Coordinates automation:**
   ```typescript
   startAutomation();  // Tell Jira window to start clicking
   stopAutomation();   // Tell it to stop
   ```

**When you'd modify this:**
- Adding new IPC channels
- Changing window sizes/settings
- Adding new app lifecycle hooks

---

#### `src/main/preload.ts`
**What it is:** The security bridge between Main and Renderer
**What it does:**

Creates a safe API that the UI can use:

```typescript
// In preload.ts
contextBridge.exposeInMainWorld('electron', {
  send: (channel, data) => {
    ipcRenderer.send(channel, data);
  },
  on: (channel, callback) => {
    ipcRenderer.on(channel, callback);
  }
});

// Now in Renderer (React), you can do:
window.electron.send(IPC_CHANNELS.START_AUTOMATION, data);
```

**Why we need it:**
Without this, the Renderer would have NO access to the Main process.
It's sandboxed for security.

**Security note:**
This file controls WHAT the UI can access. Don't expose dangerous functions like:
- `fs.readFile` (UI could read any file on computer)
- `child_process.exec` (UI could run any command)

---

### 🎨 **Renderer** (The UI)

#### `src/renderer/index.html`
**What it is:** The main HTML page
**What it contains:**
- Basic HTML structure
- Loads the React app
- Includes CSS

**You rarely touch this** - most UI work is in React components.

---

#### `src/renderer/App.tsx`
**What it is:** The root React component
**What it contains:**
- ControlPanel (start/stop buttons, settings)
- ProgressMonitor (progress bar, current status)
- LogViewer (scrolling list of processed issues)

**Structure:**
```typescript
function App() {
  const [config, setConfig] = useState<IAppConfig>(DEFAULT_CONFIG);
  const [progress, setProgress] = useState<IProgressUpdate | null>(null);
  
  // Load config on startup
  useEffect(() => {
    window.electron.send(IPC_CHANNELS.LOAD_CONFIG);
    window.electron.on(IPC_CHANNELS.CONFIG_LOADED, (config) => {
      setConfig(config);
    });
  }, []);
  
  return (
    <div>
      <ControlPanel config={config} onStart={...} onStop={...} />
      <ProgressMonitor progress={progress} />
      <LogViewer issues={progress?.issues || []} />
    </div>
  );
}
```

---

### 🤖 **Automation** (The Worker)

#### `src/automation/jira-injector.ts`
**What it is:** The script that runs INSIDE the Jira page
**What it does:**

1. **Finds issues:**
   ```typescript
   // Read issue keys from JQL results page
   const issueKeys = document.querySelectorAll('.issue-key');
   ```

2. **Clicks buttons:**
   ```typescript
   // Simulate human clicking "Edit" button
   const editButton = document.querySelector('[aria-label="Edit"]');
   editButton?.click();
   ```

3. **Fills in fields:**
   ```typescript
   // Set due date
   const dueDateField = document.querySelector('#duedate');
   dueDateField.value = '2025-01-17';
   ```

4. **Reports progress:**
   ```typescript
   // Tell main process we finished an issue
   ipcRenderer.send(IPC_CHANNELS.FIELD_UPDATE_RESULT, {
     issueKey: 'ABC-123',
     success: true
   });
   ```

**This is where the magic happens!**

---

## 🌊 HOW DATA FLOWS

Let's trace what happens when you click "Start Automation":

### Step 1: User clicks "Start" button
```typescript
// In ControlPanel.tsx
<button onClick={() => {
  window.electron.send(IPC_CHANNELS.START_AUTOMATION, {
    taskId: "task_123",
    config: { jqlQuery: "project = ABC", ... }
  });
}}>
  Start
</button>
```

### Step 2: Message goes to Main Process
```typescript
// In main.ts
ipcMain.on(IPC_CHANNELS.START_AUTOMATION, (event, payload) => {
  startAutomation(payload.taskId, payload.config);
});
```

### Step 3: Main creates Jira window
```typescript
// In main.ts
function startAutomation(taskId, config) {
  if (!jiraWindow) {
    createJiraWindow(config.jiraBaseUrl, visible);
  }
}
```

### Step 4: Jira loads, automation starts
```typescript
// In jira-injector.ts (runs in Jira page)
const issues = findIssues(config.jqlQuery);
for (const issue of issues) {
  await processIssue(issue);
}
```

### Step 5: Automation reports progress
```typescript
// In jira-injector.ts
ipcRenderer.send(IPC_CHANNELS.PROGRESS_UPDATE, {
  taskId,
  processedIssues: 1,
  totalIssues: 50,
  currentIssue: { issueKey: "ABC-123", status: "SUCCESS" }
});
```

### Step 6: Main forwards to UI
```typescript
// In main.ts
ipcMain.on(IPC_CHANNELS.PROGRESS_UPDATE, (event, progress) => {
  mainWindow.webContents.send(IPC_CHANNELS.PROGRESS_UPDATE, progress);
});
```

### Step 7: UI updates
```typescript
// In App.tsx
window.electron.on(IPC_CHANNELS.PROGRESS_UPDATE, (progress) => {
  setProgress(progress);
  // Progress bar updates: 1/50 = 2%
  // Log window shows: "ABC-123: ✓ Success"
});
```

---

## 🚀 HOW TO RUN IT

### First Time Setup:
```bash
# 1. Install dependencies
npm install

# 2. Build TypeScript
npm run build

# 3. Run the app
npm run dev
```

### Development Workflow:
```bash
# Terminal 1: Watch TypeScript files (auto-compile on save)
npm run watch:ts

# Terminal 2: Run Electron
npm run start:electron
```

### Build for Distribution:
```bash
# Creates JiraAutomationAssistant.exe in release/ folder
npm run package
```

---

## ➕ HOW TO ADD NEW FEATURES

### Adding a New Automation Task Type:

**Step 1: Add to TaskType enum**
```typescript
// In IAutomationTask.ts
export enum TaskType {
  UPDATE_DUE_DATE = "update_due_date",
  LINK_PR = "link_pr",
  MY_NEW_TASK = "my_new_task",  // <-- Add this
}
```

**Step 2: Create config interface**
```typescript
// In IAutomationTask.ts
export interface IMyNewTaskConfig extends ITaskConfig {
  myCustomSetting: string;
}
```

**Step 3: Create automation module**
```typescript
// Create src/automation/modules/my-new-task.ts
export async function runMyNewTask(config: IMyNewTaskConfig) {
  // Your automation logic here
  // Click buttons, fill fields, etc.
}
```

**Step 4: Wire it up in jira-injector.ts**
```typescript
// In jira-injector.ts
switch (task.type) {
  case TaskType.UPDATE_DUE_DATE:
    await runDueDateTask(task.config);
    break;
  case TaskType.MY_NEW_TASK:
    await runMyNewTask(task.config);  // <-- Add this
    break;
}
```

**Done!** Users can now create tasks of your new type.

---

## 🐛 COMMON PROBLEMS & SOLUTIONS

### Problem: "window.electron is undefined"
**Cause:** Preload script didn't expose the API
**Solution:**
- Check `preload.ts` has `contextBridge.exposeInMainWorld('electron', ...)`
- Check `main.ts` has `preload: path.join(__dirname, 'preload.js')` in BrowserWindow options
- Rebuild: `npm run build`

---

### Problem: IPC messages not working
**Cause:** Channel names don't match
**Solution:**
- Use `IPC_CHANNELS` constants everywhere
- Check spelling: `IPC_CHANNELS.START_AUTOMATION` (not "START_AUTOMAT1ON")
- Check both sender and receiver are using same channel

---

### Problem: "Cannot find module" errors
**Cause:** TypeScript hasn't compiled yet
**Solution:**
```bash
# Compile TypeScript
npm run build

# Or run watch mode (auto-compiles on save)
npm run watch:ts
```

---

### Problem: Automation can't find Jira elements
**Cause:** Jira's HTML structure changed, or page hasn't loaded yet
**Solution:**
- Add waits: `await waitForElement('.issue-key', 5000)`
- Use multiple fallback selectors
- Check Jira page manually - did they redesign it?

---

### Problem: App works in dev but crashes when packaged
**Cause:** File paths are different in packaged app
**Solution:**
- Use `__dirname` for file paths (NOT relative paths like `./file.js`)
- Use `app.getPath('userData')` for user data
- Test with: `npm run package` then run the .exe

---

## 🎓 LEARNING PATH

**Week 1: Understand the structure**
- Read this document
- Open each file and read the comments
- Run the app and explore

**Week 2: Make small changes**
- Change button text in UI
- Add a console.log in main.ts
- Modify default config values

**Week 3: Add a feature**
- Add a new button that shows an alert
- Add a new config setting
- Create a new IPC channel

**Week 4: Build something real**
- Implement a new automation task type
- Add error handling
- Write tests

---

## 📖 ADDITIONAL RESOURCES

**Electron Documentation:**
- https://www.electronjs.org/docs/latest/

**TypeScript Handbook:**
- https://www.typescriptlang.org/docs/handbook/intro.html

**React Tutorial:**
- https://react.dev/learn

**DOM Manipulation:**
- https://developer.mozilla.org/en-US/docs/Web/API/Document_Object_Model

---

## ✅ SUMMARY

**The app has 3 main parts:**
1. **Main Process** - Manages everything
2. **Renderer** - The UI you see
3. **Automation** - Clicks buttons in Jira

**They communicate via IPC messages:**
- UI sends: "Start automation!"
- Main creates Jira window
- Automation clicks buttons
- Automation sends progress updates
- UI shows progress

**Everything is TypeScript:**
- Catch errors before running
- Interfaces define data shapes
- Better autocomplete in your editor

**Configuration is saved to disk:**
- User doesn't re-enter settings every time
- JSON file in AppData folder

**It's modular and scalable:**
- Easy to add new automation types
- Each task type is a separate module
- Won't break existing features

---

**You now understand the entire architecture! 🎉**

Next: Start reading the actual code files with these concepts in mind.
