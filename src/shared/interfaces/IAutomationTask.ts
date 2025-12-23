/*
 * ============================================================================
 * AUTOMATION TASK INTERFACE - Defines What Automation Jobs Look Like
 * ============================================================================
 * 
 * WHAT IS THIS FILE FOR?
 * ---------------------
 * This defines the "shape" of automation tasks in our app.
 * 
 * Think of it like a recipe card template:
 *   - Recipe Name: "Chocolate Cake"
 *   - Ingredients: [flour, sugar, eggs]
 *   - Instructions: [mix, bake, cool]
 * 
 * Similarly, an automation task has:
 *   - Task Name: "Update Due Dates"
 *   - Configuration: { daysBeforeFixVersion: 10 }
 *   - Enabled: true/false
 * 
 * 
 * WHY USE TYPESCRIPT INTERFACES?
 * ------------------------------
 * Without interfaces, you might pass wrong data:
 * 
 *   ❌ BAD:
 *   const task = {
 *     name: "Update Due Dates",
 *     daysBefore: 10,        // Oops! Wrong property name
 *     enable: true            // Should be "enabled"
 *   }
 * 
 *   ✅ GOOD (TypeScript catches errors):
 *   const task: IAutomationTask = {
 *     name: "Update Due Dates",
 *     daysBefore: 10,        // ❌ TypeScript error: Unknown property
 *     // Now you know to use the correct property names
 *   }
 */

/**
 * TaskType - The Different Kinds of Automation We Support
 * 
 * WHAT IS AN ENUM?
 * ----------------
 * An enum is like a menu at a restaurant - you can only order
 * items that are on the menu.
 * 
 * Instead of typing: type = "update_due_date" (easy to typo!)
 * You use: type = TaskType.UPDATE_DUE_DATE (no typos possible)
 * 
 * 
 * CURRENT TASK TYPES:
 * -------------------
 * UPDATE_DUE_DATE: Sets due date based on FixVersion date
 * LINK_PR: Associates pull requests with Jira issues
 * INJECT_PR_COMMENTS: Copies PR comments into Jira
 * BULK_TRANSITION: Moves multiple issues to new status (e.g., "In Progress")
 * UPDATE_FIELD: Changes any field value in bulk
 */
export enum TaskType {
  UPDATE_DUE_DATE = "update_due_date",
  LINK_PR = "link_pr",
  INJECT_PR_COMMENTS = "inject_pr_comments",
  BULK_TRANSITION = "bulk_transition",
  UPDATE_FIELD = "update_field"
}


/**
 * IAutomationTask - The Main Task Definition
 * 
 * EVERY automation task you create will have these properties.
 */
export interface IAutomationTask {
  /**
   * Unique identifier for this task
   * Example: "task_1234567890"
   * 
   * WHY: So we can track which task is running, stop specific tasks, etc.
   */
  id: string;
  
  /**
   * What kind of task is this?
   * Example: TaskType.UPDATE_DUE_DATE
   * 
   * WHY: The app needs to know which automation code to run
   */
  type: TaskType;
  
  /**
   * Human-readable name shown in UI
   * Example: "Set Due Dates for Release 2.0"
   * 
   * WHY: Users need to see what this task does without reading code
   */
  name: string;
  
  /**
   * Is this task active?
   * Example: true
   * 
   * WHY: Users might want to temporarily disable a task without deleting it
   */
  enabled: boolean;
  
  /**
   * Task-specific settings
   * Example: { daysBeforeFixVersion: 10, jqlQuery: "project = ABC" }
   * 
   * WHY: Different tasks need different settings - this holds them
   */
  config: ITaskConfig;
  
  /**
   * When should this task run automatically? (optional)
   * Example: { cronExpression: "0 9 * * MON" } = Every Monday at 9am
   * 
   * WHY: Users might want automation to run overnight or on schedules
   * 
   * NOTE: This is optional (marked with "?") - can be undefined
   */
  schedule?: IScheduleConfig;
}


/**
 * ITaskConfig - Base Configuration for ALL Tasks
 * 
 * WHAT IS THIS?
 * -------------
 * Every task needs to know WHICH issues to process.
 * This config provides two ways:
 *   1. JQL Query: "project = ABC AND status = 'To Do'"
 *   2. Structure URL: Direct link to a Jira Structure view
 * 
 * 
 * WHY [key: string]: any ?
 * ------------------------
 * Different task types need different extra fields.
 * 
 * For example:
 *   - Due Date task needs: daysBeforeFixVersion
 *   - PR Link task needs: githubRepoUrl
 * 
 * This [key: string]: any says "you can add any extra properties you want"
 * It's like a flexible form that can grow new fields.
 */
export interface ITaskConfig {
  /**
   * Jira Query Language query to find issues
   * Example: "project = MYPROJ AND fixVersion = '2.0'"
   * 
   * WHY: Users need to tell the app which issues to update
   * 
   * NOTE: Optional because user might use structureUrl instead
   */
  jqlQuery?: string;
  
  /**
   * Direct link to a Jira Structure board
   * Example: "https://company.atlassian.net/structure/123"
   * 
   * WHY: Some teams organize issues in Structure instead of JQL
   * 
   * NOTE: Optional because user might use jqlQuery instead
   */
  structureUrl?: string;
  
  /**
   * Allow any additional properties
   * 
   * EXAMPLES:
   *   config.daysBeforeFixVersion = 10;
   *   config.githubRepoUrl = "https://github.com/...";
   *   config.customFieldName = "Story Points";
   */
  [key: string]: any;
}


