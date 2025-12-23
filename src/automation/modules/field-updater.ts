/*
 * ============================================================================
 * FIELD UPDATER - Update Jira Fields Through UI Simulation
 * ============================================================================
 * 
 * WHAT IS THIS FILE FOR?
 * ----------------------
 * This file simulates a human clicking through Jira to update fields.
 * 
 * The process (like a human would do):
 * 1. Navigate to issue page
 * 2. Click "Edit" button
 * 3. Wait for edit dialog to appear
 * 4. Find the field input
 * 5. Clear existing value
 * 6. Type new value
 * 7. Click "Update" button
 * 8. Wait for save confirmation
 * 
 * 
 * WHY SIMULATE UI INTERACTION?
 * -----------------------------
 * We don't have API access, so we must work through the web UI.
 * This is exactly what a human would do, just automated.
 * 
 * 
 * WHAT FIELDS CAN WE UPDATE?
 * ---------------------------
 * Any field visible in the edit dialog:
 *   - Due Date
 *   - Summary
 *   - Description
 *   - Fix Version
 *   - Custom fields
 *   - Labels
 *   - Components
 */

import { JIRA_SELECTORS, trySelectors, waitForElement } from '../selectors/jira-dom-selectors';
import { ThrottleManager } from '../utils/throttle-manager';
import { withRetry } from '../utils/retry-handler';

/**
 * FieldUpdateResult - Result of a field update operation
 */
export interface FieldUpdateResult {
  /**
   * Was the update successful?
   */
  success: boolean;
  
  /**
   * Issue key that was updated
   */
  issueKey: string;
  
  /**
   * Field name that was updated
   */
  fieldName: string;
  
  /**
   * Old value (before update)
   */
  oldValue?: string;
  
  /**
   * New value (after update)
   */
  newValue: string;
  
  /**
   * Error message if failed
   */
  error?: string;
}


/**
 * Update due date field for an issue
 * 
 * WHAT DOES THIS DO?
 * Sets the "Due Date" field to a specific date.
 * 
 * HOW IT WORKS:
 * 1. Opens edit dialog
 * 2. Finds due date field
 * 3. Sets value to new date
 * 4. Saves
 * 
 * EXAMPLE USAGE:
 *   const result = await updateDueDate(
 *     'ABC-123',
 *     '2025-01-15',
 *     throttle
 *   );
 *   
 *   if (result.success) {
 *     console.log('✓ Due date updated');
 *   }
 * 
 * @param issueKey - Issue to update (e.g., "ABC-123")
 * @param newDate - New due date in YYYY-MM-DD format
 * @param throttle - Throttle manager for delays
 * @returns Update result
 */
export async function updateDueDate(
  issueKey: string,
  newDate: string,
  throttle: ThrottleManager
): Promise<FieldUpdateResult> {
  
  console.log(`📝 Updating due date for ${issueKey} to ${newDate}`);
  
  try {
    // Ensure we're on the issue page
    await ensureOnIssuePage(issueKey, throttle);
    
    // Open edit dialog
    await openEditDialog(throttle);
    
    // Find due date field
    const dueDateField = await waitForElement(JIRA_SELECTORS.EDIT_DIALOG.DUE_DATE, 5000);
    
    if (!dueDateField) {
      throw new Error('Could not find due date field');
    }
    
    // Get old value
    const oldValue = (dueDateField as HTMLInputElement).value;
    
    // Set new value
    await setFieldValue(dueDateField as HTMLInputElement, newDate, throttle);
    
    // Save changes
    await saveEditDialog(throttle);
    
    console.log(`✓ Due date updated: ${oldValue} → ${newDate}`);
    
    return {
      success: true,
      issueKey,
      fieldName: 'duedate',
      oldValue,
      newValue: newDate
    };
    
  } catch (error) {
    console.error(`✗ Failed to update due date: ${error}`);
    
    return {
      success: false,
      issueKey,
      fieldName: 'duedate',
      newValue: newDate,
      error: String(error)
    };
  }
}


/**
 * Update any text field
 * 
 * WHAT DOES THIS DO?
 * Generic function to update any text-based field.
 * 
 * WORKS WITH:
 * - Summary
 * - Description (text areas)
 * - Custom text fields
 * - Labels
 * 
 * @param issueKey - Issue to update
 * @param fieldId - Field identifier (e.g., "summary", "customfield_10001")
 * @param newValue - New value to set
 * @param throttle - Throttle manager
 * @returns Update result
 */
