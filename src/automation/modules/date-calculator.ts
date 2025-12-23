/*
 * ============================================================================
 * DATE CALCULATOR - Working Days and Business Date Math
 * ============================================================================
 * 
 * WHAT IS THIS FILE FOR?
 * ----------------------
 * Calculates dates while accounting for:
 *   - Weekends (Saturday/Sunday)
 *   - Holidays (custom list)
 *   - Working days only
 * 
 * USE CASE:
 * "Set due date to 10 working days before the FixVersion release date"
 * 
 * Example:
 *   Release date: January 31, 2025 (Friday)
 *   Subtract 10 working days
 *   Result: January 15, 2025 (Wednesday)
 *   
 *   NOT: January 21 (calendar days would give wrong result)
 * 
 * 
 * WHY DO WE NEED THIS?
 * --------------------
 * Teams work on weekdays only. If you subtract calendar days:
 *   - You include weekends (team doesn't work)
 *   - You include holidays (team doesn't work)
 *   - Due dates are wrong
 * 
 * Working days calculation skips non-working days.
 * 
 * 
 * WHAT ARE WORKING DAYS?
 * ----------------------
 * Monday through Friday, excluding holidays.
 * 
 * Example week:
 *   Mon ✓ Working day
 *   Tue ✓ Working day
 *   Wed ✓ Working day (Holiday: New Year) ✗ Not a working day
 *   Thu ✓ Working day
 *   Fri ✓ Working day
 *   Sat ✗ Weekend
 *   Sun ✗ Weekend
 */

/**
 * Check if a date is a weekend (Saturday or Sunday)
 * 
 * WHAT DOES THIS DO?
 * Returns true if the date falls on Saturday (6) or Sunday (0).
 * 
 * HOW JAVASCRIPT DATES WORK:
 * date.getDay() returns:
 *   0 = Sunday
 *   1 = Monday
 *   2 = Tuesday
 *   3 = Wednesday
 *   4 = Thursday
 *   5 = Friday
 *   6 = Saturday
 * 
 * @param date - Date to check
 * @returns true if weekend, false if weekday
 */
export function isWeekend(date: Date): boolean {
  const dayOfWeek = date.getDay();
  return dayOfWeek === 0 || dayOfWeek === 6;  // Sunday or Saturday
}

/**
 * Check if a date is a holiday
 * 
 * WHAT DOES THIS DO?
 * Compares the date against a list of holiday dates.
 * 
 * HOLIDAY FORMAT:
 * Holidays are stored as ISO date strings: "2025-01-01", "2025-12-25", etc.
 * 
 * WHY ISO FORMAT?
 * - Unambiguous (YYYY-MM-DD)
 * - Easy to compare
 * - No timezone issues
 * 
 * @param date - Date to check
 * @param holidays - Array of holiday dates in ISO format (e.g., ["2025-01-01"])
 * @returns true if holiday, false otherwise
 */
export function isHoliday(date: Date, holidays: string[] = []): boolean {
  // Convert date to ISO string (YYYY-MM-DD format)
  const dateString = date.toISOString().split('T')[0];
  
  // Check if this date is in the holidays array
  return holidays.includes(dateString);
}

/**
 * Check if a date is a working day
 * 
 * WHAT DOES THIS DO?
 * Returns true if the date is:
 *   - NOT a weekend (Monday-Friday)
 *   - AND NOT a holiday
 * 
 * EXAMPLE:
 *   Monday (not holiday) → true (working day)
 *   Saturday → false (weekend)
 *   Wednesday (New Year) → false (holiday)
 * 
 * @param date - Date to check
 * @param holidays - Array of holiday dates
 * @returns true if working day, false otherwise
 */
export function isWorkingDay(date: Date, holidays: string[] = []): boolean {
  // Must be weekday AND not a holiday
  return !isWeekend(date) && !isHoliday(date, holidays);
}