/**
 * IDueDateTaskConfig - Specific Config for Due Date Automation
 * 
 * WHAT DOES THIS TASK DO?
 * ------------------------
 * Sets the Due Date field to be X working days before the FixVersion release date.
 * 
 * EXAMPLE SCENARIO:
 *   - FixVersion "Release 2.0" is scheduled for Jan 31, 2025
 *   - daysBeforeFixVersion = 10
 *   - Result: Due Date set to Jan 17, 2025 (10 working days earlier)
 * 
 * WHY?
 *   - Teams want issues completed before the release
 *   - Buffer time for testing and bug fixes
 */
export interface IDueDateTaskConfig extends ITaskConfig {
  /**
   * How many days before the FixVersion release date?
   * Example: 10 means "due date is 10 days before release"
   * 
   * WHY: Different teams need different buffer times
   */
  daysBeforeFixVersion: number;
  
  /**
   * Should we skip weekends when counting days?
   * Example: true means 10 working days (Monday-Friday only)
   * 
   * WHY: Most teams don't work weekends, so counting calendar days is wrong
   */
  businessDaysOnly: boolean;
  
  /**
   * List of holidays to skip (ISO date strings)
   * Example: ["2025-12-25", "2025-01-01"] = Christmas and New Year
   * 
   * WHY: Different countries/companies have different holidays
   * 
   * NOTE: Optional - if not provided, only weekends are skipped
   */
  holidays?: string[];
}


/**
 * IPRLinkTaskConfig - Specific Config for Pull Request Linking
 * 
 * WHAT DOES THIS TASK DO?
 * ------------------------
 * Finds GitHub/GitLab pull requests and links them to Jira issues.
 * Then copies PR comments into Jira so the whole team can see them.
 * 
 * EXAMPLE SCENARIO:
 *   - Developer creates PR #456 in GitHub
 *   - PR description says "Fixes ABC-123"
 *   - This automation:
 *     1. Links PR to issue ABC-123
 *     2. Copies all PR comments into ABC-123's comment section
 * 
 * WHY?
 *   - Not everyone has GitHub access
 *   - Keeps all communication in one place (Jira)
 *   - Makes it easy to see what's being discussed
 */
export interface IPRLinkTaskConfig extends ITaskConfig {
  /**
   * Which GitHub repository to monitor?
   * Example: "https://github.com/mycompany/myproject"
   * 
   * WHY: App needs to know where to look for pull requests
   */
  githubRepoUrl: string;
  
  /**
   * What's the Jira custom field name for storing PR numbers?
   * Example: "Pull Request Number"
   * 
   * WHY: Different Jira instances use different custom field names
   * User needs to tell us which field to update
   */
  prNumberField: string;
  
  /**
   * Should we automatically copy PR comments to Jira?
   * Example: true
   * 
   * WHY: User might want to link PRs but not spam Jira with comments
   */
  autoCommentPRActivity: boolean;
}


/**
 * IScheduleConfig - When Should This Task Run Automatically?
 * 
 * WHAT IS THIS?
 * Some tasks should run on a schedule, like:
 *   - Every Monday morning
 *   - Once a day at midnight
 *   - First day of every month
 * 
 * This config defines the schedule using cron expressions.
 * Examples: "0 9 [asterisk] [asterisk] MON" = Every Monday at 9am
 */
export interface IScheduleConfig {
  /**
   * Cron expression defining when to run
   * Example: "0 9 * * MON" = Every Monday at 9am
   * 
   * WHY: Flexible way to define any schedule pattern
   */
  cronExpression: string;
  
  /**
   * Human-readable description of the schedule
   * Example: "Every Monday morning"
   * 
   * WHY: Users shouldn't need to understand cron expressions
   * This shows them in plain English what the schedule means
   */
  description: string;
}


/*
 * ============================================================================
 * HOW TO USE THESE INTERFACES
 * ============================================================================
 * 
 * CREATING A NEW DUE DATE TASK:
 * 
 *   const myTask: IAutomationTask = {
 *     id: "task_" + Date.now(),
 *     type: TaskType.UPDATE_DUE_DATE,
 *     name: "Set Due Dates for Q1 Release",
 *     enabled: true,
 *     config: {
 *       jqlQuery: "fixVersion = 'Q1 2025' AND duedate is EMPTY",
 *       daysBeforeFixVersion: 10,
 *       businessDaysOnly: true,
 *       holidays: ["2025-01-01"]
 *     } as IDueDateTaskConfig
 *   };
 * 
 * 
 * CREATING A PR LINK TASK:
 * 
 *   const prTask: IAutomationTask = {
 *     id: "task_" + Date.now(),
 *     type: TaskType.LINK_PR,
 *     name: "Link GitHub PRs",
 *     enabled: true,
 *     config: {
 *       jqlQuery: "project = ABC AND status = 'In Progress'",
 *       githubRepoUrl: "https://github.com/mycompany/myproject",
 *       prNumberField: "Pull Request Number",
 *       autoCommentPRActivity: true
 *     } as IPRLinkTaskConfig
 *   };
 * 
 * 
 * WITH A SCHEDULE:
 * 
 *   const scheduledTask: IAutomationTask = {
 *     id: "task_" + Date.now(),
 *     type: TaskType.UPDATE_DUE_DATE,
 *     name: "Weekly Due Date Sync",
 *     enabled: true,
 *     config: { ... },
 *     schedule: {
 *       cronExpression: "0 9 * * MON",
 *       description: "Every Monday at 9 AM"
 *     }
 *   };
 */
