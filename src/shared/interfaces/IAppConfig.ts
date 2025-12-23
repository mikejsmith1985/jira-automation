/*
 * ============================================================================
 * APP CONFIGURATION INTERFACE - Application Settings
 * ============================================================================
 * 
 * WHAT IS THIS FILE FOR?
 * ---------------------
 * This defines ALL the settings that users can configure in the app.
 * 
 * Think of it like a settings menu in any app:
 *   - Jira URL
 *   - How fast to run automation
 *   - What to do when things fail
 *   - Which tasks are configured
 * 
 * 
 * WHY HAVE A CONFIG FILE?
 * -----------------------
 * Users shouldn't have to re-enter settings every time they open the app.
 * 
 * This config is:
 *   - Saved to disk as config.json
 *   - Loaded when app starts
 *   - Updated when user changes settings
 * 
 * 
 * WHERE IS IT STORED?
 * -------------------
 * On Windows: C:\Users\YourName\AppData\Roaming\jira-automation\config.json
 * On Mac: ~/Library/Application Support/jira-automation/config.json
 */

import { IAutomationTask } from './IAutomationTask';

/**
 * IAppConfig - The Complete Application Configuration
 * 
 * WHAT'S IN HERE?
 * ---------------
 * - Jira connection info
 * - Performance/safety settings
 * - UI preferences
 * - All automation tasks
 */
export interface IAppConfig {
  /**
   * The base URL of your Jira instance
   * Example: "https://mycompany.atlassian.net"
   *          "https://jira.mycompany.com"
   * 
   * WHY: The app needs to know where to load Jira from
   * 
   * NOTE: NO trailing slash!
   *   ✓ Good: "https://mycompany.atlassian.net"
   *   ✗ Bad:  "https://mycompany.atlassian.net/"
   */
  jiraBaseUrl: string;
  
  /**
   * Throttling - How Fast Should Automation Run?
   * 
   * WHAT IS THROTTLING?
   * -------------------
   * If automation runs too fast, it looks like a bot.
   * Jira might block you, or IT security might flag suspicious activity.
   * 
   * Throttling adds random delays between actions to look more human.
   * 
   * EXAMPLE:
   *   Without throttling: Click, click, click, click (instant - looks like a bot)
   *   With throttling: Click... wait 1.2 seconds... Click... wait 0.8 seconds...
   */
  throttling: {
    /**
     * Minimum delay between actions (milliseconds)
     * Example: 500 = wait at least 0.5 seconds
     * 
     * WHY: Even fast humans take some time to click
     */
    minDelayMs: number;
    
    /**
     * Maximum delay between actions (milliseconds)
     * Example: 2000 = wait at most 2 seconds
     * 
     * WHY: Humans are inconsistent - sometimes they're fast, sometimes slow
     * Random delays between min and max look more human
     */
    maxDelayMs: number;
    
    /**
     * How long to wait for a Jira page to load (milliseconds)
     * Example: 30000 = 30 seconds
     * 
     * WHY: Sometimes Jira is slow
     * If we give up too early, automation fails unnecessarily
     */
    pageLoadTimeoutMs: number;
  };
  
  /**
   * Retry Policy - What To Do When Things Fail
   * 
   * WHAT CAN GO WRONG?
   * ------------------
   * - Network hiccup (temporary)
   * - Jira is slow to respond (temporary)
   * - Can't find a button (might appear after a moment)
   * 
   * Instead of giving up immediately, we retry with exponential backoff.
   * 
   * EXPONENTIAL BACKOFF:
   *   Attempt 1: Fail -> Wait 1 second -> Retry
   *   Attempt 2: Fail -> Wait 2 seconds -> Retry
   *   Attempt 3: Fail -> Wait 4 seconds -> Give up
   */
  retryPolicy: {
    /**
     * How many times to retry before giving up?
     * Example: 3
     * 
     * WHY: Balance between "don't give up too easily" and "don't hang forever"
     * 
     * NOTE: 3 retries = 4 total attempts (initial + 3 retries)
     */
    maxRetries: number;
    
    /**
     * How much to multiply the wait time after each failure
     * Example: 2 means double the wait time each retry
     * 
     * WHY: If Jira is overloaded, waiting longer gives it time to recover
     * 
     * EXAMPLE with backoffMultiplier = 2:
     *   Attempt 1: Fail -> Wait 1 second
     *   Attempt 2: Fail -> Wait 2 seconds (1 * 2)
     *   Attempt 3: Fail -> Wait 4 seconds (2 * 2)
     *   Attempt 4: Fail -> Give up
     */
    backoffMultiplier: number;
  };
  
  /**
   * UI Preferences - How Should the App Look and Behave?
   */
  ui: {
    /**
     * Should we show the Jira browser window during automation?
     * Example: true
     * 
     * WHY: Some users want to see what's happening (transparency)
     *      Others want it hidden (less screen clutter)
     * 
     * SECURITY NOTE: Keeping it visible is safer for enterprise environments
     *                Hidden automation might be flagged as suspicious
     */
    showBrowserWindow: boolean;
    
    /**
     * Use dark mode for the UI?
     * Example: false
     * 
     * WHY: User preference for light/dark theme
     */
    darkMode: boolean;
  };
  
