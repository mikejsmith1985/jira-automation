/*
 * ============================================================================
 * THROTTLE MANAGER - Human-Like Delays Between Actions
 * ============================================================================
 * 
 * WHAT IS THIS FILE FOR?
 * ----------------------
 * When automating Jira, we don't want to look like a bot.
 * If we click buttons instantly one after another, it's suspicious:
 * 
 * ❌ Bot behavior:
 *    Click → Click → Click → Click (instant, 0ms between actions)
 * 
 * ✅ Human behavior:
 *    Click → wait 1.2s → Click → wait 0.8s → Click → wait 1.5s → Click
 * 
 * This file provides "throttling" - intentional delays that make
 * automation look like a human operator.
 * 
 * 
 * WHY DO WE NEED THIS?
 * --------------------
 * Three reasons:
 * 
 * 1. **Security/Compliance**
 *    - IT security teams flag "bot-like" behavior
 *    - Random delays look more human
 *    - Reduces risk of being blocked
 * 
 * 2. **Jira Performance**
 *    - Too many requests too fast can slow down Jira
 *    - Rate limiting might kick in
 *    - Server needs time to process each request
 * 
 * 3. **Reliability**
 *    - Jira pages load content dynamically
 *    - Need time for JavaScript to execute
 *    - UI elements appear with delays
 * 
 * 
 * HOW IT WORKS:
 * -------------
 * We specify a MIN and MAX delay:
 *   minDelayMs: 500   (0.5 seconds minimum)
 *   maxDelayMs: 2000  (2 seconds maximum)
 * 
 * Each action waits a RANDOM time between min and max:
 *   Action 1 → wait 1,234ms → Action 2 → wait 789ms → Action 3
 * 
 * Random delays are more human-like than fixed delays.
 */

/**
 * ThrottleConfig - Configuration for throttling behavior
 * 
 * WHAT'S IN HERE?
 * Settings that control how delays work.
 */
export interface ThrottleConfig {
  /**
   * Minimum delay between actions (milliseconds)
   * Default: 500 (0.5 seconds)
   * 
   * WHY?
   * Even the fastest human takes some time to:
   *   - Move mouse
   *   - Read the screen
   *   - Click button
   * 
   * 0.5 seconds is a reasonable minimum.
   */
  minDelayMs: number;
  
  /**
   * Maximum delay between actions (milliseconds)
   * Default: 2000 (2 seconds)
   * 
   * WHY?
   * Humans are inconsistent - sometimes fast, sometimes slow:
   *   - Looking at another screen
   *   - Thinking about what to do next
   *   - Reading issue details
   * 
   * Random variation makes it look natural.
   */
  maxDelayMs: number;
  
  /**
   * Delay before first action (milliseconds)
   * Default: 1000 (1 second)
   * 
   * WHY?
   * When a human opens a page, they don't click immediately.
   * They look at the screen, find the button, THEN click.
   * 
   * This initial delay simulates that "looking" time.
   */
  initialDelayMs?: number;
  
  /**
   * Delay after clicking buttons (milliseconds)
   * Default: Same as maxDelayMs
   * 
   * WHY?
   * After clicking, humans wait for:
   *   - Animation to finish
   *   - Page to update
   *   - New content to appear
   * 
   * You might want this longer than normal delays.
   */
  afterClickDelayMs?: number;
  
  /**
   * Delay after page navigation (milliseconds)
   * Default: 3000 (3 seconds)
   * 
   * WHY?
   * Pages take time to load:
   *   - HTTP request
   *   - HTML parsing
   *   - JavaScript execution
   *   - CSS rendering
   * 
   * Need to wait for page to be ready before interacting.
   */
  pageLoadDelayMs?: number;
}

/**
 * Default throttle configuration
 * 
 * These are conservative defaults that look human-like
 * while not being too slow.
 */
export const DEFAULT_THROTTLE_CONFIG: ThrottleConfig = {
  minDelayMs: 500,           // 0.5 seconds minimum
  maxDelayMs: 2000,          // 2 seconds maximum
  initialDelayMs: 1000,      // 1 second before starting
  afterClickDelayMs: 1500,   // 1.5 seconds after clicks
  pageLoadDelayMs: 3000      // 3 seconds after page loads
};

/**
 * Fast throttle configuration (for testing or urgent automation)
 * 
 * Use this when you need faster automation but still want
 * some human-like behavior.
 */
export const FAST_THROTTLE_CONFIG: ThrottleConfig = {
  minDelayMs: 200,           // 0.2 seconds
  maxDelayMs: 500,           // 0.5 seconds
  initialDelayMs: 500,       // 0.5 seconds
  afterClickDelayMs: 300,    // 0.3 seconds
  pageLoadDelayMs: 1000      // 1 second
};

