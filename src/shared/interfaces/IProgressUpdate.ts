/*
 * ============================================================================
 * PROGRESS UPDATE INTERFACE - Tracking Automation Progress
 * ============================================================================
 * 
 * WHAT IS THIS FILE FOR?
 * ---------------------
 * When automation is running, users want to see:
 *   - "How many issues are done?"
 *   - "What issue is being processed right now?"
 *   - "Did any issues fail?"
 * 
 * This file defines the data structure for progress updates.
 * 
 * 
 * ANALOGY:
 * --------
 * Imagine washing dishes:
 *   - Total dishes: 50
 *   - Clean dishes: 30
 *   - Current dish: "Large pot"
 *   - Status: "Scrubbing"
 * 
 * Similarly, our automation tracks:
 *   - Total issues: 50
 *   - Processed issues: 30
 *   - Current issue: "ABC-123"
 *   - Status: "Updating due date"
 */

/**
 * UpdateStatus - The Different States an Issue Can Be In
 * 
 * WHAT IS THIS?
 * -------------
 * As automation processes each issue, it goes through stages:
 * 
 *   QUEUED ──→ IN_PROGRESS ──→ SUCCESS
 *                           └──→ FAILED
 *                           └──→ SKIPPED
 * 
 * 
 * STATUS MEANINGS:
 * ----------------
 * QUEUED: Issue is waiting to be processed
 *   Example: 50 issues found, currently on issue #5, others are QUEUED
 * 
 * IN_PROGRESS: Automation is currently working on this issue
 *   Example: Clicking "Edit" button, filling in due date field
 * 
 * SUCCESS: Issue was updated successfully
 *   Example: Due date set to 2025-01-17, saved
 * 
 * FAILED: Something went wrong
 *   Example: Jira returned an error, network timeout, can't find field
 * 
 * SKIPPED: Issue was intentionally not processed
 *   Example: Issue has no FixVersion, so we can't calculate due date
 */
export enum UpdateStatus {
  QUEUED = "queued",
  IN_PROGRESS = "in_progress",
  SUCCESS = "success",
  FAILED = "failed",
  SKIPPED = "skipped"
}


/**
 * IIssueProgress - Progress Info for ONE Issue
 * 
 * WHAT IS THIS?
 * -------------
 * Each issue being processed gets one of these objects.
 * 
 * EXAMPLE:
 *   {
 *     issueKey: "ABC-123",
 *     summary: "Implement login page",
 *     status: UpdateStatus.SUCCESS,
 *     timestamp: "2025-01-15T10:30:00Z",
 *     details: "Due date set to 2025-01-17"
 *   }
 */
export interface IIssueProgress {
  /**
   * The Jira issue key
   * Example: "ABC-123" or "PROJ-456"
   * 
   * WHY: Unique identifier so we know which issue this is
   */
  issueKey: string;
  
  /**
   * The issue title/summary
   * Example: "Implement login page"
   * 
   * WHY: More meaningful to users than just "ABC-123"
   * Makes the log easier to read
   */
  summary: string;
  
  /**
   * Current processing status
   * Example: UpdateStatus.IN_PROGRESS
   * 
   * WHY: Users want to see if issues succeeded or failed
   */
  status: UpdateStatus;
  
  /**
   * When did this status change?
   * Example: new Date("2025-01-15T10:30:00Z")
   * 
   * WHY: Helps debug issues ("It failed at 10:30am - that's when the network went down!")
   * Also useful for audit logs
   */
  timestamp: Date;
  
  /**
   * Extra information (optional)
   * Example: "Due date set to 2025-01-17" (success)
   *          "Error: Field 'Due Date' not found" (failure)
   * 
   * WHY: Users need details about what happened
   * 
   * NOTE: Optional (marked with "?") - might be undefined
   */
  details?: string;
}


/**
 * IProgressUpdate - Overall Progress for the Entire Automation Task
 * 
 * WHAT IS THIS?
 * -------------
 * The "big picture" view of how automation is going.
 * 
 * EXAMPLE:
 *   {
 *     taskId: "task_1234567890",
 *     totalIssues: 50,
 *     processedIssues: 30,
 *     currentIssue: { issueKey: "ABC-123", status: IN_PROGRESS, ... },
 *     issues: [ ...history of all 30 processed issues... ]
 *   }
 * 
 * 
 * WHAT DOES THE UI DO WITH THIS?
 * -------------------------------
 * - Progress bar: 30/50 = 60% complete
 * - Current status: "Processing ABC-123..."
 * - Log window: Shows all issues array (scrollable list)
 */
