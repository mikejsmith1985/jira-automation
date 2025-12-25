const { test, expect } = require('@playwright/test');

test.describe('Automation Rules Configuration', () => {
  test.beforeEach(async ({ page }) => {
    // Start the application
    await page.goto('http://localhost:5000');
    await page.waitForLoadState('networkidle');
    
    // Navigate to Workflows tab
    await page.click('button:has-text("Workflows")');
    await page.waitForTimeout(500);
  });

  test('should display automation rules title', async ({ page }) => {
    const title = await page.locator('h2:has-text("Automation Rules")');
    await expect(title).toBeVisible();
  });

  test('should load PR Opened rules from config', async ({ page }) => {
    // Check that PR Opened section exists
    const prOpenedSection = await page.locator('h3:has-text("PR Opened/Created")');
    await expect(prOpenedSection).toBeVisible();
    
    // Check checkbox is loaded with config value
    const enabledCheckbox = await page.locator('#pr-opened-enabled');
    await expect(enabledCheckbox).toBeChecked(); // Should be true from config
    
    // Check status field has value from config
    const statusInput = await page.locator('#pr-opened-status');
    const statusValue = await statusInput.inputValue();
    expect(statusValue).toBe('In Review');
    
    // Check label field has value from config
    const labelInput = await page.locator('#pr-opened-label');
    const labelValue = await labelInput.inputValue();
    expect(labelValue).toBe('has-pr');
  });

  test('should load branch-specific merge rules from config', async ({ page }) => {
    // Wait for branch rules to load
    await page.waitForTimeout(1000);
    
    const branchRulesList = await page.locator('#branch-rules-list');
    await expect(branchRulesList).toBeVisible();
    
    // Check that DEV branch rule is loaded
    const devBranchInput = await page.locator('input[value="DEV"]');
    await expect(devBranchInput).toBeVisible();
    
    // Check that INT branch rule is loaded
    const intBranchInput = await page.locator('input[value="INT"]');
    await expect(intBranchInput).toBeVisible();
    
    // Check that PVS branch rule is loaded
    const pvsBranchInput = await page.locator('input[value="PVS"]');
    await expect(pvsBranchInput).toBeVisible();
    
    // Check that REL branch rule is loaded
    const relBranchInput = await page.locator('input[value="REL"]');
    await expect(relBranchInput).toBeVisible();
    
    // Check that PRD branch rule is loaded
    const prdBranchInput = await page.locator('input[value="PRD"]');
    await expect(prdBranchInput).toBeVisible();
  });

  test('should verify DEV rule has correct status', async ({ page }) => {
    await page.waitForTimeout(1000);
    
    // Find the DEV rule container
    const devRule = await page.locator('.branch-rule-item').filter({ hasText: 'DEV' }).first();
    
    // Check status value
    const statusInput = devRule.locator('input[placeholder="Ready for QA"]');
    const statusValue = await statusInput.inputValue();
    expect(statusValue).toBe('Ready for Testing');
  });

  test('should verify INT rule has correct status', async ({ page }) => {
    await page.waitForTimeout(1000);
    
    const intRule = await page.locator('.branch-rule-item').filter({ hasText: 'INT' }).first();
    const statusInput = intRule.locator('input[placeholder="Ready for QA"]');
    const statusValue = await statusInput.inputValue();
    expect(statusValue).toBe('Ready for QA');
  });

  test('should allow adding a new branch rule', async ({ page }) => {
    await page.waitForTimeout(1000);
    
    // Count existing rules
    const initialCount = await page.locator('.branch-rule-item').count();
    
    // Click Add Branch Rule button
    await page.click('button:has-text("Add Branch Rule")');
    await page.waitForTimeout(500);
    
    // Verify new rule was added
    const newCount = await page.locator('.branch-rule-item').count();
    expect(newCount).toBe(initialCount + 1);
  });

  test('should allow editing branch rule values', async ({ page }) => {
    await page.waitForTimeout(1000);
    
    // Find first branch rule
    const firstRule = await page.locator('.branch-rule-item').first();
    const statusInput = firstRule.locator('input[placeholder="Ready for QA"]');
    
    // Change the value
    await statusInput.fill('Testing Status');
    await page.waitForTimeout(500);
    
    // Verify value changed
    const newValue = await statusInput.inputValue();
    expect(newValue).toBe('Testing Status');
  });

  test('should allow deleting a branch rule', async ({ page }) => {
    await page.waitForTimeout(1000);
    
    // Count existing rules
    const initialCount = await page.locator('.branch-rule-item').count();
    
    if (initialCount > 0) {
      // Click delete button on first rule
      const deleteButton = await page.locator('.branch-rule-item').first().locator('button.btn-danger');
      await deleteButton.click();
      await page.waitForTimeout(500);
      
      // Verify rule was removed
      const newCount = await page.locator('.branch-rule-item').count();
      expect(newCount).toBe(initialCount - 1);
    }
  });

  test('should load PR Closed rules from config', async ({ page }) => {
    const prClosedSection = await page.locator('h3:has-text("PR Closed")');
    await expect(prClosedSection).toBeVisible();
    
    const enabledCheckbox = await page.locator('#pr-closed-enabled');
    await expect(enabledCheckbox).toBeChecked();
    
    const labelInput = await page.locator('#pr-closed-label');
    const labelValue = await labelInput.inputValue();
    expect(labelValue).toBe('pr-closed');
  });

  test('should take screenshot of loaded automation rules', async ({ page }) => {
    await page.waitForTimeout(1500);
    await page.screenshot({ 
      path: 'tests/screenshots/automation-rules-loaded.png',
      fullPage: true 
    });
  });
});
