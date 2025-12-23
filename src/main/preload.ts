/*
 * ============================================================================
 * PRELOAD.TS - The Security Bridge
 * ============================================================================
 * 
 * WHAT IS THIS FILE?
 * ------------------
 * This is the "bouncer" at a club - it controls who can talk to whom.
 * 
 * In Electron:
 *   - The UI (Renderer) is sandboxed for security
 *   - It CAN'T directly access Node.js or Electron APIs
 *   - The Preload script creates a SAFE bridge
 * 
 * 
 * WHY DO WE NEED THIS?
 * --------------------
 * Imagine if any website could:
 *   - Read your files: fs.readFile('/passwords.txt')
 *   - Run commands: child_process.exec('rm -rf /')
 *   - Access your webcam, etc.
 * 
 * That would be DANGEROUS!
 * 
 * So Electron sandboxes the Renderer (UI).
 * The Preload script exposes ONLY safe, specific functions.
 * 
 * 
 * HOW DOES IT WORK?
 * -----------------
 * 1. This script runs BEFORE the Renderer loads
 * 2. It uses contextBridge to expose a safe API
 * 3. The Renderer can ONLY call functions we explicitly allow
 * 
 * 
 * EXAMPLE:
 * --------
 * ❌ DANGEROUS (without preload):
 *    // In Renderer, this would be terrible:
 *    const fs = require('fs');  // Access to entire file system!
 * 
 * ✅ SAFE (with preload):
 *    // Renderer can only do what we allow:
 *    window.electron.send('loadConfig');  // Sends IPC message (safe)
 *    window.electron.on('configLoaded', ...);  // Receives IPC message (safe)
 */

// ============================================================================
// IMPORTS
// ============================================================================

import { contextBridge, ipcRenderer } from 'electron';
import { IPC_CHANNELS } from '../shared/ipc-channels';

// ============================================================================
// EXPOSE SAFE API TO RENDERER
// ============================================================================

/*
 * contextBridge.exposeInMainWorld()
 * 
 * WHAT DOES THIS DO?
 * Creates a global variable in the Renderer called "electron"
 * 
 * IN THE RENDERER (React):
 *   window.electron.send(...)
 *   window.electron.on(...)
 * 
 * SECURITY NOTE:
 * We're ONLY exposing specific functions, not the entire ipcRenderer.
 * This prevents malicious code from doing bad things.
 */
