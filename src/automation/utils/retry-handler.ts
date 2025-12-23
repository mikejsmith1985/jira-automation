/*
 * ============================================================================
 * RETRY HANDLER - Smart Error Recovery with Exponential Backoff
 * ============================================================================
 * 
 * WHAT IS THIS FILE FOR?
 * ----------------------
 * When automation fails (network hiccup, Jira slow, etc.), we don't give up
 * immediately. We retry with increasingly longer waits between attempts.
 * 
 * Think of it like knocking on a door:
 *   - Knock once: No answer (maybe they didn't hear)
 *   - Wait 1 second, knock again: No answer (maybe they're busy)
 *   - Wait 2 seconds, knock again: No answer (maybe they're in the shower)
 *   - Wait 4 seconds, knock again: No answer (okay, nobody's home)
 * 
 * This is called "exponential backoff" - each wait is longer than the last.
 * 
 * 
 * WHY DO WE NEED THIS?
 * --------------------
 * Things that can temporarily fail:
 *   - Network request times out (retry usually works)
 *   - Jira page is slow to load (wait longer, then works)
 *   - Element not found yet (page still loading)
 *   - Click didn't register (browser busy)
 * 
 * Instead of failing the entire automation, we retry intelligently.
 * 
 * 
 * EXPONENTIAL BACKOFF EXAMPLE:
 * ----------------------------
 * With maxRetries=3, backoffMultiplier=2, initialDelayMs=1000:
 * 
 *   Attempt 1: Try immediately → Fail
 *   Wait 1 second (1000ms)
 *   Attempt 2: Try again → Fail
 *   Wait 2 seconds (1000ms * 2)
 *   Attempt 3: Try again → Fail
 *   Wait 4 seconds (2000ms * 2)
 *   Attempt 4: Try again → Fail
 *   Give up, throw error
 * 
 * Total time: ~7 seconds (1 + 2 + 4)
 * Total attempts: 4 (initial + 3 retries)
 */

/**
 * RetryOptions - Configuration for retry behavior
 * 
 * WHAT'S IN HERE?
 * Settings that control how retries work.
 */
export interface RetryOptions {
  /**
   * Maximum number of retry attempts
   * Default: 3
   * 
   * NOTE: Total attempts = maxRetries + 1 (initial attempt)
   * maxRetries=3 means 4 total attempts
   */
  maxRetries?: number;
  
  /**
   * Initial delay before first retry (milliseconds)
   * Default: 1000 (1 second)
   * 
   * Each subsequent retry waits longer (multiplied by backoffMultiplier)
   */
  initialDelayMs?: number;
  
  /**
   * How much to multiply the delay after each retry
   * Default: 2 (doubles each time)
   * 
   * Examples:
   *   2 = 1s, 2s, 4s, 8s (doubling)
   *   1.5 = 1s, 1.5s, 2.25s, 3.375s (slower growth)
   */
  backoffMultiplier?: number;
  
  /**
   * Maximum delay between retries (milliseconds)
   * Default: 30000 (30 seconds)
   * 
   * WHY?
   * Prevents delays from growing too large.
   * Example: After 10 retries with multiplier=2, delay would be 1024 seconds!
   * This caps it at a reasonable maximum.
   */
  maxDelayMs?: number;
  
  /**
   * Function that decides if we should retry based on the error
   * Default: Always retry
   * 
   * WHY?
   * Some errors shouldn't be retried:
   *   - "Permission denied" → Retry won't help
   *   - "Issue not found" → Retry won't help
   *   - Network timeout → Retry WILL help
   * 
   * EXAMPLE:
   *   shouldRetry: (error) => {
   *     if (error.message.includes('permission')) return false;
   *     return true;
   *   }
   */
  shouldRetry?: (error: Error) => boolean;
  
  /**
   * Callback function called before each retry
   * Default: None
   * 
   * WHY?
   * Useful for logging or notifying user.
   * 
   * EXAMPLE:
   *   onRetry: (attempt, error) => {
   *     console.log(`Retry attempt ${attempt} after error:`, error);
   *   }
   */
  onRetry?: (attempt: number, error: Error) => void;
}

/**
 * Default retry options
 * 
 * These are sensible defaults that work well for most cases.
 * You can override any of them when calling retry functions.
 */
const DEFAULT_RETRY_OPTIONS: Required<RetryOptions> = {
  maxRetries: 3,
  initialDelayMs: 1000,
  backoffMultiplier: 2,
  maxDelayMs: 30000,
  shouldRetry: () => true,  // Always retry by default
  onRetry: () => {}  // No-op by default
};