export interface IProgressUpdate {
  /**
   * Which task is this progress for?
   * Example: "task_1234567890"
   * 
   * WHY: User might run multiple tasks at once
   * We need to know which task this progress belongs to
   */
  taskId: string;
  
  /**
   * How many issues total are we processing?
   * Example: 50
   * 
   * WHY: Needed to calculate progress percentage (30 / 50 = 60%)
   */
  totalIssues: number;
  
  /**
   * How many issues have we finished?
   * Example: 30
   * 
   * WHY: Shows progress - "We're 60% done"
   * 
   * NOTE: This includes SUCCESS, FAILED, and SKIPPED
   * Only QUEUED and IN_PROGRESS are not counted
   */
  processedIssues: number;
  
  /**
   * The issue being processed RIGHT NOW (optional)
   * Example: { issueKey: "ABC-123", status: IN_PROGRESS, ... }
   * 
   * WHY: Users want to see "What's it doing right now?"
   * 
   * NOTE: Optional because:
   *   - Might be undefined if automation just started
   *   - Might be undefined if automation is finished
   */
  currentIssue?: IIssueProgress;
  
  /**
   * History of ALL issues processed so far
   * Example: [
   *   { issueKey: "ABC-120", status: SUCCESS, ... },
   *   { issueKey: "ABC-121", status: FAILED, details: "Network error", ... },
   *   { issueKey: "ABC-122", status: SKIPPED, details: "No FixVersion", ... },
   *   ...
   * ]
   * 
   * WHY: Displayed in the log window
   * User can scroll through and see what happened to each issue
   * Useful for debugging: "Why did ABC-121 fail?"
   */
  issues: IIssueProgress[];
}


/*
 * ============================================================================
 * HOW PROGRESS UPDATES FLOW THROUGH THE APP
 * ============================================================================
 * 
 * 1. AUTOMATION SCRIPT (running in Jira page):
 * 
 *    - Starts processing ABC-123
 *    - Sends update: { currentIssue: { issueKey: "ABC-123", status: IN_PROGRESS } }
 * 
 * 2. MAIN PROCESS:
 * 
 *    - Receives the update
 *    - Updates internal state
 *    - Forwards to Renderer via IPC_CHANNELS.PROGRESS_UPDATE
 * 
 * 3. RENDERER (React UI):
 * 
 *    - Receives update
 *    - Updates progress bar: "30 / 50 (60%)"
 *    - Updates current status: "Processing ABC-123..."
 *    - Adds entry to log window: "ABC-123: In Progress"
 * 
 * 4. LATER, when ABC-123 finishes:
 * 
 *    - Automation sends: { 
 *        currentIssue: { issueKey: "ABC-123", status: SUCCESS },
 *        processedIssues: 31  // Incremented
 *      }
 * 
 * 5. RENDERER updates again:
 * 
 *    - Progress bar: "31 / 50 (62%)"
 *    - Log window: "ABC-123: ✓ Success - Due date set to 2025-01-17"
 * 
 * 
 * ============================================================================
 * EXAMPLE USAGE IN CODE
 * ============================================================================
 * 
 * SENDING AN UPDATE (from automation script):
 * 
 *   const update: IProgressUpdate = {
 *     taskId: "task_1234567890",
 *     totalIssues: 50,
 *     processedIssues: 30,
 *     currentIssue: {
 *       issueKey: "ABC-123",
 *       summary: "Implement login page",
 *       status: UpdateStatus.IN_PROGRESS,
 *       timestamp: new Date()
 *     },
 *     issues: [...previousIssues, currentIssue]
 *   };
 * 
 *   // Send to main process
 *   ipcRenderer.send(IPC_CHANNELS.PROGRESS_UPDATE, update);
 * 
 * 
 * RECEIVING AN UPDATE (in React component):
 * 
 *   window.electron.on(IPC_CHANNELS.PROGRESS_UPDATE, (update: IProgressUpdate) => {
 *     // Update UI state
 *     setProgress(update);
 *     
 *     // Calculate percentage
 *     const percent = (update.processedIssues / update.totalIssues) * 100;
 *     
 *     // Update progress bar
 *     setProgressPercent(percent);
 *     
 *     // Show current issue
 *     if (update.currentIssue) {
 *       setCurrentStatus(`Processing ${update.currentIssue.issueKey}...`);
 *     }
 *   });
 */