  /**
   * All automation tasks configured by the user
   * Example: [
   *   { id: "task_123", name: "Update Due Dates", enabled: true, ... },
   *   { id: "task_456", name: "Link PRs", enabled: false, ... }
   * ]
   * 
   * WHY: Users can configure multiple automation tasks
   *      Each task is independent and can be enabled/disabled
   */
  tasks: IAutomationTask[];
}


/**
 * DEFAULT_CONFIG - Sensible Default Settings
 * 
 * WHAT IS THIS?
 * -------------
 * When a user runs the app for the first time, there's no config.json yet.
 * We use these default values.
 * 
 * WHY DEFAULT VALUES?
 * -------------------
 * - App works immediately without configuration
 * - Safe, conservative settings (slow speed, many retries)
 * - User can customize later
 */
export const DEFAULT_CONFIG: IAppConfig = {
  // User must set their own Jira URL
  jiraBaseUrl: "",
  
  // Throttling: Slow and human-like by default
  throttling: {
    minDelayMs: 500,        // Wait at least 0.5 seconds
    maxDelayMs: 2000,       // Wait at most 2 seconds
    pageLoadTimeoutMs: 30000 // Give Jira 30 seconds to load
  },
  
  // Retry policy: Patient and persistent
  retryPolicy: {
    maxRetries: 3,          // Try 4 times total before giving up
    backoffMultiplier: 2    // Double the wait time after each failure
  },
  
  // UI: Visible and light mode
  ui: {
    showBrowserWindow: true, // Show Jira window (transparency)
    darkMode: false          // Use light theme
  },
  
  // No tasks configured yet
  tasks: []
};


/*
 * ============================================================================
 * HOW CONFIG IS USED IN THE APP
 * ============================================================================
 * 
 * 1. APP STARTS:
 * 
 *    - Main process tries to read config.json from disk
 *    - If file doesn't exist, use DEFAULT_CONFIG
 *    - Send config to Renderer via IPC_CHANNELS.CONFIG_LOADED
 * 
 * 2. RENDERER DISPLAYS SETTINGS:
 * 
 *    - Show Jira URL input (pre-filled with jiraBaseUrl)
 *    - Show speed slider (mapped to minDelayMs/maxDelayMs)
 *    - Show list of tasks
 * 
 * 3. USER CHANGES SETTINGS:
 * 
 *    - User types new Jira URL
 *    - Renderer sends update via IPC_CHANNELS.SAVE_CONFIG
 *    - Main process writes config.json to disk
 * 
 * 4. AUTOMATION USES CONFIG:
 * 
 *    - Read throttling.minDelayMs -> Wait random time before each click
 *    - Read retryPolicy.maxRetries -> Retry failed actions
 *    - Read tasks array -> Know which automations to run
 * 
 * 
 * ============================================================================
 * EXAMPLE: LOADING CONFIG
 * ============================================================================
 * 
 * // In main.ts
 * import { IAppConfig, DEFAULT_CONFIG } from '../shared/interfaces/IAppConfig';
 * import * as fs from 'fs';
 * import * as path from 'path';
 * 
 * function loadConfig(): IAppConfig {
 *   const configPath = path.join(app.getPath('userData'), 'config.json');
 *   
 *   try {
 *     // Try to read existing config
 *     const data = fs.readFileSync(configPath, 'utf8');
 *     return JSON.parse(data) as IAppConfig;
 *   } catch (error) {
 *     // File doesn't exist or is invalid, use defaults
 *     console.log('No config found, using defaults');
 *     return DEFAULT_CONFIG;
 *   }
 * }
 * 
 * 
 * ============================================================================
 * EXAMPLE: SAVING CONFIG
 * ============================================================================
 * 
 * // In main.ts
 * function saveConfig(config: IAppConfig): void {
 *   const configPath = path.join(app.getPath('userData'), 'config.json');
 *   
 *   // Write to disk (pretty-printed JSON)
 *   fs.writeFileSync(configPath, JSON.stringify(config, null, 2), 'utf8');
 *   
 *   console.log('Config saved to:', configPath);
 * }
 * 
 * 
 * ============================================================================
 * EXAMPLE: USING CONFIG IN AUTOMATION
 * ============================================================================
 * 
 * // In automation script
 * function getRandomDelay(config: IAppConfig): number {
 *   const min = config.throttling.minDelayMs;
 *   const max = config.throttling.maxDelayMs;
 *   
 *   // Return random number between min and max
 *   return Math.random() * (max - min) + min;
 * }
 * 
 * async function clickElement(element: HTMLElement, config: IAppConfig) {
 *   // Wait a human-like random time
 *   const delay = getRandomDelay(config);
 *   await sleep(delay);
 *   
 *   // Now click
 *   element.click();
 * }
 */
