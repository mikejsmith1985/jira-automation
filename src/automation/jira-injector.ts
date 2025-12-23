/*
 * ============================================================================
 * JIRA INJECTOR - Main Automation Orchestrator
 * ============================================================================
 * 
 * WHAT IS THIS FILE FOR?
 * ----------------------
 * This is the "conductor" of the automation orchestra.
 * 
 * Think of it like a chef following a recipe:
 *   1. Read the recipe (get task config)
 *   2. Gather ingredients (extract issues)
 *   3. Follow steps (process each issue)
 *   4. Plate the dish (report results)
 * 
 * This file:
 *   - Receives automation tasks from the main process
 *   - Extracts issues from Jira pages
 *   - Processes each issue (update fields)
 *   - Reports progress back to the UI
 *   - Handles errors gracefully
 * 
 * 
 * WHERE DOES THIS RUN?
 * --------------------
 * This script is INJECTED into the Jira webpage.
 * It runs in the Jira window's JavaScript context.
 * It can access the Jira DOM and manipulate it.
 * 
 * 
 * HOW IT COMMUNICATES:
 * --------------------
 * Main Process ←→ This Script ←→ Jira DOM
 *   
 * This script uses ipcRenderer to send messages:
 *   - Progress updates
 *   - Completion status
 *   - Errors
 */

// Import our automation modules
import { extractIssuesFromPage, IssueData } from './modules/issue-reader';
import { updateDueDate, FieldUpdateResult } from './modules/field-updater';
import { subtractWorkingDays, formatDateForJira, parseDateFromJira, DEFAULT_US_HOLIDAYS } from './modules/date-calculator';
import { ThrottleManager, createThrottleFromConfig } from './utils/throttle-manager';

// Import shared interfaces
import { IProgressUpdate, UpdateStatus, IIssueProgress } from '../shared/interfaces/IProgressUpdate';
import { TaskType, IAutomationTask, IDueDateTaskConfig } from '../shared/interfaces/IAutomationTask';
import { IAppConfig } from '../shared/interfaces/IAppConfig';
import { IPC_CHANNELS } from '../shared/ipc-channels';

/*
 * NOTE: This code runs in the Jira page context, so we have access to:
 * - window.electron (exposed by preload.ts)
 * - document (Jira's DOM)
 * - All browser APIs
 */

/**
 * AutomationState - Current state of automation
 * 
 * WHAT IS THIS?
 * Tracks what the automation is doing right now.
 */
interface AutomationState {
  /**
   * Is automation currently running?
   */
  isRunning: boolean;
  
  /**
   * Current task being executed
   */
  currentTask?: IAutomationTask;
  
  /**
   * Issues to process
   */
  issues: IssueData[];
  
  /**
   * Progress tracking
   */
  progress: IProgressUpdate;
  
  /**
   * Throttle manager for delays
   */
  throttle: ThrottleManager;
}

// Global state
let automationState: AutomationState | null = null;


/**
 * Initialize automation system
 * 
 * WHAT DOES THIS DO?
 * Sets up listeners for automation commands from main process.
 * 
 * WHEN IS THIS CALLED?
 * When this script is injected into the Jira page.
 */
export function initializeAutomation(): void {
  console.log('🤖 Jira Automation System initializing...');
  
  // Listen for automation start command
  if (window.electron) {
    window.electron.on('automation:start-command', handleAutomationStart);
    window.electron.on('automation:stop-command', handleAutomationStop);
    
    console.log('✓ Automation system ready');
  } else {
    console.error('✗ window.electron not available - automation cannot start');
  }
}


/**
 * Handle automation start command
 * 
 * WHAT DOES THIS DO?
 * Receives command from main process to start automation.
 * 
 * @param data - Contains task and config
 */
async function handleAutomationStart(data: { task: IAutomationTask, config: IAppConfig }): Promise<void> {
  console.log('▶️ Starting automation...', data.task);
  
  // Check if already running
  if (automationState?.isRunning) {
    console.warn('⚠️ Automation already running, ignoring start command');
    return;
  }
  
  try {
    // Create throttle manager from config
    const throttle = createThrottleFromConfig(data.config);
    
    // Initialize state
    automationState = {
      isRunning: true,
      currentTask: data.task,
      issues: [],
      progress: {
        taskId: data.task.id,
        totalIssues: 0,
        processedIssues: 0,
        issues: []
      },
      throttle
    };
    
    // Run the automation based on task type
    await runAutomation(data.task, data.config);
    
    // Send completion message
    sendAutomationComplete();
    
  } catch (error) {
    console.error('✗ Automation failed:', error);
    sendAutomationError(String(error));
  } finally {
    // Cleanup
    if (automationState) {
      automationState.isRunning = false;
    }
  }
}