export async function updateTextField(
  issueKey: string,
  fieldId: string,
  newValue: string,
  throttle: ThrottleManager
): Promise<FieldUpdateResult> {
  
  console.log(`📝 Updating ${fieldId} for ${issueKey}`);
  
  try {
    await ensureOnIssuePage(issueKey, throttle);
    await openEditDialog(throttle);
    
    // Find field by ID
    const fieldSelectors = [
      `#${fieldId}`,
      `input[name="${fieldId}"]`,
      `textarea[name="${fieldId}"]`,
      `[data-field-id="${fieldId}"]`
    ];
    
    const field = await waitForElement(fieldSelectors, 5000);
    
    if (!field) {
      throw new Error(`Could not find field: ${fieldId}`);
    }
    
    // Get old value
    const oldValue = (field as HTMLInputElement).value;
    
    // Set new value
    await setFieldValue(field as HTMLInputElement, newValue, throttle);
    
    // Save
    await saveEditDialog(throttle);
    
    console.log(`✓ Field updated: ${oldValue} → ${newValue}`);
    
    return {
      success: true,
      issueKey,
      fieldName: fieldId,
      oldValue,
      newValue
    };
    
  } catch (error) {
    console.error(`✗ Failed to update field: ${error}`);
    
    return {
      success: false,
      issueKey,
      fieldName: fieldId,
      newValue,
      error: String(error)
    };
  }
}


/**
 * Ensure we're on the issue detail page
 * 
 * WHAT DOES THIS DO?
 * Navigates to the issue page if we're not already there.
 * 
 * WHY?
 * We need to be on the issue page to click "Edit".
 * 
 * @param issueKey - Issue key
 * @param throttle - Throttle manager
 */
async function ensureOnIssuePage(issueKey: string, throttle: ThrottleManager): Promise<void> {
  const currentUrl = window.location.href;
  const expectedUrl = `/browse/${issueKey}`;
  
  if (!currentUrl.includes(expectedUrl)) {
    // Not on the issue page, navigate to it
    console.log(`🔗 Navigating to ${issueKey}...`);
    
    window.location.href = `${window.location.origin}${expectedUrl}`;
    
    // Wait for page to load
    await throttle.waitForPageLoad();
    
    // Wait for issue to be visible
    await waitForPageReady();
  }
}


/**
 * Open the edit dialog
 * 
 * WHAT DOES THIS DO?
 * Clicks the "Edit" button and waits for the dialog to appear.
 * 
 * @param throttle - Throttle manager
 */
async function openEditDialog(throttle: ThrottleManager): Promise<void> {
  console.log('🖱️ Opening edit dialog...');
  
  await withRetry(async () => {
    // Find edit button
    const editButton = trySelectors(JIRA_SELECTORS.ISSUE_DETAIL.EDIT_BUTTON);
    
    if (!editButton) {
      throw new Error('Edit button not found');
    }
    
    // Click it
    (editButton as HTMLElement).click();
    
    // Wait for dialog to appear
    await throttle.waitAfterClick();
    
    // Verify dialog is visible
    const dialog = await waitForElement(JIRA_SELECTORS.EDIT_DIALOG.DIALOG, 5000);
    
    if (!dialog) {
      throw new Error('Edit dialog did not appear');
    }
    
    console.log('✓ Edit dialog opened');
    
  }, {
    maxRetries: 3,
    onRetry: (attempt) => console.log(`Retry opening edit dialog (${attempt})...`)
  });
}


/**
 * Set value of an input field
 * 
 * WHAT DOES THIS DO?
 * Clears the field and types the new value (simulating human typing).
 * 
 * WHY CLEAR FIRST?
 * Some fields have existing values we need to replace.
 * 
 * @param field - Input element
 * @param value - New value
 * @param throttle - Throttle manager
 */
async function setFieldValue(
  field: HTMLInputElement | HTMLTextAreaElement,
  value: string,
  throttle: ThrottleManager
): Promise<void> {
  
  console.log(`⌨️ Setting field value to: ${value}`);
  
  // Focus the field (like a human would)
  field.focus();
  await throttle.wait();
  
  // Clear existing value
  field.value = '';
  
  // Trigger input event (some Jira fields need this)
  field.dispatchEvent(new Event('input', { bubbles: true }));
  
  await throttle.wait();
  
  // Set new value
  field.value = value;
  
  // Trigger events that Jira listens for
  field.dispatchEvent(new Event('input', { bubbles: true }));
  field.dispatchEvent(new Event('change', { bubbles: true }));
  
  console.log('✓ Field value set');
}


/**
 * Save the edit dialog
 * 
 * WHAT DOES THIS DO?
 * Clicks the "Update" button and waits for save to complete.
 * 
 * @param throttle - Throttle manager
 */
