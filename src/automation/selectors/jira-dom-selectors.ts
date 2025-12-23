/*
 * ============================================================================
 * JIRA DOM SELECTORS - CSS Selectors for Finding Jira Elements
 * ============================================================================
 * 
 * WHAT IS THIS FILE FOR?
 * ----------------------
 * Jira's HTML structure can change over time (when Atlassian updates Jira).
 * Instead of scattering selectors throughout our code, we centralize them here.
 * 
 * Think of this like a "phone book" for Jira elements:
 *   - Need to find the Edit button? Look here.
 *   - Need to find the Due Date field? Look here.
 *   - Jira changed their HTML? Update only this file.
 * 
 * 
 * WHY MULTIPLE SELECTORS PER ELEMENT?
 * -----------------------------------
 * Jira has changed over time and varies between:
 *   - Cloud vs Server
 *   - Different versions
 *   - Different views (issue list vs issue detail)
 * 
 * We provide FALLBACK selectors - try the first one, if it doesn't exist,
 * try the second, then third, etc.
 * 
 * This makes our automation resilient to Jira updates.
 * 
 * 
 * HOW TO USE:
 * -----------
 * Instead of:
 *   ❌ document.querySelector('.ghx-issue-key')  // What if this changes?
 * 
 * Use:
 *   ✅ findElement(JIRA_SELECTORS.ISSUE_LIST.ISSUE_KEY)
 *   ✅ This tries all fallback selectors automatically
 */

/**
 * JIRA_SELECTORS - Complete map of all Jira UI elements we need to find
 * 
 * STRUCTURE:
 * {
 *   SECTION_NAME: {
 *     ELEMENT_NAME: ['primary-selector', 'fallback1', 'fallback2']
 *   }
 * }
 */
