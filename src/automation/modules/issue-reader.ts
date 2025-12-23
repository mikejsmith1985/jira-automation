/*
 * ============================================================================
 * ISSUE READER - Extract Issues from Jira Pages
 * ============================================================================
 * 
 * WHAT IS THIS FILE FOR?
 * ----------------------
 * When you run a JQL query in Jira, you get a list of issues.
 * This file extracts those issues from the HTML DOM.
 * 
 * Think of it like reading a shopping list:
 *   - The list is on the page (HTML)
 *   - We need to read each item (issue)
 *   - Extract the data we need (key, summary, fields)
 * 
 * 
 * WHAT WE EXTRACT:
 * ----------------
 * For each issue, we get:
 *   - Issue Key (e.g., "ABC-123")
 *   - Summary (issue title)
 *   - Fix Version (if present)
 *   - Any other visible fields
 * 
 * 
 * WHERE WE READ FROM:
 * -------------------
 * 1. JQL Results Page (Issue Navigator)
 * 2. Agile Board (Scrum/Kanban)
 * 3. Structure Plugin Board
 * 4. Search Results
 */

import { JIRA_SELECTORS, trySelectors, waitForElement } from '../selectors/jira-dom-selectors';

/**
 * IssueData - Information about a single issue
 * 
 * WHAT IS THIS?
 * The data structure we create for each issue we find.
 */
export interface IssueData {
  /**
   * Issue key (e.g., "ABC-123")
   * This is the unique identifier for the issue.
   */
  key: string;
  
  /**
   * Issue summary/title
   * Example: "Implement login page"
   */
  summary: string;
  
  /**
   * Fix version (if present)
   * Example: "Release 2.0"
   * 
   * NOTE: Can be undefined if issue has no fix version
   */
  fixVersion?: string;
  
  /**
   * URL to the issue detail page
   * Example: "https://company.atlassian.net/browse/ABC-123"
   */
  url: string;
  
  /**
   * Additional fields (optional)
   * 
   * WHY?
   * Different views show different fields.
   * We store any extra data we find here.
   * 
   * Example: { status: "To Do", assignee: "John Doe" }
   */
  additionalFields?: Record<string, string>;
}


/**
 * Extract issues from current page
 * 
 * WHAT DOES THIS DO?
 * Looks at the current Jira page and extracts all visible issues.
 * 
 * HOW IT WORKS:
 * 1. Detect what type of page we're on (issue navigator, board, etc.)
 * 2. Find all issue rows/cards
 * 3. Extract data from each
 * 4. Return array of IssueData
 * 
 * EXAMPLE USAGE:
 *   // User runs JQL query, results page loads
 *   const issues = await extractIssuesFromPage();
 *   console.log(`Found ${issues.length} issues`);
 *   // issues = [{ key: "ABC-123", summary: "...", ... }, ...]
 * 
 * @returns Array of IssueData objects
 */
export async function extractIssuesFromPage(): Promise<IssueData[]> {
  console.log('🔍 Extracting issues from current page...');
  
  // Wait for page to be fully loaded
  await waitForPageReady();
  
  // Try different extraction methods based on page type
  let issues: IssueData[] = [];
  
  // Try 1: Issue Navigator (JQL results table)
  issues = await extractFromIssueNavigator();
  if (issues.length > 0) {
    console.log(`✓ Found ${issues.length} issues in Issue Navigator`);
    return issues;
  }
  
  // Try 2: Agile Board (cards)
  issues = await extractFromAgileBoard();
  if (issues.length > 0) {
    console.log(`✓ Found ${issues.length} issues on Agile Board`);
    return issues;
  }
  
  // Try 3: Structure Plugin
  issues = await extractFromStructure();
  if (issues.length > 0) {
    console.log(`✓ Found ${issues.length} issues in Structure`);
    return issues;
  }
  
  // No issues found
  console.warn('⚠️ Could not find any issues on this page');
  return [];
}