/**
 * Execute a function with automatic retry logic
 * 
 * WHAT DOES THIS DO?
 * Wraps any async function and retries it if it fails.
 * 
 * HOW IT WORKS:
 * 1. Try to execute the function
 * 2. If it succeeds, return the result
 * 3. If it fails, wait (with exponential backoff), then retry
 * 4. Repeat until success or max retries reached
 * 
 * EXAMPLE USAGE:
 * 
 *   // Function that might fail
 *   async function clickButton() {
 *     const button = document.querySelector('#edit-button');
 *     if (!button) throw new Error('Button not found');
 *     button.click();
 *   }
 * 
 *   // Wrap with retry logic
 *   await withRetry(clickButton, {
 *     maxRetries: 3,
 *     onRetry: (attempt) => console.log(`Retry attempt ${attempt}`)
 *   });
 * 
 * @param fn - Async function to execute (can throw errors)
 * @param options - Retry configuration
 * @returns Promise that resolves to function result or throws if all retries fail
 */
export async function withRetry<T>(
  fn: () => Promise<T>,
  options: RetryOptions = {}
): Promise<T> {
  
  // Merge user options with defaults
  const opts: Required<RetryOptions> = {
    ...DEFAULT_RETRY_OPTIONS,
    ...options
  };
  
  let lastError: Error | null = null;
  let currentDelay = opts.initialDelayMs;
  
  // Try initial attempt + retries
  for (let attempt = 0; attempt <= opts.maxRetries; attempt++) {
    try {
      // Try to execute the function
      const result = await fn();
      
      // Success! Return the result
      if (attempt > 0) {
        console.log(`✓ Success after ${attempt} retries`);
      }
      return result;
      
    } catch (error) {
      lastError = error as Error;
      
      // Check if we should retry this error
      if (!opts.shouldRetry(lastError)) {
        console.log(`✗ Error not retryable: ${lastError.message}`);
        throw lastError;
      }
      
      // Check if we've exhausted retries
      if (attempt >= opts.maxRetries) {
        console.error(`✗ All ${opts.maxRetries} retries exhausted`);
        throw lastError;
      }
      
      // We're going to retry - log it
      console.warn(`⚠️ Attempt ${attempt + 1} failed: ${lastError.message}`);
      console.log(`⏳ Waiting ${currentDelay}ms before retry ${attempt + 1}...`);
      
      // Call onRetry callback if provided
      opts.onRetry(attempt + 1, lastError);
      
      // Wait before retrying
      await sleep(currentDelay);
      
      // Increase delay for next retry (exponential backoff)
      currentDelay = Math.min(
        currentDelay * opts.backoffMultiplier,
        opts.maxDelayMs
      );
    }
  }
  
  // Should never reach here, but TypeScript requires it
  throw lastError || new Error('Retry failed with unknown error');
}


/**
 * Retry a function until it returns true or times out
 * 
 * WHAT DOES THIS DO?
 * Keeps calling a function until it returns true (success condition met).
 * 
 * WHY DIFFERENT FROM withRetry?
 * - withRetry: Retries on exceptions
 * - retryUntil: Retries until condition is true (no exceptions needed)
 * 
 * USE CASE:
 * Waiting for something to happen (element appears, status changes, etc.)
 * 
 * EXAMPLE:
 * 
 *   // Wait for element to appear
 *   const found = await retryUntil(
 *     () => document.querySelector('#loading') === null,  // Returns true when loading done
 *     { maxRetries: 10, initialDelayMs: 500 }
 *   );
 * 
 * @param conditionFn - Function that returns true when condition is met
 * @param options - Retry configuration
 * @returns Promise that resolves to true if condition met, false if timeout
 */
export async function retryUntil(
  conditionFn: () => boolean | Promise<boolean>,
  options: RetryOptions = {}
): Promise<boolean> {
  
  const opts: Required<RetryOptions> = {
    ...DEFAULT_RETRY_OPTIONS,
    ...options
  };
  
  let currentDelay = opts.initialDelayMs;
  
  for (let attempt = 0; attempt <= opts.maxRetries; attempt++) {
    try {
      // Check condition
      const result = await conditionFn();
      
      if (result) {
        // Condition met!
        if (attempt > 0) {
          console.log(`✓ Condition met after ${attempt} attempts`);
        }
        return true;
      }
      
      // Condition not met yet
      if (attempt < opts.maxRetries) {
        console.log(`⏳ Condition not met, waiting ${currentDelay}ms...`);
        await sleep(currentDelay);
        
        // Increase delay for next attempt
        currentDelay = Math.min(
          currentDelay * opts.backoffMultiplier,
          opts.maxDelayMs
        );
      }
      
    } catch (error) {
      // conditionFn threw an error
      console.warn(`⚠️ Condition check failed: ${error}`);
      
      // Should we retry errors?
      const shouldRetryError = opts.shouldRetry(error as Error);
      if (!shouldRetryError) {
        return false;
      }
      
      // Wait and try again
      if (attempt < opts.maxRetries) {
        await sleep(currentDelay);
        currentDelay = Math.min(
          currentDelay * opts.backoffMultiplier,
          opts.maxDelayMs
        );
      }
    }
  }
  
  // Exhausted all retries, condition never met
  console.error(`✗ Condition not met after ${opts.maxRetries} retries`);
  return false;
}