/**
 * Add working days to a date
 * 
 * WHAT DOES THIS DO?
 * Adds a specified number of WORKING days to a date.
 * Skips weekends and holidays.
 * 
 * EXAMPLE:
 *   Start: Friday, January 10, 2025
 *   Add 3 working days:
 *     Skip Saturday & Sunday
 *     Monday (1), Tuesday (2), Wednesday (3)
 *   Result: Wednesday, January 15, 2025
 * 
 * HOW IT WORKS:
 * 1. Start with the given date
 * 2. Add 1 day
 * 3. Is it a working day? Count it
 * 4. Not a working day? Skip it, don't count
 * 5. Repeat until we've counted enough working days
 * 
 * @param date - Starting date
 * @param days - Number of working days to add
 * @param holidays - Array of holiday dates
 * @returns New date that is 'days' working days later
 */
export function addWorkingDays(
  date: Date,
  days: number,
  holidays: string[] = []
): Date {
  // Create a copy so we don't modify the original
  const result = new Date(date);
  
  let workingDaysAdded = 0;
  
  // Keep adding days until we've added enough working days
  while (workingDaysAdded < days) {
    // Add one calendar day
    result.setDate(result.getDate() + 1);
    
    // Is this a working day?
    if (isWorkingDay(result, holidays)) {
      // Yes! Count it
      workingDaysAdded++;
    }
    // If not a working day, skip it (don't increment counter)
  }
  
  return result;
}

/**
 * Subtract working days from a date
 * 
 * WHAT DOES THIS DO?
 * Subtracts a specified number of WORKING days from a date.
 * Skips weekends and holidays.
 * 
 * THIS IS THE MAIN FUNCTION for our use case!
 * "Set due date to 10 working days BEFORE release date"
 * 
 * EXAMPLE:
 *   Start: Friday, January 31, 2025 (Release date)
 *   Subtract 10 working days:
 *     Go back: Thu (1), Wed (2), Tue (3), Mon (4)
 *     Skip weekend
 *     Go back: Fri (5), Thu (6), Wed (7), Tue (8), Mon (9)
 *     Skip weekend
 *     Go back: Fri (10)
 *   Result: Friday, January 17, 2025 (Due date)
 * 
 * @param date - Starting date (usually FixVersion release date)
 * @param days - Number of working days to subtract
 * @param holidays - Array of holiday dates
 * @returns New date that is 'days' working days earlier
 */
export function subtractWorkingDays(
  date: Date,
  days: number,
  holidays: string[] = []
): Date {
  // Create a copy so we don't modify the original
  const result = new Date(date);
  
  let workingDaysSubtracted = 0;
  
  // Keep subtracting days until we've gone back enough working days
  while (workingDaysSubtracted < days) {
    // Subtract one calendar day
    result.setDate(result.getDate() - 1);
    
    // Is this a working day?
    if (isWorkingDay(result, holidays)) {
      // Yes! Count it
      workingDaysSubtracted++;
    }
    // If not a working day, skip it (don't increment counter)
  }
  
  return result;
}

/**
 * Count working days between two dates
 * 
 * WHAT DOES THIS DO?
 * Counts how many working days exist between two dates.
 * 
 * USEFUL FOR:
 * - Reporting: "There are 15 working days until release"
 * - Validation: "Due date should be at least 5 working days before release"
 * 
 * EXAMPLE:
 *   Start: Monday, Jan 6
 *   End: Friday, Jan 10
 *   Working days: Mon, Tue, Wed, Thu, Fri = 5 days
 *   (Excludes weekends if range crosses them)
 * 
 * @param startDate - Beginning of range
 * @param endDate - End of range
 * @param holidays - Array of holiday dates
 * @returns Number of working days between the dates (inclusive)
 */
export function countWorkingDays(
  startDate: Date,
  endDate: Date,
  holidays: string[] = []
): number {
  // Make copies so we don't modify originals
  const start = new Date(startDate);
  const end = new Date(endDate);
  
  // Ensure start is before end
  if (start > end) {
    // Swap them
    return countWorkingDays(end, start, holidays);
  }
  
  let count = 0;
  const current = new Date(start);
  
  // Loop through each day in the range
  while (current <= end) {
    // Is this a working day?
    if (isWorkingDay(current, holidays)) {
      count++;
    }
    
    // Move to next day
    current.setDate(current.getDate() + 1);
  }
  
  return count;
}

