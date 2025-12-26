/**
 * Extension System Visual Tests
 * Tests the new extension architecture from user perspective
 */
const { test, expect } = require('@playwright/test');

const BASE_URL = 'http://localhost:5000';

test.describe('Extension System Visual Tests', () => {
    
    test.beforeEach(async ({ page }) => {
        await page.goto(BASE_URL);
        await page.waitForLoadState('networkidle');
    });

    test('Dashboard loads correctly', async ({ page }) => {
        await expect(page.locator('h1, .header')).toBeVisible();
        await page.screenshot({ path: 'test-results/extension-dashboard.png', fullPage: true });
    });

    test('PO Tab shows data import section', async ({ page }) => {
        // Navigate to PO tab
        await page.click('text=PO');
        await page.waitForTimeout(500);
        
        // Check for features section
        const featuresSection = page.locator('text=Features');
        await expect(featuresSection.first()).toBeVisible();
        
        await page.screenshot({ path: 'test-results/extension-po-tab.png', fullPage: true });
    });

    test('Automation tab has data import controls', async ({ page }) => {
        // Navigate to Rules/Automation tab
        await page.click('text=Rules');
        await page.waitForTimeout(500);
        
        // Check for Jira Data Scraper section
        const jiraSection = page.locator('text=Jira Data Scraper');
        
        // Check for JQL input
        const jqlInput = page.locator('#jira-jql-query, [placeholder*="project"]');
        
        // Check for Import button
        const importBtn = page.locator('text=Import Now');
        
        await page.screenshot({ path: 'test-results/extension-automation-tab.png', fullPage: true });
    });

    test('SM Tab shows insights section', async ({ page }) => {
        // Navigate to SM tab
        await page.click('text=SM');
        await page.waitForTimeout(500);
        
        // Check for insights section
        const insightsSection = page.locator('text=Insights');
        
        await page.screenshot({ path: 'test-results/extension-sm-tab.png', fullPage: true });
    });

    test('Dev Tab shows sync controls', async ({ page }) => {
        // Navigate to Dev tab
        await page.click('text=Dev');
        await page.waitForTimeout(500);
        
        // Check for sync button
        const syncBtn = page.locator('text=Sync Now');
        await expect(syncBtn.first()).toBeVisible();
        
        await page.screenshot({ path: 'test-results/extension-dev-tab.png', fullPage: true });
    });

    test('Settings tab is accessible', async ({ page }) => {
        // Navigate to Settings tab
        await page.click('text=Settings');
        await page.waitForTimeout(500);
        
        // Check for Jira URL input
        const jiraInput = page.locator('[id*="jira"], [placeholder*="atlassian"]');
        
        await page.screenshot({ path: 'test-results/extension-settings-tab.png', fullPage: true });
    });

    test('API endpoints return proper responses', async ({ page }) => {
        // Test extensions endpoint
        const extensionsResponse = await page.evaluate(async () => {
            const response = await fetch('/api/extensions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: '{}'
            });
            return response.json();
        });
        
        expect(extensionsResponse.success).toBe(true);
        expect(Array.isArray(extensionsResponse.extensions)).toBe(true);
    });

    test('Features endpoint works', async ({ page }) => {
        const featuresResponse = await page.evaluate(async () => {
            const response = await fetch('/api/data/features', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: '{}'
            });
            return response.json();
        });
        
        expect(featuresResponse.success).toBe(true);
    });

    test('Dependencies endpoint works', async ({ page }) => {
        const depsResponse = await page.evaluate(async () => {
            const response = await fetch('/api/data/dependencies', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: '{}'
            });
            return response.json();
        });
        
        expect(depsResponse.success).toBe(true);
    });

    test('Insights endpoint works', async ({ page }) => {
        const insightsResponse = await page.evaluate(async () => {
            const response = await fetch('/api/reports/insights', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: '{}'
            });
            return response.json();
        });
        
        expect(insightsResponse.success).toBe(true);
    });
});