/**
 * Extract issues from Issue Navigator (JQL results table)
 * 
 * WHAT IS ISSUE NAVIGATOR?
 * The table view you see after running a JQL query.
 * 
 * WHAT IT LOOKS LIKE:
 * ```
 * Key        Summary              Status    Assignee
 * ABC-123    Implement login      To Do     John
 * ABC-124    Fix bug in parser    Done      Jane
 * ```
 * 
 * @returns Array of issues found
 */
async function extractFromIssueNavigator(): Promise<IssueData[]> {
  console.log('Trying Issue Navigator extraction...');
  
  const issues: IssueData[] = [];
  
  // Find all issue rows
  const issueRows = document.querySelectorAll(JIRA_SELECTORS.ISSUE_LIST.ISSUE_ROW.join(','));
  
  if (issueRows.length === 0) {
    return [];  // Not in Issue Navigator, or no issues
  }
  
  // Extract data from each row
  for (const row of Array.from(issueRows)) {
    try {
      const issueData = extractIssueFromRow(row as HTMLElement);
      if (issueData) {
        issues.push(issueData);
      }
    } catch (error) {
      console.warn('Error extracting issue from row:', error);
    }
  }
  
  return issues;
}


/**
 * Extract issue data from a single table row
 * 
 * @param row - HTML element representing the issue row
 * @returns IssueData or null if extraction fails
 */
function extractIssueFromRow(row: HTMLElement): IssueData | null {
  // Find issue key
  const keyElement = row.querySelector(JIRA_SELECTORS.ISSUE_LIST.ISSUE_KEY.join(',')) as HTMLElement;
  if (!keyElement) {
    console.warn('Could not find issue key in row');
    return null;
  }
  
  const key = keyElement.textContent?.trim() || '';
  if (!key) {
    return null;
  }
  
  // Find summary
  const summaryElement = row.querySelector(JIRA_SELECTORS.ISSUE_LIST.SUMMARY.join(',')) as HTMLElement;
  const summary = summaryElement?.textContent?.trim() || '';
  
  // Build URL
  const url = buildIssueUrl(key);
  
  // Try to find fix version
  const fixVersion = extractFixVersionFromRow(row);
  
  // Extract other fields if visible
  const additionalFields = extractAdditionalFieldsFromRow(row);
  
  return {
    key,
    summary,
    fixVersion,
    url,
    additionalFields
  };
}


/**
 * Extract fix version from a row
 * 
 * @param row - HTML element
 * @returns Fix version string or undefined
 */
function extractFixVersionFromRow(row: HTMLElement): string | undefined {
  // Look for fix version cell
  // Different Jira versions use different selectors
  const fixVersionSelectors = [
    '[data-field-id="fixVersions"]',
    '.fixfor-val',
    'td.fixVersions'
  ];
  
  for (const selector of fixVersionSelectors) {
    const element = row.querySelector(selector) as HTMLElement;
    if (element) {
      const text = element.textContent?.trim();
      if (text && text !== '-' && text !== 'None') {
        return text;
      }
    }
  }
  
  return undefined;
}


/**
 * Extract additional visible fields from row
 * 
 * @param row - HTML element
 * @returns Object with field name/value pairs
 */
function extractAdditionalFieldsFromRow(row: HTMLElement): Record<string, string> {
  const fields: Record<string, string> = {};
  
  // Common fields to look for
  const fieldSelectors = {
    status: '[data-field-id="status"]',
    assignee: '[data-field-id="assignee"]',
    priority: '[data-field-id="priority"]',
    duedate: '[data-field-id="duedate"]'
  };
  
  for (const [fieldName, selector] of Object.entries(fieldSelectors)) {
    const element = row.querySelector(selector) as HTMLElement;
    if (element) {
      const value = element.textContent?.trim();
      if (value && value !== '-') {
        fields[fieldName] = value;
      }
    }
  }
  
  return fields;
}