/**
 * Sleep utility function
 * 
 * WHAT DOES THIS DO?
 * Pauses execution for a specified time.
 * 
 * WHY?
 * JavaScript doesn't have a built-in sleep.
 * This is a simple Promise-based implementation.
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
 * EXAMPLE 1: Retry clicking a button
 * 
 *   import { withRetry } from './retry-handler';
 * 
 *   async function clickEditButton() {
 *     await withRetry(async () => {
 *       const button = document.querySelector('#edit-issue');
 *       if (!button) throw new Error('Edit button not found');
 *       (button as HTMLElement).click();
 *     }, {
 *       maxRetries: 3,
 *       onRetry: (attempt) => console.log(`Retrying click (${attempt})...`)
 *     });
 *   }
 * 
 * 
 * EXAMPLE 2: Wait for loading to finish
 * 
 *   import { retryUntil } from './retry-handler';
 * 
 *   async function waitForPageLoad() {
 *     const loaded = await retryUntil(
 *       () => document.querySelector('.loading') === null,
 *       { maxRetries: 30, initialDelayMs: 500 }
 *     );
 *     
 *     if (!loaded) {
 *       throw new Error('Page never finished loading');
 *     }
 *   }
 * 
 * 
 * EXAMPLE 3: Retry with custom shouldRetry logic
 * 
 *   await withRetry(async () => {
 *     const response = await fetch('/api/issues');
 *     if (!response.ok) throw new Error(`HTTP ${response.status}`);
 *     return response.json();
 *   }, {
 *     shouldRetry: (error) => {
 *       // Retry network errors and 5xx errors
 *       if (error.message.includes('Network')) return true;
 *       if (error.message.includes('500')) return true;
 *       
 *       // Don't retry 404 or permission errors
 *       if (error.message.includes('404')) return false;
 *       if (error.message.includes('403')) return false;
 *       
 *       return true;
 *     }
 *   });
 * 
 * 
 * EXAMPLE 4: Retry with progress reporting
 * 
 *   await withRetry(updateIssueField, {
 *     maxRetries: 5,
 *     onRetry: (attempt, error) => {
 *       // Send progress update to UI
 *       ipcRenderer.send('progress:update', {
 *         message: `Retry ${attempt}/5: ${error.message}`
 *       });
 *     }
 *   });
 */

/*
 * ============================================================================
 * DEVELOPER NOTES
 * ============================================================================
 * 
 * WHEN TO USE RETRY LOGIC:
 * 
 * ✅ Good use cases:
 *   - Network requests (transient failures)
 *   - Waiting for elements to appear (async page loading)
 *   - Clicking buttons (sometimes browser is busy)
 *   - Reading dynamic content (might load slowly)
 * 
 * ❌ Bad use cases:
 *   - Permission errors (retry won't help)
 *   - Invalid data (retry won't fix it)
 *   - Logic errors in your code (fix the code!)
 * 
 * 
 * CHOOSING RETRY PARAMETERS:
 * 
 * Fast operations (clicks, reads):
 *   maxRetries: 3
 *   initialDelayMs: 500
 *   backoffMultiplier: 2
 * 
 * Slow operations (page loads, API calls):
 *   maxRetries: 5
 *   initialDelayMs: 2000
 *   backoffMultiplier: 1.5
 * 
 * Very patient (dealing with very slow Jira):
 *   maxRetries: 10
 *   initialDelayMs: 3000
 *   backoffMultiplier: 1.5
 *   maxDelayMs: 60000  // Cap at 1 minute
 * 
 * 
 * DEBUGGING RETRY LOGIC:
 * 
 * If retries aren't working:
 * 1. Check console logs - are retries happening?
 * 2. Check shouldRetry - is it returning true?
 * 3. Check if maxRetries is high enough
 * 4. Check if delays are long enough
 * 5. Is the error actually retryable? (maybe it's a permanent failure)
 * 
 * 
 * PERFORMANCE CONSIDERATIONS:
 * 
 * - Each retry adds delay (1s + 2s + 4s = 7 seconds total)
 * - Too many retries = slow automation
 * - Too few retries = fails on temporary issues
 * - Balance based on how reliable your Jira instance is
 */