/**
 * Slow throttle configuration (for very cautious automation)
 * 
 * Use this for:
 *   - Production environments with strict monitoring
 *   - Slow Jira instances
 *   - When you want maximum "human-ness"
 */
export const SLOW_THROTTLE_CONFIG: ThrottleConfig = {
  minDelayMs: 1000,          // 1 second
  maxDelayMs: 4000,          // 4 seconds
  initialDelayMs: 2000,      // 2 seconds
  afterClickDelayMs: 3000,   // 3 seconds
  pageLoadDelayMs: 5000      // 5 seconds
};


/**
 * ThrottleManager - Manages delays between actions
 * 
 * WHAT IS THIS?
 * A class that provides various delay functions with configuration.
 * 
 * WHY A CLASS?
 * We want to maintain state (last action time, config) across calls.
 */
export class ThrottleManager {
  private config: ThrottleConfig;
  private lastActionTime: number = 0;
  
  /**
   * Create a new ThrottleManager
   * 
   * @param config - Throttle configuration (uses defaults if not provided)
   */
  constructor(config: Partial<ThrottleConfig> = {}) {
    // Merge user config with defaults
    this.config = {
      ...DEFAULT_THROTTLE_CONFIG,
      ...config
    };
    
    console.log('ThrottleManager initialized with config:', this.config);
  }
  
  /**
   * Get a random delay between min and max
   * 
   * WHAT DOES THIS DO?
   * Returns a random number between minDelayMs and maxDelayMs.
   * 
   * WHY RANDOM?
   * Humans are unpredictable. Random delays look more natural.
   * 
   * EXAMPLE:
   *   minDelayMs = 500, maxDelayMs = 2000
   *   Possible results: 734ms, 1892ms, 523ms, 1456ms, ...
   *   Each call returns a different random value
   * 
   * @returns Random delay in milliseconds
   */
  private getRandomDelay(): number {
    const min = this.config.minDelayMs;
    const max = this.config.maxDelayMs;
    
    // Math.random() returns 0.0 to 1.0
    // Multiply by range, add to min
    const delay = Math.random() * (max - min) + min;
    
    // Round to nearest millisecond
    return Math.round(delay);
  }
  
  /**
   * Wait for a random delay
   * 
   * WHAT DOES THIS DO?
   * Pauses execution for a random time between min and max delays.
   * 
   * WHEN TO USE:
   * Between any two automation actions.
   * 
   * EXAMPLE:
   *   await throttle.wait();  // Waits 500-2000ms randomly
   *   button.click();
   *   await throttle.wait();  // Waits again before next action
   * 
   * @returns Promise that resolves after the delay
   */
  async wait(): Promise<void> {
    const delay = this.getRandomDelay();
    console.log(`⏳ Throttling: waiting ${delay}ms...`);
    await this.sleep(delay);
    this.lastActionTime = Date.now();
  }
  
  /**
   * Wait for initial delay (before starting automation)
   * 
   * WHAT DOES THIS DO?
   * Waits for initialDelayMs before beginning automation.
   * 
   * WHEN TO USE:
   * Once at the very start, before first action.
   * 
   * WHY?
   * Simulates human "looking at the page" time before starting.
   * 
   * EXAMPLE:
   *   await throttle.waitInitial();  // Wait 1 second
   *   // Now start clicking buttons
   */
  async waitInitial(): Promise<void> {
    const delay = this.config.initialDelayMs || this.config.minDelayMs;
    console.log(`⏳ Initial delay: waiting ${delay}ms...`);
    await this.sleep(delay);
    this.lastActionTime = Date.now();
  }
  
  /**
   * Wait after clicking a button
   * 
   * WHAT DOES THIS DO?
   * Waits for afterClickDelayMs after a click action.
   * 
   * WHEN TO USE:
   * After clicking any button that causes page changes.
   * 
   * WHY?
   * Clicks trigger:
   *   - Animations
   *   - AJAX requests
   *   - DOM updates
   *   - JavaScript execution
   * 
   * Need to wait for these to complete.
   * 
   * EXAMPLE:
   *   editButton.click();
   *   await throttle.waitAfterClick();  // Wait for edit dialog to appear
   *   // Now interact with the dialog
   */
  async waitAfterClick(): Promise<void> {
    const delay = this.config.afterClickDelayMs || this.config.maxDelayMs;
    console.log(`⏳ After-click delay: waiting ${delay}ms...`);
    await this.sleep(delay);
    this.lastActionTime = Date.now();
  }
  