/**
 * Extract issues from Agile Board (Scrum/Kanban)
 * 
 * WHAT IS AGILE BOARD?
 * The card view with columns (To Do, In Progress, Done).
 * Issues are displayed as cards you can drag between columns.
 * 
 * @returns Array of issues found
 */
async function extractFromAgileBoard(): Promise<IssueData[]> {
  console.log('Trying Agile Board extraction...');
  
  const issues: IssueData[] = [];
  
  // Find all issue cards
  const issueCards = document.querySelectorAll('.ghx-issue, [data-issue-key]');
  
  if (issueCards.length === 0) {
    return [];
  }
  
  for (const card of Array.from(issueCards)) {
    try {
      const issueData = extractIssueFromCard(card as HTMLElement);
      if (issueData) {
        issues.push(issueData);
      }
    } catch (error) {
      console.warn('Error extracting issue from card:', error);
    }
  }
  
  return issues;
}


/**
 * Extract issue data from an agile board card
 * 
 * @param card - HTML element representing the card
 * @returns IssueData or null
 */
function extractIssueFromCard(card: HTMLElement): IssueData | null {
  // Get issue key from data attribute or text
  const key = card.getAttribute('data-issue-key') ||
              card.querySelector('.ghx-key')?.textContent?.trim() ||
              '';
  
  if (!key) {
    return null;
  }
  
  // Get summary
  const summary = card.querySelector('.ghx-summary')?.textContent?.trim() || '';
  
  // Build URL
  const url = buildIssueUrl(key);
  
  return {
    key,
    summary,
    url
  };
}


/**
 * Extract issues from Structure Plugin
 * 
 * WHAT IS STRUCTURE?
 * A Jira plugin that shows issues in a hierarchical tree/table.
 * Popular for portfolio management.
 * 
 * @returns Array of issues found
 */
async function extractFromStructure(): Promise<IssueData[]> {
  console.log('Trying Structure extraction...');
  
  const issues: IssueData[] = [];
  
  // Find Structure grid
  const structureGrid = trySelectors(JIRA_SELECTORS.STRUCTURE.GRID);
  if (!structureGrid) {
    return [];
  }
  
  // Find all issue rows in Structure
  const issueRows = structureGrid.querySelectorAll(JIRA_SELECTORS.STRUCTURE.ISSUE_ROW.join(','));
  
  for (const row of Array.from(issueRows)) {
    try {
      const issueData = extractIssueFromRow(row as HTMLElement);
      if (issueData) {
        issues.push(issueData);
      }
    } catch (error) {
      console.warn('Error extracting issue from Structure row:', error);
    }
  }
  
  return issues;
}


/**
 * Build full URL for an issue
 * 
 * @param key - Issue key (e.g., "ABC-123")
 * @returns Full URL to issue
 */
function buildIssueUrl(key: string): string {
  // Get base URL from current page
  const baseUrl = window.location.origin;
  
  // Build browse URL
  return `${baseUrl}/browse/${key}`;
}


/**
 * Wait for page to be ready for extraction
 * 
 * WHAT DOES THIS DO?
 * Waits for Jira to finish loading before we try to extract issues.
 * 
 * WHY?
 * Jira loads content dynamically with AJAX.
 * If we try to extract too early, we'll miss issues.
 * 
 * HOW IT WORKS:
 * Wait for loading indicators to disappear.
 */
async function waitForPageReady(): Promise<void> {
  console.log('⏳ Waiting for page to be ready...');
  
  // Wait for loading indicator to disappear
  const loadingIndicators = JIRA_SELECTORS.NAVIGATION.LOADING_INDICATOR;
  
  // Keep checking if loading indicator exists
  let attempts = 0;
  const maxAttempts = 30;  // 30 seconds max
  
  while (attempts < maxAttempts) {
    const loadingElement = trySelectors(loadingIndicators);
    
    if (!loadingElement) {
      // No loading indicator visible, page is ready
      console.log('✓ Page is ready');
      return;
    }
    
    // Still loading, wait a bit
    await sleep(1000);
    attempts++;
  }
  
  console.warn('⚠️ Page took too long to load, proceeding anyway');
}