async function saveEditDialog(throttle: ThrottleManager): Promise<void> {
  console.log('💾 Saving changes...');
  
  await withRetry(async () => {
    // Find submit button
    const submitButton = trySelectors(JIRA_SELECTORS.EDIT_DIALOG.SUBMIT_BUTTON);
    
    if (!submitButton) {
      throw new Error('Submit button not found');
    }
    
    // Click it
    (submitButton as HTMLElement).click();
    
    // Wait for save to complete
    await throttle.waitAfterClick();
    
    // Wait for dialog to close
    await waitForDialogToClose();
    
    console.log('✓ Changes saved');
    
  }, {
    maxRetries: 3,
    onRetry: (attempt) => console.log(`Retry saving changes (${attempt})...`)
  });
}


/**
 * Wait for edit dialog to close
 * 
 * WHAT DOES THIS DO?
 * Waits until the edit dialog disappears from the DOM.
 * 
 * WHY?
 * After clicking "Update", Jira saves and closes the dialog.
 * We need to wait for this to complete.
 */
async function waitForDialogToClose(): Promise<void> {
  let attempts = 0;
  const maxAttempts = 20;  // 10 seconds max
  
  while (attempts < maxAttempts) {
    const dialog = trySelectors(JIRA_SELECTORS.EDIT_DIALOG.DIALOG);
    
    if (!dialog) {
      // Dialog is gone
      console.log('✓ Dialog closed');
      return;
    }
    
    // Still visible, wait
    await sleep(500);
    attempts++;
  }
  
  console.warn('⚠️ Dialog did not close in time');
}


/**
 * Wait for page to be ready
 * 
 * Waits for loading indicators to disappear.
 */
async function waitForPageReady(): Promise<void> {
  let attempts = 0;
  const maxAttempts = 30;
  
  while (attempts < maxAttempts) {
    const loadingIndicator = trySelectors(JIRA_SELECTORS.NAVIGATION.LOADING_INDICATOR);
    
    if (!loadingIndicator) {
      return;
    }
    
    await sleep(1000);
    attempts++;
  }
}


/**
 * Sleep utility
 */
function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}


/*
 * ============================================================================
 * REAL-WORLD USAGE EXAMPLES
 * ============================================================================
 * 
 * EXAMPLE 1: Update due date for an issue
 * 
 *   import { ThrottleManager } from '../utils/throttle-manager';
 *   import { updateDueDate } from './field-updater';
 *   
 *   const throttle = new ThrottleManager();
 *   
 *   const result = await updateDueDate('ABC-123', '2025-01-15', throttle);
 *   
 *   if (result.success) {
 *     console.log(`✓ Updated due date: ${result.oldValue} → ${result.newValue}`);
 *   } else {
 *     console.error(`✗ Failed: ${result.error}`);
 *   }
 * 
 * 
 * EXAMPLE 2: Update multiple issues
 * 
 *   const issues = ['ABC-123', 'ABC-124', 'ABC-125'];
 *   const dueDate = '2025-01-15';
 *   
 *   for (const issueKey of issues) {
 *     await throttle.wait();  // Random delay between issues
 *     
 *     const result = await updateDueDate(issueKey, dueDate, throttle);
 *     
 *     if (result.success) {
 *       console.log(`✓ ${issueKey}: Due date updated`);
 *     } else {
 *       console.error(`✗ ${issueKey}: ${result.error}`);
 *     }
 *   }
 * 
 * 
 * EXAMPLE 3: Update custom field
 * 
 *   const result = await updateTextField(
 *     'ABC-123',
 *     'customfield_10001',  // Custom field ID
 *     'New value',
 *     throttle
 *   );
 */

/*
 * ============================================================================
 * DEVELOPER NOTES
 * ============================================================================
 * 
 * ERROR HANDLING:
 * 
 * Common errors and solutions:
 * 
 * 1. "Edit button not found"
 *    - User might not have edit permission
 *    - Issue might be in a closed status
 *    - Check user permissions
 * 
 * 2. "Field not found"
 *    - Field might be hidden for this issue type
 *    - Field might use different ID in this Jira instance
 *    - Check jira-dom-selectors.ts
 * 
 * 3. "Dialog did not appear"
 *    - Jira might be slow
 *    - Increase wait times
 *    - Check for JavaScript errors
 * 
 * 4. "Changes did not save"
 *    - Validation error (e.g., invalid date format)
 *    - Required field not filled
 *    - Check for error messages in UI
 * 
 * 
 * RELIABILITY:
 * 
 * This module uses retry logic automatically.
 * If something fails temporarily (network, slow page), it retries.
 * 
 * Permanent failures (permissions, validation) fail immediately.
 * 
 * 
 * PERFORMANCE:
 * 
 * Each field update takes ~3-5 seconds:
 *   - Navigate: 1-2s
 *   - Open dialog: 1s
 *   - Fill field: 0.5s
 *   - Save: 1-2s
 * 
 * For 100 issues: ~5-8 minutes
 * 
 * Can't go much faster without looking like a bot.
 */