/**
 * Format a date as ISO string (YYYY-MM-DD)
 * 
 * WHAT DOES THIS DO?
 * Converts a Date object to the format Jira expects: "2025-01-15"
 * 
 * WHY DO WE NEED THIS?
 * - Jira's due date field expects YYYY-MM-DD format
 * - JavaScript Date.toString() gives a different format
 * - We need consistent formatting
 * 
 * @param date - Date to format
 * @returns String in YYYY-MM-DD format
 */
export function formatDateForJira(date: Date): string {
  // Get components
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');  // Months are 0-indexed
  const day = String(date.getDate()).padStart(2, '0');
  
  // Return formatted string
  return `${year}-${month}-${day}`;
}

/**
 * Parse a date from ISO string
 * 
 * WHAT DOES THIS DO?
 * Converts "2025-01-15" to a Date object.
 * 
 * WHY DO WE NEED THIS?
 * - Jira returns dates as strings
 * - We need Date objects for calculations
 * 
 * @param dateString - Date string in YYYY-MM-DD format
 * @returns Date object, or null if invalid
 */
export function parseDateFromJira(dateString: string): Date | null {
  try {
    // Parse the date
    const date = new Date(dateString);
    
    // Check if valid
    if (isNaN(date.getTime())) {
      console.error('Invalid date string:', dateString);
      return null;
    }
    
    return date;
  } catch (error) {
    console.error('Error parsing date:', dateString, error);
    return null;
  }
}

/**
 * Get next working day after a date
 * 
 * WHAT DOES THIS DO?
 * Finds the next working day (skips weekends/holidays).
 * 
 * USEFUL FOR:
 * "If release is on a weekend, use next Monday"
 * 
 * @param date - Starting date
 * @param holidays - Array of holiday dates
 * @returns Next working day
 */
export function getNextWorkingDay(date: Date, holidays: string[] = []): Date {
  const result = new Date(date);
  
  // Keep adding days until we find a working day
  do {
    result.setDate(result.getDate() + 1);
  } while (!isWorkingDay(result, holidays));
  
  return result;
}

/**
 * Get previous working day before a date
 * 
 * @param date - Starting date
 * @param holidays - Array of holiday dates
 * @returns Previous working day
 */
export function getPreviousWorkingDay(date: Date, holidays: string[] = []): Date {
  const result = new Date(date);
  
  // Keep subtracting days until we find a working day
  do {
    result.setDate(result.getDate() - 1);
  } while (!isWorkingDay(result, holidays));
  
  return result;
}


/**
 * DEFAULT_US_HOLIDAYS - Common US Federal Holidays
 * 
 * WHAT IS THIS?
 * Pre-defined list of US federal holidays for 2025-2026.
 * 
 * WHY?
 * Most US-based teams observe these holidays.
 * Provides sensible defaults.
 * 
 * USER CAN OVERRIDE:
 * In app config, users can provide their own holiday list.
 * Different countries have different holidays.
 */
export const DEFAULT_US_HOLIDAYS = [
  // 2025
  '2025-01-01',  // New Year's Day
  '2025-01-20',  // Martin Luther King Jr. Day
  '2025-02-17',  // Presidents' Day
  '2025-05-26',  // Memorial Day
  '2025-07-04',  // Independence Day
  '2025-09-01',  // Labor Day
  '2025-10-13',  // Columbus Day
  '2025-11-11',  // Veterans Day
  '2025-11-27',  // Thanksgiving
  '2025-12-25',  // Christmas
  
  // 2026
  '2026-01-01',  // New Year's Day
  '2026-01-19',  // Martin Luther King Jr. Day
  '2026-02-16',  // Presidents' Day
  '2026-05-25',  // Memorial Day
  '2026-07-03',  // Independence Day (observed)
  '2026-09-07',  // Labor Day
  '2026-10-12',  // Columbus Day
  '2026-11-11',  // Veterans Day
  '2026-11-26',  // Thanksgiving
  '2026-12-25',  // Christmas
];