export const JIRA_SELECTORS = {
  
  // ==========================================================================
  // ISSUE LIST - Elements in the issue search results / JQL results page
  // ==========================================================================
  ISSUE_LIST: {
    /**
     * Issue Key (e.g., "ABC-123")
     * 
     * WHERE: Issue search results, Structure boards
     * WHAT: The clickable issue key/ID
     * 
     * SELECTORS EXPLAINED:
     * - 'a.issue-link' = Modern Jira Cloud link
     * - '[data-issue-key]' = Issues with data attribute
     * - '.ghx-issue-key' = Older Jira agile boards
     * - '.issuekey' = Classic Jira issue navigator
     */
    ISSUE_KEY: [
      'a.issue-link',
      '[data-issue-key]',
      '.ghx-issue-key',
      '.issuekey',
      'a[href*="/browse/"]'  // Any link to browse page
    ],
    
    /**
     * Issue Row
     * 
     * WHERE: Issue search results table
     * WHAT: The entire row containing issue data
     */
    ISSUE_ROW: [
      'tr[data-issue-key]',
      'li[data-issue-key]',
      '.issue-row',
      '.ghx-issue'
    ],
    
    /**
     * Summary Text
     * 
     * WHERE: Issue list
     * WHAT: The issue title/summary text
     */
    SUMMARY: [
      '.summary',
      '.ghx-summary',
      '[data-field-id="summary"]',
      'td.singleline'
    ]
  },
  
  // ==========================================================================
  // ISSUE DETAIL - Elements on the individual issue page
  // ==========================================================================
  ISSUE_DETAIL: {
    /**
     * Edit Button
     * 
     * WHERE: Top of issue detail page
     * WHAT: Button that opens the edit dialog
     * 
     * WHY MULTIPLE:
     * - Some Jira instances use <button>
     * - Some use <a> tag
     * - Different aria-labels across versions
     */
    EDIT_BUTTON: [
      '#edit-issue',
      'button#edit-issue',
      'a#edit-issue',
      '[aria-label="Edit"]',
      'button[title="Edit"]',
      '#opsbar-operations_more a:contains("Edit")'  // In dropdown menu
    ],
    
    /**
     * Comment Button
     * 
     * WHERE: Issue detail page
     * WHAT: Button to add a comment
     */
    COMMENT_BUTTON: [
      '#comment-issue',
      'button#comment-issue',
      '[aria-label="Comment"]',
      '#footer-comment-button'
    ],
    
    /**
     * Transition Buttons (Status changes)
     * 
     * WHERE: Issue detail page
     * WHAT: Buttons like "To Do", "In Progress", "Done"
     */
    TRANSITION_BUTTON: [
      '#action_id_',  // Prefix for transition buttons
      '.aui-button.issueaction-workflow-transition',
      '[data-operation-id^="action_id_"]'
    ]
  },
  
  // ==========================================================================
  // EDIT DIALOG - Form fields when editing an issue
  // ==========================================================================
  EDIT_DIALOG: {
    /**
     * Edit Dialog Container
     * 
     * WHERE: Modal/popup that appears when clicking Edit
     * WHAT: The container holding all edit fields
     */
    DIALOG: [
      '#edit-issue-dialog',
      '.aui-dialog.edit-issue-dialog',
      '[role="dialog"][aria-label*="Edit"]'
    ],
    
    /**
     * Due Date Field
     * 
     * WHERE: Edit dialog
     * WHAT: Input field for due date
     * 
     * HOW IT WORKS:
     * Jira uses date pickers - we need to find the input field
     */
    DUE_DATE: [
      '#duedate',
      'input[name="duedate"]',
      '[data-field-id="duedate"]',
      '#duedate-field'
    ],
    
    /**
     * Fix Version Field
     * 
     * WHERE: Edit dialog
     * WHAT: Dropdown/select for fix version
     */
    FIX_VERSION: [
      '#fixVersions',
      'select[name="fixVersions"]',
      '[data-field-id="fixVersions"]',
      '#fixVersions-field'
    ],
    
    /**
     * Summary Field
     * 
     * WHERE: Edit dialog
     * WHAT: Text input for issue summary/title
     */
    SUMMARY_FIELD: [
      '#summary',
      'input[name="summary"]',
      '[data-field-id="summary"]'
    ],
    
    /**
     * Description Field
     * 
     * WHERE: Edit dialog
     * WHAT: Rich text editor for description
     */
    DESCRIPTION: [
      '#description',
      'textarea[name="description"]',
      '[data-field-id="description"]',
      '#description-wiki-edit'
    ],
    
    /**
     * Custom Fields
     * 
     * WHERE: Edit dialog
     * WHAT: Any custom field (format varies)
     * 
     * NOTE: Custom fields have IDs like "customfield_10001"
     * Use this as a pattern to find any custom field
     */
    CUSTOM_FIELD_PREFIX: 'customfield_',
    
    /**
     * Submit/Save Button
     * 
     * WHERE: Edit dialog
     * WHAT: Button to save changes
     */
    SUBMIT_BUTTON: [
      '#edit-issue-submit',
      'button[type="submit"]',
      'input[value="Update"]',
      '.save-form-button'
    ],
    
    /**
     * Cancel Button
     * 
     * WHERE: Edit dialog
     * WHAT: Button to close without saving
     */
    CANCEL_BUTTON: [
      '#edit-issue-cancel',
      '.cancel',
      'button:contains("Cancel")'
    ]
  },
  
  // ==========================================================================
  // VERSION/RELEASE - Fix Version detail elements
  // ==========================================================================
  VERSION: {
    /**
     * Version Link
     * 
     * WHERE: Issue detail, edit dialog
     * WHAT: Clickable version name
     */
    VERSION_LINK: [
      'a[href*="/projects/"][href*="/versions/"]',
      '.fixfor-val a',
      '[data-field-id="fixVersions"] a'
    ],
    
    /**
     * Release Date
     * 
     * WHERE: Version tooltip, version detail page
     * WHAT: The scheduled release date for the version
     * 
     * HOW TO GET IT:
     * - Hover over version name → tooltip appears
     * - Or navigate to version detail page
     */
    RELEASE_DATE: [
      '[data-field="releaseDate"]',
      '.version-release-date',
      'time[datetime]',  // Jira uses <time> tags
      '.release-date'
    ],
    
    /**
     * Version Tooltip
     * 
     * WHERE: Appears on hover over version name
     * WHAT: Popup showing version details
     */
    VERSION_TOOLTIP: [
      '.version-tooltip',
      '[role="tooltip"]',
      '.aui-inline-dialog-contents'
    ]
  },
  
  // ==========================================================================
  // COMMENTS - Comment section elements
  // ==========================================================================
  COMMENTS: {
    /**
     * Comment Input
     * 
     * WHERE: Bottom of issue page
     * WHAT: Text area for adding comments
     */
    COMMENT_INPUT: [
      '#comment',
      'textarea[name="comment"]',
      '[data-field-id="comment"]'
    ],
    
    /**
     * Add Comment Button
     * 
     * WHERE: Comment section
     * WHAT: Button to submit comment
     */
    ADD_COMMENT_BUTTON: [
      '#issue-comment-add-submit',
      'button[type="submit"].comment-button',
      '#comment-add-submit'
    ],
    
    /**
     * Comment List
     * 
     * WHERE: Issue detail page
     * WHAT: Container of all comments
     */
    COMMENT_LIST: [
      '#issue_actions_container',
      '.action-body',
      '#activitymodule'
    ]
  },
  
  // ==========================================================================
  // NAVIGATION - Page navigation elements
  // ==========================================================================
  NAVIGATION: {
    /**
     * Search Box
     * 
     * WHERE: Top navigation bar
     * WHAT: Quick search / issue navigator
     */
    SEARCH_BOX: [
      '#quickSearchInput',
      'input[name="searchers"]',
      '#search-query'
    ],
    
    /**
     * Issue Navigator Link
     * 
     * WHERE: Top navigation
     * WHAT: Link to issue search/filter
     */
    ISSUE_NAVIGATOR: [
      'a[href*="/issues/"]',
      '#find_link',
      'a:contains("Issues")'
    ],
    
    /**
     * Loading Indicator
     * 
     * WHERE: Anywhere on page
     * WHAT: Spinner/loading animation
     * 
     * WHY WE NEED THIS:
     * Wait for this to disappear before interacting with page
     */
    LOADING_INDICATOR: [
      '.loading',
      '.spinner',
      '.aui-spinner',
      '[data-testid="loading"]'
    ]
  },
  
  // ==========================================================================
  // STRUCTURE - Tempo Structure plugin elements
  // ==========================================================================
  STRUCTURE: {
    /**
     * Structure Grid
     * 
     * WHERE: Structure board page
     * WHAT: The main grid/table of issues
     */
    GRID: [
      '.structure-grid',
      '[data-structure-id]',
      '.structure-table'
    ],
    
    /**
     * Structure Issue Row
     * 
     * WHERE: Structure grid
     * WHAT: Row containing issue data
     */
    ISSUE_ROW: [
      '[data-issue-key]',
      '.structure-issue-row',
      'tr[data-row-type="issue"]'
    ]
  },
  
  // ==========================================================================
  // ERROR DETECTION - Elements that indicate errors or problems
  // ==========================================================================
  ERROR: {
    /**
     * Error Message
     * 
     * WHERE: Anywhere on page
     * WHAT: Error notification
     */
    ERROR_MESSAGE: [
      '.error',
      '.aui-message.error',
      '[role="alert"]',
      '.error-message'
    ],
    
    /**
     * Login Page Indicator
     * 
     * WHERE: Login page
     * WHAT: Element that only exists on login page
     * 
     * WHY:
     * If we detect this, session expired - need to prompt user
     */
    LOGIN_FORM: [
      '#login-form',
      'form[name="loginform"]',
      'input[name="os_username"]',  // Username field
      '#login'
    ],
    
    /**
     * Permission Error
     * 
     * WHERE: Issue page
     * WHAT: "You don't have permission" message
     */
    PERMISSION_ERROR: [
      '.error-message:contains("permission")',
      '[data-error="permission"]',
      '.no-permission'
    ]
  }
  
} as const;  // 'as const' makes this read-only


