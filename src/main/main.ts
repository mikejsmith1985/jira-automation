/*
 * ============================================================================
 * MAIN.TS - The "Brain" of the Electron App
 * ============================================================================
 * 
 * This is the MAIN PROCESS - the first file that runs when you open the app.
 * It manages windows, handles files, and coordinates communication.
 */

import { app, BrowserWindow, ipcMain } from 'electron';
import * as path from 'path';
import * as fs from 'fs';

import { IPC_CHANNELS } from '../shared/ipc-channels';
import { IAppConfig, DEFAULT_CONFIG } from '../shared/interfaces/IAppConfig';

// Global variables
let mainWindow: BrowserWindow | null = null;
let jiraWindow: BrowserWindow | null = null;
let currentConfig: IAppConfig = DEFAULT_CONFIG;

// File paths
function getConfigPath(): string {
  return path.join(app.getPath('userData'), 'config.json');
}

function getLogsPath(): string {
  return path.join(app.getPath('userData'), 'logs');
}

// Configuration management
function loadConfig(): IAppConfig {
  const configPath = getConfigPath();
  
  try {
    if (!fs.existsSync(configPath)) {
      console.log('No config file found, using defaults');
      return DEFAULT_CONFIG;
    }
    
    const fileContent = fs.readFileSync(configPath, 'utf8');
    const config = JSON.parse(fileContent) as IAppConfig;
    
    console.log('Config loaded successfully');
    return config;
    
  } catch (error) {
    console.error('Error loading config:', error);
    return DEFAULT_CONFIG;
  }
}

function saveConfig(config: IAppConfig): void {
  const configPath = getConfigPath();
  
  try {
    const jsonString = JSON.stringify(config, null, 2);
    fs.writeFileSync(configPath, jsonString, 'utf8');
    console.log('Config saved successfully');
    
  } catch (error) {
    console.error('Error saving config:', error);
    
    if (mainWindow) {
      mainWindow.webContents.send(IPC_CHANNELS.AUTOMATION_ERROR, {
        taskId: 'system',
        error: 'Failed to save configuration: ' + error
      });
    }
  }
}

// Window creation
function createMainWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  const htmlPath = path.join(__dirname, '..', 'renderer', 'index.html');
  mainWindow.loadFile(htmlPath);

  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
  
  console.log('Main window created');
}

function createJiraWindow(jiraUrl: string, visible: boolean): void {
  jiraWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    show: visible,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: true,
    },
  });

  jiraWindow.loadURL(jiraUrl);

  jiraWindow.webContents.on('did-finish-load', () => {
    console.log('Jira loaded, ready for automation');
    
    if (mainWindow) {
      mainWindow.webContents.send('jira:ready');
    }
  });

  jiraWindow.on('closed', () => {
    jiraWindow = null;
  });
  
  console.log('Jira window created');
}

// IPC handlers
function setupIpcHandlers(): void {
  
  ipcMain.on(IPC_CHANNELS.LOAD_CONFIG, (event) => {
    console.log('UI requested config');
    currentConfig = loadConfig();
    event.reply(IPC_CHANNELS.CONFIG_LOADED, currentConfig);
  });

  ipcMain.on(IPC_CHANNELS.SAVE_CONFIG, (event, newConfig: IAppConfig) => {
    console.log('UI requested config save');
    currentConfig = newConfig;
    saveConfig(currentConfig);
  });

  ipcMain.on(IPC_CHANNELS.START_AUTOMATION, (event, payload: { taskId: string, config: any }) => {
    console.log('Starting automation for task:', payload.taskId);
    startAutomation(payload.taskId, payload.config);
  });

  ipcMain.on(IPC_CHANNELS.STOP_AUTOMATION, (event, payload: { taskId: string }) => {
    console.log('Stopping automation for task:', payload.taskId);
    stopAutomation(payload.taskId);
  });
  
  console.log('IPC handlers set up');
}

// Automation control
async function startAutomation(taskId: string, config: any): Promise<void> {
  try {
    if (!currentConfig.jiraBaseUrl) {
      throw new Error('Jira URL not configured');
    }
    
    // Create Jira window if it doesn't exist
    if (!jiraWindow) {
      const visible = currentConfig.ui.showBrowserWindow;
      createJiraWindow(currentConfig.jiraBaseUrl, visible);
      
      // Wait for Jira to load
      await new Promise((resolve) => {
        if (jiraWindow) {
          jiraWindow.webContents.once('did-finish-load', resolve);
        }
      });
    }
    
    // Inject automation script
    await injectAutomationScript();
    
    // Find the task configuration
    const task = currentConfig.tasks.find(t => t.id === taskId);
    if (!task) {
      throw new Error(`Task ${taskId} not found in configuration`);
    }
    
    // Send start command to automation script
    if (jiraWindow) {
      jiraWindow.webContents.send('automation:start-command', {
        task,
        config: currentConfig
      });
    }
    
    console.log('Automation started successfully');
    
  } catch (error) {
    console.error('Error starting automation:', error);
    
    if (mainWindow) {
      mainWindow.webContents.send(IPC_CHANNELS.AUTOMATION_ERROR, {
        taskId,
        error: String(error)
      });
    }
  }
}

async function injectAutomationScript(): Promise<void> {
  if (!jiraWindow) return;
  
  try {
    const scriptPath = path.join(__dirname, '..', 'automation', 'jira-injector.js');
    
    if (!fs.existsSync(scriptPath)) {
      console.warn('Automation script not found, skipping injection');
      return;
    }
    
    const scriptContent = fs.readFileSync(scriptPath, 'utf8');
    await jiraWindow.webContents.executeJavaScript(scriptContent);
    
    console.log('Automation script injected successfully');
    
  } catch (error) {
    console.error('Error injecting automation script:', error);
    throw error;
  }
}

function stopAutomation(taskId: string): void {
  if (jiraWindow) {
    jiraWindow.webContents.send('automation:stop-command', { taskId });
    console.log('Stop command sent');
  }
}

// App lifecycle
app.on('ready', () => {
  console.log('App is ready');
  
  currentConfig = loadConfig();
  createMainWindow();
  setupIpcHandlers();
  
  const logsPath = getLogsPath();
  if (!fs.existsSync(logsPath)) {
    fs.mkdirSync(logsPath, { recursive: true });
  }
  
  console.log('Initialization complete');
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createMainWindow();
  }
});

app.on('before-quit', () => {
  console.log('App quitting, cleaning up...');
  
  if (jiraWindow) {
    jiraWindow.close();
    jiraWindow = null;
  }
});