contextBridge.exposeInMainWorld(
  'electron',  // This becomes window.electron in the Renderer
  {
    /**
     * send() - Send a message to the Main process
     * 
     * WHAT DOES IT DO?
     * Allows the Renderer to send IPC messages to Main process.
     * 
     * USAGE IN RENDERER:
     *   window.electron.send(IPC_CHANNELS.START_AUTOMATION, {
     *     taskId: "task_123",
     *     config: { ... }
     *   });
     * 
     * SECURITY:
     * We validate the channel is in our allowed list (IPC_CHANNELS).
     * This prevents sending messages on arbitrary channels.
     * 
     * @param channel - The IPC channel name (must be in IPC_CHANNELS)
     * @param data - The data to send (will be serialized to JSON)
     */
    send: (channel: string, data?: any) => {
      /*
       * CHANNEL VALIDATION
       * 
       * WHY?
       * We only want to allow specific, known channels.
       * This prevents a compromised Renderer from sending arbitrary messages.
       * 
       * EXAMPLE OF WHAT WE'RE PREVENTING:
       *   window.electron.send('malicious:steal-data', ...);  // Blocked!
       * 
       * ALLOWED CHANNELS (from IPC_CHANNELS):
       *   - START_AUTOMATION
       *   - STOP_AUTOMATION
       *   - SAVE_CONFIG
       *   - LOAD_CONFIG
       */
      const validChannels = [
        IPC_CHANNELS.START_AUTOMATION,
        IPC_CHANNELS.STOP_AUTOMATION,
        IPC_CHANNELS.SAVE_CONFIG,
        IPC_CHANNELS.LOAD_CONFIG,
      ];
      
      if (validChannels.includes(channel)) {
        // Channel is allowed, send the message
        ipcRenderer.send(channel, data);
      } else {
        // Channel is not allowed, log a warning
        console.warn(`Attempted to send on unauthorized channel: ${channel}`);
      }
    },
    
    /**
     * on() - Listen for messages from the Main process
     * 
     * WHAT DOES IT DO?
     * Allows the Renderer to receive IPC messages from Main process.
     * 
     * USAGE IN RENDERER:
     *   window.electron.on(IPC_CHANNELS.PROGRESS_UPDATE, (progress) => {
     *     console.log('Progress:', progress);
     *     setProgress(progress);
     *   });
     * 
     * SECURITY:
     * We validate the channel is in our allowed list.
     * We strip the 'event' object (only pass the data).
     * 
     * WHY STRIP THE EVENT OBJECT?
     * The event object has methods like event.sender.send() which could
     * be used to send messages directly, bypassing our validation.
     * 
     * @param channel - The IPC channel name (must be in IPC_CHANNELS)
     * @param func - Callback function to run when message received
     */
    on: (channel: string, func: (...args: any[]) => void) => {
      /*
       * CHANNEL VALIDATION
       * 
       * ALLOWED CHANNELS (from IPC_CHANNELS):
       *   - PROGRESS_UPDATE
       *   - AUTOMATION_COMPLETE
       *   - AUTOMATION_ERROR
       *   - CONFIG_LOADED
       */
      const validChannels = [
        IPC_CHANNELS.PROGRESS_UPDATE,
        IPC_CHANNELS.AUTOMATION_COMPLETE,
        IPC_CHANNELS.AUTOMATION_ERROR,
        IPC_CHANNELS.CONFIG_LOADED,
        'jira:ready',  // Special channel for Jira window ready
      ];
      
      if (validChannels.includes(channel)) {
        // Channel is allowed, set up the listener
        
        // Remove existing listeners first (prevent duplicates)
        ipcRenderer.removeAllListeners(channel);
        
        // Add the new listener
        // Note: We pass (event, ...args) but only call func(...args)
        // This strips the event object for security
        ipcRenderer.on(channel, (event, ...args) => {
          func(...args);
        });
      } else {
        // Channel is not allowed, log a warning
        console.warn(`Attempted to listen on unauthorized channel: ${channel}`);
      }
    },
    
    /**
     * once() - Listen for ONE message from Main process, then stop listening
     * 
     * WHAT DOES IT DO?
     * Like on(), but automatically removes the listener after first message.
     * 
     * USAGE IN RENDERER:
     *   window.electron.once(IPC_CHANNELS.CONFIG_LOADED, (config) => {
     *     console.log('Config loaded once:', config);
     *     // This won't fire again, even if CONFIG_LOADED is sent multiple times
     *   });
     * 
     * WHEN TO USE:
     * - One-time events (e.g., initial config load)
     * - Request/response patterns
     * 
     * @param channel - The IPC channel name
     * @param func - Callback function (runs only once)
     */
    once: (channel: string, func: (...args: any[]) => void) => {
      const validChannels = [
        IPC_CHANNELS.PROGRESS_UPDATE,
        IPC_CHANNELS.AUTOMATION_COMPLETE,
        IPC_CHANNELS.AUTOMATION_ERROR,
        IPC_CHANNELS.CONFIG_LOADED,
        'jira:ready',
      ];
      
      if (validChannels.includes(channel)) {
        // Set up one-time listener
        ipcRenderer.once(channel, (event, ...args) => {
          func(...args);
        });
      } else {
        console.warn(`Attempted to listen once on unauthorized channel: ${channel}`);
      }
    },
    
    /**
     * removeListener() - Stop listening to a channel
     * 
     * WHAT DOES IT DO?
     * Removes event listeners to prevent memory leaks.
     * 
     * USAGE IN RENDERER:
     *   // Set up listener
     *   const handler = (progress) => { ... };
     *   window.electron.on(IPC_CHANNELS.PROGRESS_UPDATE, handler);
     * 
     *   // Later, clean up
     *   window.electron.removeListener(IPC_CHANNELS.PROGRESS_UPDATE, handler);
     * 
     * WHEN TO USE:
     * - Component unmounting (React useEffect cleanup)
     * - Switching views
     * - Preventing memory leaks
     * 
     * @param channel - The IPC channel name
     * @param func - The specific function to remove (optional - if not provided, removes all)
     */
    removeListener: (channel: string, func?: (...args: any[]) => void) => {
      const validChannels = [
        IPC_CHANNELS.PROGRESS_UPDATE,
        IPC_CHANNELS.AUTOMATION_COMPLETE,
        IPC_CHANNELS.AUTOMATION_ERROR,
        IPC_CHANNELS.CONFIG_LOADED,
        'jira:ready',
      ];
      
      if (validChannels.includes(channel)) {
        if (func) {
          // Remove specific listener
          ipcRenderer.removeListener(channel, func);
        } else {
          // Remove all listeners on this channel
          ipcRenderer.removeAllListeners(channel);
        }
      } else {
        console.warn(`Attempted to remove listener on unauthorized channel: ${channel}`);
      }
    },
  }
);