/*
 * ============================================================================
 * UTILITY FUNCTIONS FOR USING SELECTORS
 * ============================================================================
 */

/**
 * Try multiple selectors until one works
 * 
 * WHAT DOES THIS DO?
 * Takes an array of CSS selectors and tries each one until it finds an element.
 * 
 * WHY?
 * Jira's HTML structure varies. This provides resilience.
 * 
 * EXAMPLE:
 *   const editButton = trySelectors(JIRA_SELECTORS.ISSUE_DETAIL.EDIT_BUTTON);
 *   if (editButton) {
 *     editButton.click();
 *   }
 * 
 * @param selectors - Array of CSS selector strings
 * @returns The first matching element, or null if none found
 */
export function trySelectors(selectors: readonly string[]): HTMLElement | null {
  for (const selector of selectors) {
    try {
      // Try to find element with this selector
      const element = document.querySelector(selector) as HTMLElement;
      
      if (element) {
        // Found it! Return immediately
        console.log(`✓ Found element using selector: ${selector}`);
        return element;
      }
    } catch (error) {
      // Invalid selector or other error - continue to next
      console.warn(`✗ Selector failed: ${selector}`, error);
    }
  }
  
  // None of the selectors worked
  console.error('✗ Could not find element with any of the selectors:', selectors);
  return null;
}