  /**
   * Wait after page navigation
   * 
   * WHAT DOES THIS DO?
   * Waits for pageLoadDelayMs after navigating to a new page.
   * 
   * WHEN TO USE:
   * After clicking links that load new pages.
   * 
   * WHY?
   * Pages take time to:
   *   - Make HTTP request
   *   - Download HTML/CSS/JS
   *   - Parse and render
   *   - Execute JavaScript
   *   - Fetch additional AJAX data
   * 
   * EXAMPLE:
   *   issueLink.click();
   *   await throttle.waitForPageLoad();  // Wait for issue detail page
   *   // Now page is ready, can read issue data
   */
  async waitForPageLoad(): Promise<void> {
    const delay = this.config.pageLoadDelayMs || 3000;
    console.log(`⏳ Page load delay: waiting ${delay}ms...`);
    await this.sleep(delay);
    this.lastActionTime = Date.now();
  }
  
  /**
   * Wait with a custom delay
   * 
   * WHAT DOES THIS DO?
   * Waits for a specific amount of time.
   * 
   * WHEN TO USE:
   * When you need a specific delay that doesn't fit other categories.
   * 
   * EXAMPLE:
   *   await throttle.waitCustom(5000);  // Wait exactly 5 seconds
   * 
   * @param delayMs - Milliseconds to wait
   */
  async waitCustom(delayMs: number): Promise<void> {
    console.log(`⏳ Custom delay: waiting ${delayMs}ms...`);
    await this.sleep(delayMs);
    this.lastActionTime = Date.now();
  }
  
  /**
   * Ensure minimum time has passed since last action
   * 
   * WHAT DOES THIS DO?
   * If you accidentally call actions too quickly, this adds
   * additional delay to maintain minimum spacing.
   * 
   * WHY?
   * Safety net to prevent actions from running too fast.
   * 
   * EXAMPLE:
   *   action1();
   *   action2();  // Oops, called immediately
   *   await throttle.ensureMinDelay();  // Adds delay if needed
   * 
   * @returns Promise that resolves after ensuring minimum delay
   */
  async ensureMinDelay(): Promise<void> {
    const now = Date.now();
    const timeSinceLastAction = now - this.lastActionTime;
    const minDelay = this.config.minDelayMs;
    
    if (timeSinceLastAction < minDelay) {
      // Not enough time has passed, need to wait more
      const additionalDelay = minDelay - timeSinceLastAction;
      console.log(`⏳ Ensuring min delay: waiting additional ${additionalDelay}ms...`);
      await this.sleep(additionalDelay);
    }
    
    this.lastActionTime = Date.now();
  }
  
  /**
   * Update configuration
   * 
   * WHAT DOES THIS DO?
   * Changes throttle settings on the fly.
   * 
   * WHEN TO USE:
   * If you want to speed up or slow down during automation.
   * 
   * EXAMPLE:
   *   // Start with default settings
   *   const throttle = new ThrottleManager();
   *   
   *   // Do some work...
   *   
   *   // Speed up for final batch
   *   throttle.updateConfig(FAST_THROTTLE_CONFIG);
   * 
   * @param config - New configuration (partial or complete)
   */
  updateConfig(config: Partial<ThrottleConfig>): void {
    this.config = {
      ...this.config,
      ...config
    };
    console.log('ThrottleManager config updated:', this.config);
  }
  
  /**
   * Get current configuration
   * 
   * @returns Current throttle configuration
   */
  getConfig(): ThrottleConfig {
    return { ...this.config };
  }
  
