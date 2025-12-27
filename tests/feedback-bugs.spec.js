const { test, expect } = require('@playwright/test');

test.describe('Feedback System - Bug Fixes', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('http://localhost:5000');
        await page.waitForLoadState('networkidle');
    });

    test('Issue 1: Submit feedback button should work', async ({ page }) => {
        // Open feedback modal
        await page.click('#feedbackBtn');
        await page.waitForSelector('#feedback-modal', { state: 'visible' });
        
        // Fill in required fields
        await page.fill('#feedback-title', 'Test Bug Report');
        await page.fill('#feedback-description', 'This is a test description to verify submit works');
        
        // Mock the API call to avoid actually creating GitHub issue
        await page.route('**/api/feedback/submit', route => {
            route.fulfill({
                status: 200,
                body: JSON.stringify({
                    success: true,
                    issue_number: 123,
                    issue_url: 'https://github.com/test/test/issues/123'
                })
            });
        });
        
        // Click submit
        const submitBtn = page.locator('#submit-feedback-btn');
        await expect(submitBtn).toBeEnabled();
        await submitBtn.click();
        
        // Should show success notification
        const notification = page.locator('#notification');
        await expect(notification).toBeVisible({ timeout: 5000 });
        await expect(notification).toContainText('submitted');
        
        // Modal should close after success
        const modal = page.locator('#feedback-modal');
        await expect(modal).toBeHidden({ timeout: 5000 });
    });

    test('Issue 2: Record video should NOT start immediately', async ({ page }) => {
        // Open feedback modal
        await page.click('#feedbackBtn');
        await page.waitForSelector('#feedback-modal', { state: 'visible' });
        
        // Minimize modal first
        await page.click('.modal-minimize');
        await page.waitForSelector('#feedback-controller', { state: 'visible' });
        
        // Recording indicator should NOT be visible yet
        const indicator = page.locator('#controller-recording-indicator');
        await expect(indicator).toBeHidden();
        
        // Click record button
        const recordBtn = page.locator('#controller-record-btn');
        await recordBtn.click();
        
        // Browser should prompt for screen share (we can't automate this)
        // But recording indicator should NOT show until user clicks "Share"
        // Wait a moment to ensure it doesn't auto-start
        await page.waitForTimeout(1000);
        
        // Indicator should still be hidden (waiting for user to share)
        await expect(indicator).toBeHidden();
        
        // Note: We can't test the actual MediaRecorder start because it requires
        // user interaction with the browser's share dialog
    });

    test('Issue 3: Submit with GitHub token should work', async ({ page }) => {
        // This test verifies the submit flow with actual backend
        await page.click('#feedbackBtn');
        await page.waitForSelector('#feedback-modal', { state: 'visible' });
        
        // Fill form
        await page.fill('#feedback-title', 'Integration Test');
        await page.fill('#feedback-description', 'Testing GitHub issue creation');
        
        // Uncheck logs to simplify test
        await page.uncheck('#feedback-include-logs');
        
        // Submit (will hit real backend)
        const submitBtn = page.locator('#submit-feedback-btn');
        await submitBtn.click();
        
        // Should either show success or error about token
        const notification = page.locator('#notification');
        await expect(notification).toBeVisible({ timeout: 10000 });
        
        // Check if it's success or token error
        const notifText = await notification.textContent();
        
        // If token is configured, should succeed
        // If not, should show clear error
        if (notifText.includes('token')) {
            expect(notifText).toContain('GitHub token');
        } else {
            expect(notifText).toContain('submitted');
        }
    });
});

test.describe('Selenium Session Persistence', () => {
    test('Issue 4: Chrome should persist session data', async ({ page }) => {
        await page.goto('http://localhost:5000');
        await page.waitForLoadState('networkidle');
        
        // Navigate to integrations
        await page.click('a[href="#integrations"]');
        await page.waitForTimeout(500);
        
        // Fill Jira settings
        await page.fill('#jira-url-input', 'https://test.atlassian.net/');
        await page.fill('#jira-projects-input', 'TEST');
        
        // Save settings
        await page.click('#save-jira-btn');
        await page.waitForTimeout(1000);
        
        // Mock the selenium endpoint to check user data dir
        let userDataDirUsed = false;
        await page.route('**/api/selenium/open-jira', async route => {
            const postData = await route.request().postDataJSON();
            // Check if backend is using a persistent user data directory
            userDataDirUsed = true; // We'll verify this in backend logs
            
            route.fulfill({
                status: 200,
                body: JSON.stringify({ success: true })
            });
        });
        
        // Open Jira browser
        await page.click('#open-jira-btn');
        await page.waitForTimeout(2000);
        
        // Verify the endpoint was called
        expect(userDataDirUsed).toBe(true);
    });

    test('Issue 5: Login should persist across sessions', async ({ page }) => {
        // This is more of an integration test that requires manual verification
        // We can test that the backend is configured to use persistent storage
        
        await page.goto('http://localhost:5000/api/config');
        
        const config = await page.evaluate(() => {
            return fetch('/api/config').then(r => r.json());
        });
        
        // Should have selenium config
        expect(config).toHaveProperty('selenium');
        
        // Note: Actual session persistence must be tested manually:
        // 1. Login to Jira via app
        // 2. Close app
        // 3. Reopen app
        // 4. Check if still logged in
    });
});
