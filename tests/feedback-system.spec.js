const { test, expect } = require('@playwright/test');

test.describe('Feedback System - Complete Flow', () => {
    let page;
    
    test.beforeEach(async ({ page: p }) => {
        page = p;
        await page.goto('http://localhost:5000');
        await page.waitForLoadState('networkidle');
    });

    test('1. Feedback button should be visible and clickable', async () => {
        const feedbackBtn = page.locator('#feedbackBtn');
        await expect(feedbackBtn).toBeVisible();
        await expect(feedbackBtn).toBeEnabled();
    });

    test('2. Clicking feedback button should open modal', async () => {
        await page.click('#feedbackBtn');
        const modal = page.locator('#feedback-modal');
        await expect(modal).toBeVisible();
        
        // Modal should have minimize button (−), NOT close (×)
        const minimizeBtn = page.locator('.modal-minimize');
        await expect(minimizeBtn).toBeVisible();
        await expect(minimizeBtn).toHaveText('−');
    });

    test('3. Minimize button should hide modal and show controller', async () => {
        // Open modal
        await page.click('#feedbackBtn');
        await page.waitForSelector('#feedback-modal', { state: 'visible' });
        
        // Click minimize
        await page.click('.modal-minimize');
        
        // Modal should be hidden
        const modal = page.locator('#feedback-modal');
        await expect(modal).toBeHidden();
        
        // Controller should be visible
        const controller = page.locator('#feedback-controller');
        await expect(controller).toBeVisible();
    });

    test('4. Restore button should bring modal back', async () => {
        // Open and minimize
        await page.click('#feedbackBtn');
        await page.click('.modal-minimize');
        
        // Click restore
        const restoreBtn = page.locator('#feedback-controller button[onclick="restoreFeedbackModal()"]');
        await expect(restoreBtn).toBeVisible();
        await restoreBtn.click();
        
        // Modal should be visible again
        const modal = page.locator('#feedback-modal');
        await expect(modal).toBeVisible();
        
        // Controller should be hidden
        const controller = page.locator('#feedback-controller');
        await expect(controller).toBeHidden();
    });

    test('5. Log checkbox should show visual confirmation', async () => {
        await page.click('#feedbackBtn');
        
        const checkbox = page.locator('#feedback-include-logs');
        const indicator = page.locator('#log-indicator');
        
        // Should be checked by default with green checkmark
        await expect(checkbox).toBeChecked();
        await expect(indicator).toBeVisible();
        await expect(indicator).toHaveText('✓ Logs will be included');
        await expect(indicator).toHaveCSS('color', 'rgb(0, 135, 90)'); // #00875a
        
        // Uncheck and verify red X
        await checkbox.uncheck();
        await expect(indicator).toHaveText('✗ Logs will not be included');
        await expect(indicator).toHaveCSS('color', 'rgb(222, 53, 11)'); // #de350b
    });

    test('6. Record button should show 60s duration', async () => {
        await page.click('#feedbackBtn');
        
        const recordBtn = page.locator('#record-video-btn');
        await expect(recordBtn).toHaveText('🎥 Record Video (60s)');
    });

    test('7. Cancel button should close modal and clear data', async () => {
        await page.click('#feedbackBtn');
        
        // Fill in some data
        await page.fill('#feedback-title', 'Test Title');
        await page.fill('#feedback-description', 'Test Description');
        
        // Click cancel
        const cancelBtn = page.locator('button:has-text("Cancel")');
        await cancelBtn.click();
        
        // Modal should be hidden
        const modal = page.locator('#feedback-modal');
        await expect(modal).toBeHidden();
        
        // Controller should be hidden
        const controller = page.locator('#feedback-controller');
        await expect(controller).toBeHidden();
        
        // Re-open and verify data is cleared
        await page.click('#feedbackBtn');
        const titleInput = page.locator('#feedback-title');
        const descInput = page.locator('#feedback-description');
        await expect(titleInput).toHaveValue('');
        await expect(descInput).toHaveValue('');
    });

    test('8. Submit without title/description should show error', async () => {
        await page.click('#feedbackBtn');
        
        // Try to submit empty form
        await page.click('#submit-feedback-btn');
        
        // Should show notification
        const notification = page.locator('#notification');
        await expect(notification).toBeVisible();
        await expect(notification).toContainText('title and description');
    });

    test('9. Controller should update when media is captured', async () => {
        await page.click('#feedbackBtn');
        await page.click('.modal-minimize');
        
        const controllerStatus = page.locator('#controller-attachments');
        await expect(controllerStatus).toHaveText('No media captured yet');
        
        // Note: We can't actually test screen capture without user interaction
        // But we verify the UI elements exist
        const screenshotBtn = page.locator('#feedback-controller button:has-text("📸")');
        const recordBtn = page.locator('#controller-record-btn');
        
        await expect(screenshotBtn).toBeVisible();
        await expect(recordBtn).toBeVisible();
    });

    test('10. Form validation - title and description required', async () => {
        await page.click('#feedbackBtn');
        
        const titleInput = page.locator('#feedback-title');
        const descInput = page.locator('#feedback-description');
        const submitBtn = page.locator('#submit-feedback-btn');
        
        await expect(titleInput).toHaveAttribute('placeholder', 'Brief description of the issue');
        await expect(descInput).toHaveAttribute('placeholder');
        
        // Submit button should be enabled (validation happens on click)
        await expect(submitBtn).toBeEnabled();
    });
});

test.describe('Feedback System - Visual Regression', () => {
    test('Modal appearance', async ({ page }) => {
        await page.goto('http://localhost:5000');
        await page.click('#feedbackBtn');
        await page.waitForSelector('#feedback-modal', { state: 'visible' });
        
        const modal = page.locator('#feedback-modal');
        await expect(modal).toHaveScreenshot('feedback-modal.png');
    });

    test('Floating controller appearance', async ({ page }) => {
        await page.goto('http://localhost:5000');
        await page.click('#feedbackBtn');
        await page.click('.modal-minimize');
        await page.waitForSelector('#feedback-controller', { state: 'visible' });
        
        const controller = page.locator('#feedback-controller');
        await expect(controller).toHaveScreenshot('feedback-controller.png');
    });
});