/**
 * Wait for element to appear (with timeout)
 * 
 * WHAT DOES THIS DO?
 * Keeps checking for an element to appear on the page.
 * 
 * WHY?
 * Jira loads content dynamically (AJAX).
 * We need to wait for elements to appear before interacting.
 * 
 * EXAMPLE:
 *   await waitForElement(JIRA_SELECTORS.EDIT_DIALOG.DIALOG, 5000);
 *   // Now dialog is visible, we can interact with it
 * 
 * @param selectors - Array of CSS selectors to try
 * @param timeoutMs - How long to wait before giving up (default: 10 seconds)
 * @param checkIntervalMs - How often to check (default: 100ms)
 * @returns Promise that resolves to element or null if timeout
 */
export async function waitForElement(
  selectors: readonly string[],
  timeoutMs: number = 10000,
  checkIntervalMs: number = 100
): Promise<HTMLElement | null> {
  
  const startTime = Date.now();
  
  // Keep checking until we find it or timeout
  while (Date.now() - startTime < timeoutMs) {
    // Try to find the element
    const element = trySelectors(selectors);
    
    if (element) {
      // Found it!
      return element;
    }
    
    // Not found yet, wait a bit before trying again
    await sleep(checkIntervalMs);
  }
  
  // Timeout - element never appeared
  console.error(`⏱️ Timeout waiting for element (${timeoutMs}ms):`, selectors);
  return null;
}

/**
 * Sleep utility (for waiting)
 * 
 * WHAT DOES THIS DO?
 * Pauses execution for a specified time.
 * 
 * WHY?
 * JavaScript doesn't have a built-in sleep function.
 * We need to wait between actions to look human.
 * 
 * EXAMPLE:
 *   await sleep(1000);  // Wait 1 second
 * 
 * @param ms - Milliseconds to sleep
 */
function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}


/*
 * ============================================================================
 * DEVELOPER NOTES - HOW TO MAINTAIN THIS FILE
 * ============================================================================
 * 
 * WHEN JIRA CHANGES:
 * 
 * 1. Automation starts failing
 * 2. Check console logs - which selector failed?
 * 3. Open Jira in browser DevTools (F12)
 * 4. Inspect the element that changed
 * 5. Find the new selector (ID, class, data attribute)
 * 6. Add it to the BEGINNING of the selectors array (becomes primary)
 * 7. Keep old selectors as fallbacks
 * 
 * 
 * EXAMPLE:
 * 
 * Jira changed the Edit button from #edit-issue to #edit-issue-btn
 * 
 * Before:
 *   EDIT_BUTTON: ['#edit-issue', 'button#edit-issue']
 * 
 * After:
 *   EDIT_BUTTON: ['#edit-issue-btn', '#edit-issue', 'button#edit-issue']
 *                 ↑ New primary     ↑ Old selectors kept as fallbacks
 * 
 * 
 * TESTING NEW SELECTORS:
 * 
 * 1. Open Jira in browser
 * 2. Open DevTools console (F12)
 * 3. Type: document.querySelector('#your-selector')
 * 4. If it returns the element, it works!
 * 5. If it returns null, selector is wrong
 * 
 * 
 * SELECTOR BEST PRACTICES:
 * 
 * ✅ Prefer: IDs (#edit-issue)
 * ✅ Good: Data attributes ([data-issue-key])
 * ✅ Okay: Specific classes (.edit-issue-button)
 * ❌ Avoid: Generic classes (.button)
 * ❌ Avoid: Complex chains (.parent .child .grandchild)
 * 
 * 
 * WHY MULTIPLE SELECTORS?
 * 
 * Jira has:
 * - Multiple versions (Cloud, Server, Data Center)
 * - Regular updates (HTML changes frequently)
 * - Different views (classic vs new UI)
 * 
 * Multiple selectors = More resilient automation
 */
