/**
 * UI Refinements Test Suite
 * Tests for:
 * - Content centering
 * - Light/dark mode contrast
 * - Theme toggle placement in sidebar
 * - Removal of redundant header
 */

const { test, expect } = require('@playwright/test');

test.describe('UI Refinements', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('http://localhost:5000');
        await page.waitForLoadState('networkidle');
    });

    test('Content should be centered in viewport', async ({ page }) => {
        const content = page.locator('.content');
        await expect(content).toBeVisible();
        
        // Get content bounding box
        const contentBox = await content.boundingBox();
        const viewportSize = page.viewportSize();
        
        // Content should be centered (with sidebar offset)
        const sidebarWidth = 250;
        const availableWidth = viewportSize.width - sidebarWidth;
        const contentLeft = contentBox.x - sidebarWidth;
        
        // Content should have margin on both sides (centered)
        expect(contentLeft).toBeGreaterThan(0);
        expect(contentBox.x + contentBox.width).toBeLessThan(viewportSize.width);
    });

    test('Redundant page header should be removed', async ({ page }) => {
        // Old header element should not exist
        const header = page.locator('.header');
        await expect(header).toHaveCount(0);
        
        // Page title and subtitle elements should not exist
        const pageTitle = page.locator('#page-title');
        const pageSubtitle = page.locator('#page-subtitle');
        await expect(pageTitle).toHaveCount(0);
        await expect(pageSubtitle).toHaveCount(0);
    });

    test('Theme toggle should be in sidebar, not floating', async ({ page }) => {
        // New sidebar theme toggle should exist
        const sidebarToggle = page.locator('.theme-toggle-sidebar');
        await expect(sidebarToggle).toBeVisible();
        
        // Old floating toggle should not exist
        const floatingToggle = page.locator('.theme-toggle');
        await expect(floatingToggle).toHaveCount(0);
        
        // Theme toggle should be in sidebar
        const sidebar = page.locator('.sidebar');
        const toggleInSidebar = sidebar.locator('.theme-toggle-sidebar');
        await expect(toggleInSidebar).toBeVisible();
    });

    test('Theme toggle should show correct label', async ({ page }) => {
        const toggle = page.locator('.theme-toggle-sidebar');
        const label = toggle.locator('.theme-label');
        
        // Should show "Light Mode" by default
        await expect(label).toContainText('Light Mode');
        
        // Click to switch to dark mode
        await toggle.click();
        await page.waitForTimeout(300); // Animation
        
        // Should now show "Dark Mode"
        await expect(label).toContainText('Dark Mode');
    });

    test('Light mode should have good contrast', async ({ page }) => {
        // Ensure we're in light mode
        await page.evaluate(() => {
            document.documentElement.setAttribute('data-theme', 'light');
        });
        
        // Take screenshot of light mode
        await page.screenshot({ path: 'test-results/light-mode.png', fullPage: true });
        
        // Check stat cards are visible
        const statCards = page.locator('.stat-card');
        await expect(statCards.first()).toBeVisible();
        
        // Check text is not white on white (by checking computed styles)
        const statLabel = page.locator('.stat-label').first();
        const color = await statLabel.evaluate(el => window.getComputedStyle(el).color);
        
        // Color should be dark (rgb values should be low)
        expect(color).toMatch(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
        const matches = color.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
        const r = parseInt(matches[1]);
        const g = parseInt(matches[2]);
        const b = parseInt(matches[3]);
        
        // In light mode, text should be dark (values < 128)
        expect(r).toBeLessThan(128);
        expect(g).toBeLessThan(128);
        expect(b).toBeLessThan(128);
    });

    test('Dark mode should have good contrast', async ({ page }) => {
        // Switch to dark mode
        const toggle = page.locator('.theme-toggle-sidebar');
        await toggle.click();
        await page.waitForTimeout(300);
        
        // Take screenshot of dark mode
        await page.screenshot({ path: 'test-results/dark-mode.png', fullPage: true });
        
        // Check text is light on dark
        const statLabel = page.locator('.stat-label').first();
        const color = await statLabel.evaluate(el => window.getComputedStyle(el).color);
        
        const matches = color.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
        const r = parseInt(matches[1]);
        const g = parseInt(matches[2]);
        const b = parseInt(matches[3]);
        
        // In dark mode, text should be light (values > 128)
        expect(r).toBeGreaterThan(128);
        expect(g).toBeGreaterThan(128);
        expect(b).toBeGreaterThan(128);
    });

    test('All persona tabs should be accessible and properly styled', async ({ page }) => {
        const tabs = ['dashboard', 'po', 'dev', 'sm', 'rules', 'integrations', 'settings'];
        
        for (const tabName of tabs) {
            const navItem = page.locator(`[data-tab="${tabName}"]`);
            await navItem.click();
            await page.waitForTimeout(300); // Animation
            
            // Tab content should be visible
            const content = page.locator(`#${tabName}`);
            await expect(content).toBeVisible();
            
            // Nav item should be active
            await expect(navItem).toHaveClass(/active/);
            
            // Take screenshot
            await page.screenshot({ 
                path: `test-results/tab-${tabName}.png`,
                fullPage: true 
            });
        }
    });

    test('Theme toggle should work from any tab', async ({ page }) => {
        // Navigate to different tab
        await page.locator('[data-tab="rules"]').click();
        await page.waitForTimeout(300);
        
        // Theme toggle should still work
        const toggle = page.locator('.theme-toggle-sidebar');
        await toggle.click();
        await page.waitForTimeout(300);
        
        // Should be in dark mode
        const theme = await page.evaluate(() => 
            document.documentElement.getAttribute('data-theme')
        );
        expect(theme).toBe('dark');
    });

    test('Content max-width should be respected', async ({ page }) => {
        const content = page.locator('.content');
        const contentBox = await content.boundingBox();
        
        // Content should not exceed 1200px width
        expect(contentBox.width).toBeLessThanOrEqual(1200);
    });

    test('Visual regression - Dashboard light mode', async ({ page }) => {
        await page.evaluate(() => {
            document.documentElement.setAttribute('data-theme', 'light');
        });
        await page.screenshot({ 
            path: 'test-results/regression-dashboard-light.png',
            fullPage: true 
        });
    });

    test('Visual regression - Dashboard dark mode', async ({ page }) => {
        const toggle = page.locator('.theme-toggle-sidebar');
        await toggle.click();
        await page.waitForTimeout(300);
        await page.screenshot({ 
            path: 'test-results/regression-dashboard-dark.png',
            fullPage: true 
        });
    });
});
