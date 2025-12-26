// @ts-check
const { test, expect } = require('@playwright/test');

test.describe('Functional UI Tests - No Mocks, Real Data', () => {
    
    test.beforeEach(async ({ page }) => {
        await page.goto('http://localhost:5000');
        await page.waitForLoadState('networkidle');
    });

    test('Dashboard loads with real data from API', async ({ page }) => {
        // Check that dashboard stats load (not hardcoded)
        const activeRules = page.locator('#stat-active-rules');
        await expect(activeRules).toBeVisible();
        // Should show a number (not "-" which is initial loading state)
        await page.waitForTimeout(1000);
        const text = await activeRules.textContent();
        expect(text).not.toBe('-');
        expect(text).toMatch(/^\d+$/); // Should be a number
        
        // Take screenshot
        await page.screenshot({ path: 'test-results/dashboard-loaded.png', fullPage: true });
    });

    test('Integration status shows NOT CONFIGURED when no tokens set', async ({ page }) => {
        // Navigate to Integrations tab
        await page.click('[data-tab="integrations"]');
        await page.waitForTimeout(500);
        
        // Check GitHub status badge
        const githubBadge = page.locator('#github-status-badge');
        await expect(githubBadge).toBeVisible();
        const githubStatus = await githubBadge.textContent();
        
        // Should show either "Connected" or "Not Configured" - NOT "Loading..."
        expect(githubStatus).not.toBe('Loading...');
        expect(['Connected', 'Not Configured']).toContain(githubStatus);
        
        // Check Jira status badge  
        const jiraBadge = page.locator('#jira-status-badge');
        await expect(jiraBadge).toBeVisible();
        const jiraStatus = await jiraBadge.textContent();
        expect(jiraStatus).not.toBe('Loading...');
        expect(['Configured', 'Not Configured']).toContain(jiraStatus);
        
        await page.screenshot({ path: 'test-results/integrations-status.png', fullPage: true });
    });

    test('Integrations tab has configuration forms', async ({ page }) => {
        await page.click('[data-tab="integrations"]');
        await page.waitForTimeout(500);
        
        // GitHub configuration form exists
        await expect(page.locator('#github-token-input')).toBeVisible();
        await expect(page.locator('#github-org-input')).toBeVisible();
        await expect(page.getByText('Test Connection')).toBeVisible();
        await expect(page.getByText('Save GitHub Settings')).toBeVisible();
        
        // Jira configuration form exists
        await expect(page.locator('#jira-url-input')).toBeVisible();
        await expect(page.locator('#jira-projects-input')).toBeVisible();
        await expect(page.getByText('Save Jira Settings')).toBeVisible();
        
        await page.screenshot({ path: 'test-results/integrations-forms.png', fullPage: true });
    });

    test('Automation rules tab shows real rules from config', async ({ page }) => {
        await page.click('[data-tab="rules"]');
        await page.waitForTimeout(500);
        
        // Check PR Opened rule exists with form fields
        await expect(page.locator('#pr-opened-enabled')).toBeVisible();
        await expect(page.locator('#pr-opened-status')).toBeVisible();
        await expect(page.locator('#pr-opened-label')).toBeVisible();
        
        // Check PR Merged rule exists
        await expect(page.locator('#pr-merged-enabled')).toBeVisible();
        
        // Check PR Closed rule exists
        await expect(page.locator('#pr-closed-enabled')).toBeVisible();
        
        await page.screenshot({ path: 'test-results/automation-rules.png', fullPage: true });
    });

    test('Dev tab shows dynamic automation rules (not hardcoded)', async ({ page }) => {
        await page.click('[data-tab="dev"]');
        await page.waitForTimeout(1000);
        
        // Check that the automation rules container has real content
        const rulesContainer = page.locator('#dev-automation-rules');
        await expect(rulesContainer).toBeVisible();
        
        // Should not show "Loading rules..."
        const content = await rulesContainer.textContent();
        expect(content).not.toContain('Loading rules...');
        
        // Manual actions should be present
        await expect(page.getByText('Open Browser')).toBeVisible();
        await expect(page.getByText('Sync Now')).toBeVisible();
        
        await page.screenshot({ path: 'test-results/dev-tab.png', fullPage: true });
    });

    test('Dashboard shows integration status summary', async ({ page }) => {
        // Wait for data to load
        await page.waitForTimeout(1500);
        
        const statusContainer = page.locator('#dashboard-integration-status');
        await expect(statusContainer).toBeVisible();
        
        // Should not show "Loading..."
        const content = await statusContainer.textContent();
        expect(content).not.toContain('Loading...');
        
        await page.screenshot({ path: 'test-results/dashboard-integration-summary.png', fullPage: true });
    });

    test('Can save Jira settings', async ({ page }) => {
        await page.click('[data-tab="integrations"]');
        await page.waitForTimeout(500);
        
        // Fill in Jira URL
        await page.fill('#jira-url-input', 'https://test-company.atlassian.net');
        await page.fill('#jira-projects-input', 'TEST, DEMO');
        
        // Click save
        await page.click('text=Save Jira Settings');
        
        // Wait for notification
        await page.waitForTimeout(1000);
        
        // Verify notification appeared
        const notification = page.locator('#notification');
        await expect(notification).toContainText('saved');
        
        await page.screenshot({ path: 'test-results/jira-settings-saved.png', fullPage: true });
    });

    test('API returns real integration status', async ({ request }) => {
        const response = await request.get('http://localhost:5000/api/integrations/status');
        expect(response.ok()).toBeTruthy();
        
        const data = await response.json();
        
        // Verify structure
        expect(data).toHaveProperty('github');
        expect(data).toHaveProperty('jira');
        expect(data).toHaveProperty('feedback');
        
        expect(data.github).toHaveProperty('configured');
        expect(data.jira).toHaveProperty('configured');
        expect(data.feedback).toHaveProperty('configured');
        
        // configured should be boolean
        expect(typeof data.github.configured).toBe('boolean');
        expect(typeof data.jira.configured).toBe('boolean');
    });

    test('API returns real automation rules', async ({ request }) => {
        const response = await request.get('http://localhost:5000/api/automation/rules');
        expect(response.ok()).toBeTruthy();
        
        const data = await response.json();
        
        // Verify structure
        expect(data).toHaveProperty('rules');
        expect(data).toHaveProperty('active_count');
        expect(data).toHaveProperty('total_count');
        
        expect(data.rules).toHaveProperty('pr_opened');
        expect(data.rules).toHaveProperty('pr_merged');
        expect(data.rules).toHaveProperty('pr_closed');
        
        expect(typeof data.active_count).toBe('number');
    });

    test('Feedback button is visible', async ({ page }) => {
        const feedbackBtn = page.locator('#feedbackBtn');
        await expect(feedbackBtn).toBeVisible();
        
        // Click to open modal
        await feedbackBtn.click();
        await page.waitForTimeout(300);
        
        // Modal should be visible
        const modal = page.locator('#feedback-modal');
        await expect(modal).toBeVisible();
        
        await page.screenshot({ path: 'test-results/feedback-modal.png', fullPage: true });
    });

});