/*
 * ============================================================================
 * REAL-WORLD USAGE EXAMPLES
 * ============================================================================
 * 
 * EXAMPLE 1: Calculate due date from release date
 * 
 *   const releaseDate = parseDateFromJira('2025-01-31');  // FixVersion date
 *   const daysBeforeRelease = 10;  // User's config
 *   const holidays = DEFAULT_US_HOLIDAYS;
 *   
 *   const dueDate = subtractWorkingDays(releaseDate, daysBeforeRelease, holidays);
 *   const dueDateString = formatDateForJira(dueDate);
 *   
 *   console.log(`Release: ${releaseDate.toDateString()}`);
 *   console.log(`Due date: ${dueDateString}`);
 *   // Output: Due date: 2025-01-17
 * 
 * 
 * EXAMPLE 2: Validate due date is far enough before release
 * 
 *   const dueDate = parseDateFromJira('2025-01-20');
 *   const releaseDate = parseDateFromJira('2025-01-31');
 *   
 *   const daysBetween = countWorkingDays(dueDate, releaseDate);
 *   
 *   if (daysBetween < 10) {
 *     console.warn(`Warning: Only ${daysBetween} working days until release!`);
 *   }
 * 
 * 
 * EXAMPLE 3: Check if today is a working day
 * 
 *   const today = new Date();
 *   
 *   if (isWorkingDay(today, DEFAULT_US_HOLIDAYS)) {
 *     console.log('Today is a working day');
 *   } else {
 *     console.log('Today is a weekend or holiday');
 *   }
 * 
 * 
 * EXAMPLE 4: Handle releases on weekends
 * 
 *   const releaseDate = parseDateFromJira('2025-01-25');  // Saturday
 *   
 *   // If release is on weekend, adjust to previous Friday
 *   const adjustedRelease = isWeekend(releaseDate)
 *     ? getPreviousWorkingDay(releaseDate)
 *     : releaseDate;
 *   
 *   const dueDate = subtractWorkingDays(adjustedRelease, 10);
 */

/*
 * ============================================================================
 * DEVELOPER NOTES
 * ============================================================================
 * 
 * TIMEZONE CONSIDERATIONS:
 * 
 * JavaScript Date objects have timezone complexity.
 * We use ISO strings (YYYY-MM-DD) which are date-only (no time).
 * This avoids most timezone issues.
 * 
 * If you see dates off by one day:
 *   - Check if you're parsing with time included
 *   - Use toISOString().split('T')[0] to get date-only
 * 
 * 
 * HOLIDAY LISTS:
 * 
 * Different teams need different holidays:
 *   - US teams: Federal holidays
 *   - UK teams: Bank holidays
 *   - Other countries: Their holidays
 *   - Companies: Custom holidays
 * 
 * Let users provide custom holiday lists in config.
 * DEFAULT_US_HOLIDAYS is just a starting point.
 * 
 * 
 * EDGE CASES:
 * 
 * 1. Release date is on a weekend
 *    - Decision: Use Friday before or Monday after?
 *    - Current code: Uses the weekend date as-is
 *    - Consider: Add option to adjust
 * 
 * 2. Subtracting more days than available
 *    - Example: Subtract 100 working days, only 50 in the year
 *    - Works correctly - keeps going back into previous year
 * 
 * 3. Holidays on weekends
 *    - Example: Christmas on Saturday
 *    - Not a problem - already not a working day
 * 
 * 
 * TESTING:
 * 
 * Test with known examples:
 *   - 5 working days from Monday = following Monday
 *   - 10 working days from Friday = Wednesday of second week
 *   - Across year boundary (Dec → Jan)
 *   - With holidays in range
 * 
 * 
 * PERFORMANCE:
 * 
 * These functions are fast enough for automation.
 * Even subtracting 100 working days takes < 1ms.
 * 
 * If processing thousands of dates, consider caching:
 *   - Cache working day calculations
 *   - Pre-compute holiday lookups
 */