/**
 * Handle automation stop command
 * 
 * WHAT DOES THIS DO?
 * Gracefully stops automation when user clicks "Stop".
 */
function handleAutomationStop(data: { taskId: string }): void {
  console.log('⏹️ Stop command received');
  
  if (automationState && automationState.isRunning) {
    automationState.isRunning = false;
    console.log('✓ Automation will stop after current issue');
  }
}


/**
 * Run automation based on task type
 * 
 * WHAT DOES THIS DO?
 * Routes to the appropriate automation function based on task type.
 * 
 * @param task - Automation task to run
 * @param config - App configuration
 */
async function runAutomation(task: IAutomationTask, config: IAppConfig): Promise<void> {
  console.log(`🎯 Running ${task.type} automation...`);
  
  switch (task.type) {
    case TaskType.UPDATE_DUE_DATE:
      await runDueDateAutomation(task, config);
      break;
      
    case TaskType.LINK_PR:
      // TODO: Implement PR linking
      throw new Error('PR linking not yet implemented');
      
    case TaskType.INJECT_PR_COMMENTS:
      // TODO: Implement comment injection
      throw new Error('PR comment injection not yet implemented');
      
    default:
      throw new Error(`Unknown task type: ${task.type}`);
  }
}


/**
 * Run due date automation
 * 
 * WHAT DOES THIS DO?
 * Sets due dates based on fix version release dates.
 * 
 * PROCESS:
 * 1. Extract issues from current page
 * 2. For each issue with a fix version:
 *    a. Get fix version release date
 *    b. Subtract N working days
 *    c. Set as due date
 * 3. Report progress
 * 
 * @param task - Automation task
 * @param config - App configuration
 */
async function runDueDateAutomation(task: IAutomationTask, config: IAppConfig): Promise<void> {
  if (!automationState) return;
  
  const taskConfig = task.config as IDueDateTaskConfig;
  const throttle = automationState.throttle;
  
  // Step 1: Extract issues from page
  console.log('📋 Extracting issues from page...');
  await throttle.waitInitial();
  
  const issues = await extractIssuesFromPage();
  
  if (issues.length === 0) {
    throw new Error('No issues found on this page');
  }
  
  console.log(`✓ Found ${issues.length} issues`);
  
  // Update state
  automationState.issues = issues;
  automationState.progress.totalIssues = issues.length;
  
  // Send initial progress
  sendProgressUpdate();
  
  // Step 2: Process each issue
  for (let i = 0; i < issues.length; i++) {
    // Check if we should stop
    if (!automationState.isRunning) {
      console.log('⏹️ Automation stopped by user');
      break;
    }
    
    const issue = issues[i];
    console.log(`\n[${i + 1}/${issues.length}] Processing ${issue.key}...`);
    
    // Update current issue
    automationState.progress.currentIssue = {
      issueKey: issue.key,
      summary: issue.summary,
      status: UpdateStatus.IN_PROGRESS,
      timestamp: new Date()
    };
    
    sendProgressUpdate();
    
    // Process the issue
    const result = await processIssueDueDate(issue, taskConfig, throttle);
    
    // Update progress with result
    automationState.progress.processedIssues++;
    automationState.progress.currentIssue = {
      issueKey: issue.key,
      summary: issue.summary,
      status: result.success ? UpdateStatus.SUCCESS : UpdateStatus.FAILED,
      timestamp: new Date(),
      details: result.success 
        ? `Due date set to ${result.newValue}`
        : result.error
    };
    
    automationState.progress.issues.push(automationState.progress.currentIssue);
    
    sendProgressUpdate();
    
    // Wait between issues
    await throttle.wait();
  }
  
  console.log('\n✅ Automation complete!');
}


/**
 * Process one issue for due date update
 * 
 * WHAT DOES THIS DO?
 * Calculates and sets the due date for a single issue.
 * 
 * @param issue - Issue data
 * @param config - Task configuration
 * @param throttle - Throttle manager
 * @returns Update result
 */
