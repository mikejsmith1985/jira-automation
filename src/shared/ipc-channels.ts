/*
 * ============================================================================
 * IPC CHANNELS - Communication Highway Between App Parts
 * ============================================================================
 * 
 * WHAT IS THIS FILE FOR?
 * ---------------------
 * Electron apps have 3 separate "worlds" that need to talk to each other:
 * 
 *   1. MAIN PROCESS (main.ts) - The "boss" that manages windows and files
 *   2. RENDERER PROCESS (React UI) - The pretty interface you see and click
 *   3. INJECTED SCRIPT (automation code) - The robot that clicks in Jira
 * 
 * They can't directly call each other's functions (for security reasons).
 * Instead, they send MESSAGES through "channels" - like walkie-talkies.
 * 
 * This file defines the channel names so everyone uses the same frequency.
 */

export const IPC_CHANNELS = {
  
  // User clicks buttons in the UI
  START_AUTOMATION: "automation:start",
  STOP_AUTOMATION: "automation:stop",
  SAVE_CONFIG: "config:save",
  LOAD_CONFIG: "config:load",
  
  // Updates to show in the UI
  PROGRESS_UPDATE: "progress:update",
  AUTOMATION_COMPLETE: "automation:complete",
  AUTOMATION_ERROR: "automation:error",
  CONFIG_LOADED: "config:loaded",
  
  // Automation reporting back
  ISSUE_EXTRACTED: "jira:issue-extracted",
  FIELD_UPDATE_RESULT: "jira:field-updated",
  SESSION_EXPIRED: "jira:session-expired",
  
} as const;