/**
 * Sleep utility
 * 
 * @param ms - Milliseconds to sleep
 */
function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}


/*
 * ============================================================================
 * REAL-WORLD USAGE EXAMPLES
 * ============================================================================
 * 
 * EXAMPLE 1: Extract all issues from current page
 * 
 *   // User navigates to JQL results page
 *   const issues = await extractIssuesFromPage();
 *   
 *   console.log(`Found ${issues.length} issues:`);
 *   for (const issue of issues) {
 *     console.log(`- ${issue.key}: ${issue.summary}`);
 *     if (issue.fixVersion) {
 *       console.log(`  Fix Version: ${issue.fixVersion}`);
 *     }
 *   }
 * 
 * 
 * EXAMPLE 2: Filter issues by fix version
 * 
 *   const allIssues = await extractIssuesFromPage();
 *   
 *   const issuesWithFixVersion = allIssues.filter(issue => issue.fixVersion);
 *   
 *   console.log(`${issuesWithFixVersion.length} issues have fix versions`);
 * 
 * 
 * EXAMPLE 3: Navigate and extract from multiple pages
 * 
 *   // If there are multiple pages of results
 *   let allIssues: IssueData[] = [];
 *   let hasNextPage = true;
 *   
 *   while (hasNextPage) {
 *     // Extract from current page
 *     const pageIssues = await extractIssuesFromPage();
 *     allIssues = allIssues.concat(pageIssues);
 *     
 *     // Click next page button
 *     const nextButton = document.querySelector('.pagination-next');
 *     if (nextButton && !nextButton.hasAttribute('disabled')) {
 *       (nextButton as HTMLElement).click();
 *       await sleep(2000);  // Wait for page load
 *     } else {
 *       hasNextPage = false;
 *     }
 *   }
 *   
 *   console.log(`Total issues across all pages: ${allIssues.length}`);
 */

/*
 * ============================================================================
 * DEVELOPER NOTES
 * ============================================================================
 * 
 * HANDLING DIFFERENT JIRA VIEWS:
 * 
 * Jira has many different views:
 *   - Issue Navigator (table)
 *   - Agile Boards (cards)
 *   - Structure (hierarchical)
 *   - List view
 *   - Detail view
 * 
 * We try each extraction method in order.
 * First one that finds issues wins.
 * 
 * 
 * PAGINATION:
 * 
 * If there are 500 issues, Jira shows them in pages (50 per page).
 * This module extracts from ONE page at a time.
 * 
 * To get all issues:
 * 1. Extract from page 1
 * 2. Click "Next" button
 * 3. Wait for page load
 * 4. Extract from page 2
 * 5. Repeat until no more pages
 * 
 * (Pagination logic is in jira-injector.ts, not here)
 * 
 * 
 * DYNAMIC LOADING:
 * 
 * Modern Jira uses infinite scroll or lazy loading.
 * Issues load as you scroll down.
 * 
 * To handle this:
 * - Scroll to bottom of page
 * - Wait for new issues to load
 * - Extract again
 * - Repeat until no more issues load
 * 
 * 
 * RELIABILITY:
 * 
 * Jira's HTML structure changes frequently.
 * We use multiple fallback selectors in jira-dom-selectors.ts.
 * 
 * If extraction breaks after Jira update:
 * 1. Open Jira in browser
 * 2. Inspect issue elements
 * 3. Find new selectors
 * 4. Update jira-dom-selectors.ts
 * 5. Extraction works again
 * 
 * 
 * TESTING:
 * 
 * Test extraction with:
 * - JQL with 0 results (should return empty array)
 * - JQL with 1 result
 * - JQL with 100+ results
 * - Different views (navigator, board, structure)
 * - Issues with/without fix versions
 */