  /**
   * Sleep utility
   * 
   * WHAT DOES THIS DO?
   * Simple promise-based sleep function.
   * 
   * @param ms - Milliseconds to sleep
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}


/**
 * Create a throttle manager from app config
 * 
 * WHAT DOES THIS DO?
 * Convenience function to create ThrottleManager from IAppConfig.
 * 
 * WHY?
 * User sets throttle settings in app config.
 * This converts that config into a ThrottleManager instance.
 * 
 * EXAMPLE:
 *   import { IAppConfig } from '../shared/interfaces/IAppConfig';
 *   
 *   const config: IAppConfig = loadConfig();
 *   const throttle = createThrottleFromConfig(config);
 *   
 *   await throttle.wait();  // Uses user's configured delays
 * 
 * @param config - Application configuration
 * @returns Configured ThrottleManager instance
 */
export function createThrottleFromConfig(config: { throttling: { minDelayMs: number, maxDelayMs: number, pageLoadTimeoutMs: number } }): ThrottleManager {
  return new ThrottleManager({
    minDelayMs: config.throttling.minDelayMs,
    maxDelayMs: config.throttling.maxDelayMs,
    pageLoadDelayMs: config.throttling.pageLoadTimeoutMs
  });
}


/*
 * ============================================================================
 * REAL-WORLD USAGE EXAMPLES
 * ============================================================================
 * 
 * EXAMPLE 1: Basic automation with throttling
 * 
 *   const throttle = new ThrottleManager();
 *   
 *   // Wait before starting
 *   await throttle.waitInitial();
 *   
 *   // Find and click edit button
 *   const editButton = document.querySelector('#edit-issue');
 *   editButton.click();
 *   await throttle.waitAfterClick();  // Wait for dialog
 *   
 *   // Fill in field
 *   const dueDateField = document.querySelector('#duedate');
 *   dueDateField.value = '2025-01-15';
 *   await throttle.wait();  // Random delay
 *   
 *   // Save
 *   const saveButton = document.querySelector('#edit-issue-submit');
 *   saveButton.click();
 *   await throttle.waitAfterClick();
 * 
 * 
 * EXAMPLE 2: Processing multiple issues
 * 
 *   const throttle = new ThrottleManager();
 *   const issues = ['ABC-123', 'ABC-124', 'ABC-125'];
 *   
 *   for (const issueKey of issues) {
 *     // Wait between issues (random)
 *     await throttle.wait();
 *     
 *     // Navigate to issue
 *     window.location.href = `/browse/${issueKey}`;
 *     await throttle.waitForPageLoad();
 *     
 *     // Update issue...
 *     await updateIssue(issueKey);
 *   }
 * 
 * 
 * EXAMPLE 3: Using different speed presets
 * 
 *   // Fast mode for testing
 *   const throttle = new ThrottleManager(FAST_THROTTLE_CONFIG);
 *   
 *   // Or slow mode for production
 *   const throttle = new ThrottleManager(SLOW_THROTTLE_CONFIG);
 *   
 *   // Or custom config
 *   const throttle = new ThrottleManager({
 *     minDelayMs: 300,
 *     maxDelayMs: 1000
 *   });
 * 
 * 
 * EXAMPLE 4: Dynamic speed adjustment
 * 
 *   const throttle = new ThrottleManager();
 *   
 *   // Process first 10 issues slowly (careful)
 *   for (let i = 0; i < 10; i++) {
 *     await processIssue(issues[i], throttle);
 *   }
 *   
 *   // Everything working well? Speed up!
 *   throttle.updateConfig(FAST_THROTTLE_CONFIG);
 *   
 *   // Process remaining issues faster
 *   for (let i = 10; i < issues.length; i++) {
 *     await processIssue(issues[i], throttle);
 *   }
 */

/*
 * ============================================================================
 * DEVELOPER NOTES
 * ============================================================================
 * 
 * CHOOSING THE RIGHT DELAYS:
 * 
 * Too fast (minDelayMs < 200):
 *   ❌ Looks like a bot
 *   ❌ Might trigger rate limiting
 *   ❌ Elements might not be ready
 * 
 * Too slow (maxDelayMs > 5000):
 *   ❌ Automation takes forever
 *   ❌ User gets impatient
 *   ❌ Timeout risks increase
 * 
 * Sweet spot:
 *   ✅ minDelayMs: 500-1000ms
 *   ✅ maxDelayMs: 2000-3000ms
 *   ✅ Random variation between them
 * 
 * 
 * WHEN TO USE EACH WAIT METHOD:
 * 
 * wait(): Between any two actions
 * waitInitial(): Once at start
 * waitAfterClick(): After buttons that cause UI changes
 * waitForPageLoad(): After navigation
 * waitCustom(): Special cases (long operations)
 * ensureMinDelay(): Safety net (automatic spacing)
 * 
 * 
 * DEBUGGING SLOW AUTOMATION:
 * 
 * If automation is too slow:
 * 1. Check your delay config - are they too long?
 * 2. Are you calling wait() too many times?
 * 3. Try FAST_THROTTLE_CONFIG for testing
 * 4. Profile with console.log to see where time is spent
 * 
 * 
 * DEBUGGING FAST/FAILING AUTOMATION:
 * 
 * If automation fails with "element not found":
 * 1. Increase delays - might need more time
 * 2. Use waitAfterClick() after every button
 * 3. Add waitForPageLoad() after navigation
 * 4. Try SLOW_THROTTLE_CONFIG
 * 5. Check if elements load asynchronously
 */