/*
 * ============================================================================
 * TYPE DEFINITIONS FOR RENDERER
 * ============================================================================
 * 
 * TypeScript needs to know about window.electron.
 * 
 * Create a file: src/renderer/types/electron.d.ts
 * 
 * Content:
 * 
 * export interface IElectronAPI {
 *   send: (channel: string, data?: any) => void;
 *   on: (channel: string, func: (...args: any[]) => void) => void;
 *   once: (channel: string, func: (...args: any[]) => void) => void;
 *   removeListener: (channel: string, func?: (...args: any[]) => void) => void;
 * }
 * 
 * declare global {
 *   interface Window {
 *     electron: IElectronAPI;
 *   }
 * }
 */

/*
 * ============================================================================
 * DEVELOPER NOTES
 * ============================================================================
 * 
 * COMMON MISTAKE: Exposing too much
 * 
 * ❌ BAD (dangerous):
 *    contextBridge.exposeInMainWorld('electron', {
 *      ipcRenderer: ipcRenderer,  // Exposes EVERYTHING!
 *      fs: require('fs'),         // Direct file system access!
 *      shell: require('electron').shell  // Can run any command!
 *    });
 * 
 * ✅ GOOD (safe):
 *    contextBridge.exposeInMainWorld('electron', {
 *      send: (channel, data) => {
 *        // Validate channel first
 *        if (validChannels.includes(channel)) {
 *          ipcRenderer.send(channel, data);
 *        }
 *      }
 *    });
 * 
 * 
 * SECURITY CHECKLIST:
 * 
 * ✅ Are all channels validated against a whitelist?
 * ✅ Is the event object stripped (not passed to callbacks)?
 * ✅ Are dangerous APIs (fs, child_process) NOT exposed?
 * ✅ Can the Renderer only do what it NEEDS to do?
 * 
 * 
 * DEBUGGING TIP:
 * 
 * If you see "window.electron is undefined":
 * 1. Check this file is being loaded (add console.log at top)
 * 2. Check main.ts has: webPreferences: { preload: path.join(__dirname, 'preload.js') }
 * 3. Rebuild: npm run build
 * 4. Restart the app
 * 
 * 
 * ADDING NEW CHANNELS:
 * 
 * 1. Add to IPC_CHANNELS in ipc-channels.ts
 * 2. Add to validChannels arrays in this file
 * 3. Implement handler in main.ts
 * 4. Use in Renderer components
 */

console.log('Preload script loaded successfully');