async function processIssueDueDate(
  issue: IssueData,
  config: IDueDateTaskConfig,
  throttle: ThrottleManager
): Promise<FieldUpdateResult> {
  
  try {
    // Check if issue has fix version
    if (!issue.fixVersion) {
      console.log(`⏭️ ${issue.key}: No fix version, skipping`);
      return {
        success: false,
        issueKey: issue.key,
        fieldName: 'duedate',
        newValue: '',
        error: 'No fix version set'
      };
    }
    
    // Get fix version release date
    // TODO: In full implementation, we'd fetch this from Jira
    // For now, we'll use a placeholder
    console.log(`📅 ${issue.key}: Fix version = ${issue.fixVersion}`);
    
    // Example: Parse release date from fix version
    // In reality, we'd need to navigate to version details or parse tooltip
    // For now, we'll use a hardcoded example date
    const releaseDateString = '2025-01-31';  // TODO: Get from Jira
    const releaseDate = parseDateFromJira(releaseDateString);
    
    if (!releaseDate) {
      throw new Error('Could not parse release date');
    }
    
    // Calculate due date (N working days before release)
    const daysBeforeRelease = config.daysBeforeFixVersion;
    const holidays = config.holidays || DEFAULT_US_HOLIDAYS;
    
    const dueDate = subtractWorkingDays(releaseDate, daysBeforeRelease, holidays);
    const dueDateString = formatDateForJira(dueDate);
    
    console.log(`🎯 ${issue.key}: Calculated due date = ${dueDateString}`);
    
    // Update the due date field
    const result = await updateDueDate(issue.key, dueDateString, throttle);
    
    return result;
    
  } catch (error) {
    console.error(`✗ ${issue.key}: Error - ${error}`);
    
    return {
      success: false,
      issueKey: issue.key,
      fieldName: 'duedate',
      newValue: '',
      error: String(error)
    };
  }
}


/**
 * Send progress update to main process
 * 
 * WHAT DOES THIS DO?
 * Sends current progress to the UI via IPC.
 */
function sendProgressUpdate(): void {
  if (!automationState || !window.electron) return;
  
  window.electron.send(IPC_CHANNELS.PROGRESS_UPDATE, automationState.progress);
}


/**
 * Send automation complete message
 */
function sendAutomationComplete(): void {
  if (!automationState || !window.electron) return;
  
  const summary = {
    total: automationState.progress.totalIssues,
    success: automationState.progress.issues.filter(i => i.status === UpdateStatus.SUCCESS).length,
    failed: automationState.progress.issues.filter(i => i.status === UpdateStatus.FAILED).length,
    skipped: automationState.progress.issues.filter(i => i.status === UpdateStatus.SKIPPED).length
  };
  
  console.log('📊 Final Summary:', summary);
  
  window.electron.send(IPC_CHANNELS.AUTOMATION_COMPLETE, {
    taskId: automationState.currentTask?.id,
    summary
  });
}


/**
 * Send automation error message
 */
function sendAutomationError(error: string): void {
  if (!automationState || !window.electron) return;
  
  window.electron.send(IPC_CHANNELS.AUTOMATION_ERROR, {
    taskId: automationState.currentTask?.id,
    error
  });
}


// Initialize when script loads
if (typeof window !== 'undefined') {
  // Wait for page to be ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAutomation);
  } else {
    initializeAutomation();
  }
}


/*
 * ============================================================================
 * DEVELOPER NOTES
 * ============================================================================
 * 
 * HOW THIS SCRIPT GETS INJECTED:
 * 
 * 1. Main process creates Jira window
 * 2. Jira page loads
 * 3. Preload script runs (before page scripts)
 * 4. This script is injected via:
 *    - Script tag in HTML
 *    - Or executeJavaScript() from main process
 * 5. initializeAutomation() runs
 * 6. System is ready for commands
 * 
 * 
 * ERROR RECOVERY:
 * 
 * If automation fails midway:
 * - State is preserved
 * - User can see which issues succeeded/failed
 * - Can manually fix failed issues
 * - Can restart automation from where it stopped
 * 
 * 
 * STOPPING GRACEFULLY:
 * 
 * When user clicks "Stop":
 * 1. automationState.isRunning = false
 * 2. Current issue finishes processing
 * 3. Loop checks isRunning, sees false, exits
 * 4. Sends completion with partial results
 * 
 * 
 * FUTURE ENHANCEMENTS:
 * 
 * - Pagination: Process multiple pages automatically
 * - Parallel processing: Update multiple issues simultaneously
 * - Smart retries: Retry only failed issues
 * - Resume capability: Continue from where you left off
 * - Dry run mode: Preview changes without saving
 * - Undo capability: Revert changes if needed
 */
