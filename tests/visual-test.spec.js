const { test, expect } = require('@playwright/test');

test.describe('Visual Regression - Enhanced UI', () => {
  test('PO Tab - All States', async ({ page }) => {
    await page.goto('http://localhost:5000');
    await page.waitForLoadState('networkidle');
    
    // Navigate to PO tab
    await page.click('[data-tab="po"]');
    await page.waitForTimeout(500);
    
    // 1. Baseline screenshot
    await page.screenshot({ 
      path: 'test-results/po-tab-baseline.png',
      fullPage: true 
    });
    
    // 2. Team Mode Card Hover
    const teamModeCard = page.locator('.card').first();
    await teamModeCard.scrollIntoViewIfNeeded();
    await teamModeCard.hover();
    await page.waitForTimeout(400);
    await page.screenshot({ 
      path: 'test-results/team-mode-card-hover.png',
      fullPage: false 
    });
    
    // 3. Flow Metrics - Individual Stat Card Hovers
    const statCards = page.locator('#kanban-metrics .stat-card');
    
    // WIP Card
    await statCards.nth(0).scrollIntoViewIfNeeded();
    await statCards.nth(0).hover();
    await page.waitForTimeout(400);
    await page.screenshot({ 
      path: 'test-results/stat-card-wip-hover.png',
      fullPage: false 
    });
    
    // Cycle Time Card
    await statCards.nth(1).hover();
    await page.waitForTimeout(400);
    await page.screenshot({ 
      path: 'test-results/stat-card-cycletime-hover.png',
      fullPage: false 
    });
    
    // Throughput Card
    await statCards.nth(2).hover();
    await page.waitForTimeout(400);
    await page.screenshot({ 
      path: 'test-results/stat-card-throughput-hover.png',
      fullPage: false 
    });
    
    // Blocked Card
    await statCards.nth(3).hover();
    await page.waitForTimeout(400);
    await page.screenshot({ 
      path: 'test-results/stat-card-blocked-hover.png',
      fullPage: false 
    });
    
    // 4. Features Card Hover
    const featuresCard = page.locator('.card').filter({ hasText: 'Features & Epics' });
    await featuresCard.scrollIntoViewIfNeeded();
    await featuresCard.hover();
    await page.waitForTimeout(400);
    await page.screenshot({ 
      path: 'test-results/features-card-hover.png',
      fullPage: false 
    });
    
    // 5. Dependency Card Hover
    const depCard = page.locator('.card').filter({ hasText: 'Dependency Canvas' });
    await depCard.scrollIntoViewIfNeeded();
    await depCard.hover();
    await page.waitForTimeout(400);
    await page.screenshot({ 
      path: 'test-results/dependency-card-hover.png',
      fullPage: false 
    });
    
    // 6. Final full page after all interactions
    await page.screenshot({ 
      path: 'test-results/po-tab-final.png',
      fullPage: true 
    });
  });
  
  test('Dark Mode - PO Tab', async ({ page }) => {
    await page.goto('http://localhost:5000');
    await page.waitForLoadState('networkidle');
    
    // Toggle dark mode
    await page.click('#themeToggle');
    await page.waitForTimeout(500);
    
    // Navigate to PO tab
    await page.click('[data-tab="po"]');
    await page.waitForTimeout(500);
    
    // Dark mode baseline
    await page.screenshot({ 
      path: 'test-results/po-tab-dark-baseline.png',
      fullPage: true 
    });
    
    // Hover on stat card in dark mode
    const statCard = page.locator('.stat-card').first();
    await statCard.scrollIntoViewIfNeeded();
    await statCard.hover();
    await page.waitForTimeout(400);
    await page.screenshot({ 
      path: 'test-results/stat-card-dark-hover.png',
      fullPage: false 
    });
    
    // Card hover in dark mode
    const card = page.locator('.card').first();
    await card.scrollIntoViewIfNeeded();
    await card.hover();
    await page.waitForTimeout(400);
    await page.screenshot({ 
      path: 'test-results/card-dark-hover.png',
      fullPage: false 
    });
  });
  
  test('Dashboard - Enhanced Cards', async ({ page }) => {
    await page.goto('http://localhost:5000');
    await page.waitForLoadState('networkidle');
    
    // Dashboard baseline
    await page.screenshot({ 
      path: 'test-results/dashboard-baseline.png',
      fullPage: true 
    });
    
    // Hover on dashboard stat cards
    const statCards = page.locator('.stat-card');
    if (await statCards.count() > 0) {
      await statCards.nth(0).hover();
      await page.waitForTimeout(400);
      await page.screenshot({ 
        path: 'test-results/dashboard-stat-hover.png',
        fullPage: false 
      });
    }
  });
  
  test('Dev Tab - Enhanced Cards', async ({ page }) => {
    await page.goto('http://localhost:5000');
    await page.waitForLoadState('networkidle');
    
    await page.click('[data-tab="dev"]');
    await page.waitForTimeout(500);
    
    // Dev tab baseline
    await page.screenshot({ 
      path: 'test-results/dev-tab-baseline.png',
      fullPage: true 
    });
    
    // Hover on dev stat cards
    const statCard = page.locator('.stat-card').first();
    await statCard.scrollIntoViewIfNeeded();
    await statCard.hover();
    await page.waitForTimeout(400);
    await page.screenshot({ 
      path: 'test-results/dev-stat-hover.png',
      fullPage: false 
    });
  });
});
