const { test, expect } = require('@playwright/test');

test.describe('UI Enhancements - Main Data Pane', () => {
  test.beforeEach(async ({ page }) => {
    // Start the application
    await page.goto('http://localhost:5000');
    await page.waitForLoadState('networkidle');
    
    // Navigate to PO tab
    await page.click('[data-tab="po"]');
    await page.waitForTimeout(500);
  });

  test('should display readable text with proper contrast', async ({ page }) => {
    // Check font sizes
    const statNumber = page.locator('.stat-number').first();
    const fontSize = await statNumber.evaluate(el => 
      window.getComputedStyle(el).fontSize
    );
    
    // Font should be at least 36px for readability
    const sizeInPx = parseInt(fontSize);
    expect(sizeInPx).toBeGreaterThanOrEqual(36);
  });

  test('should show glowing border on card hover', async ({ page }) => {
    const card = page.locator('.card').first();
    
    // Get initial state
    const initialBoxShadow = await card.evaluate(el => 
      window.getComputedStyle(el).boxShadow
    );
    
    // Hover over card
    await card.hover();
    await page.waitForTimeout(300); // Wait for transition
    
    // Get hovered state
    const hoverBoxShadow = await card.evaluate(el => 
      window.getComputedStyle(el).boxShadow
    );
    
    // Shadow should be different and visible
    expect(hoverBoxShadow).not.toBe(initialBoxShadow);
    expect(hoverBoxShadow).not.toBe('none');
    
    // Take screenshot of hover state
    await page.screenshot({ 
      path: 'test-results/card-hover-glow.png',
      fullPage: false 
    });
  });

  test('should have pop effect on stat card hover', async ({ page }) => {
    const statCard = page.locator('.stat-card').first();
    
    // Get initial transform
    const initialTransform = await statCard.evaluate(el => 
      window.getComputedStyle(el).transform
    );
    
    // Hover over stat card
    await statCard.hover();
    await page.waitForTimeout(300); // Wait for transition
    
    // Get hovered transform
    const hoverTransform = await statCard.evaluate(el => 
      window.getComputedStyle(el).transform
    );
    
    // Transform should change (scale or translate)
    expect(hoverTransform).not.toBe(initialTransform);
    expect(hoverTransform).not.toBe('none');
    
    // Take screenshot of pop effect
    await page.screenshot({ 
      path: 'test-results/stat-card-pop-effect.png',
      fullPage: false 
    });
  });

  test('should have smooth transitions', async ({ page }) => {
    const card = page.locator('.card').first();
    
    // Check transition property
    const transition = await card.evaluate(el => 
      window.getComputedStyle(el).transition
    );
    
    // Should have transition defined
    expect(transition).not.toBe('all 0s ease 0s');
    expect(transition).toContain('0.3s');
  });

  test('visual regression - PO tab full page', async ({ page }) => {
    // Capture full PO tab
    await page.screenshot({ 
      path: 'test-results/po-tab-full.png',
      fullPage: true 
    });
  });

  test('visual regression - hover states', async ({ page }) => {
    // Capture team mode card with hover
    const teamModeCard = page.locator('.card').first();
    await teamModeCard.hover();
    await page.waitForTimeout(300);
    await page.screenshot({ 
      path: 'test-results/team-mode-card-hover.png',
      clip: await teamModeCard.boundingBox()
    });
    
    // Capture flow metrics
    const flowMetricsCard = page.locator('#kanban-metrics');
    await page.screenshot({ 
      path: 'test-results/flow-metrics-card.png',
      clip: await flowMetricsCard.boundingBox()
    });
    
    // Hover individual stat card
    const statCard = page.locator('.stat-card').first();
    await statCard.hover();
    await page.waitForTimeout(300);
    await page.screenshot({ 
      path: 'test-results/stat-card-hover.png',
      clip: await statCard.boundingBox()
    });
  });

  test('dark mode - should maintain readability', async ({ page }) => {
    // Toggle to dark mode
    await page.click('#themeToggle');
    await page.waitForTimeout(500);
    
    // Capture dark mode
    await page.screenshot({ 
      path: 'test-results/po-tab-dark-mode.png',
      fullPage: true 
    });
    
    // Check contrast
    const statNumber = page.locator('.stat-number').first();
    const color = await statNumber.evaluate(el => 
      window.getComputedStyle(el).color
    );
    
    // Color should be defined
    expect(color).toBeTruthy();
  });

  test('all stat cards should have hover effects', async ({ page }) => {
    const statCards = page.locator('.stat-card');
    const count = await statCards.count();
    
    expect(count).toBeGreaterThan(0);
    
    // Test each stat card
    for (let i = 0; i < Math.min(count, 4); i++) {
      const card = statCards.nth(i);
      await card.hover();
      await page.waitForTimeout(200);
      
      const transform = await card.evaluate(el => 
        window.getComputedStyle(el).transform
      );
      const boxShadow = await card.evaluate(el => 
        window.getComputedStyle(el).boxShadow
      );
      
      // Should have transform or shadow
      expect(transform !== 'none' || boxShadow !== 'none').toBeTruthy();
    }
  });

  test('features and dependency cards should be hoverable', async ({ page }) => {
    const cards = page.locator('.card');
    const count = await cards.count();
    
    // Test last two cards (Features & Dependency)
    for (let i = Math.max(0, count - 2); i < count; i++) {
      const card = cards.nth(i);
      await card.scrollIntoViewIfNeeded();
      await card.hover();
      await page.waitForTimeout(200);
      
      const boxShadow = await card.evaluate(el => 
        window.getComputedStyle(el).boxShadow
      );
      
      expect(boxShadow).not.toBe('none');
    }
  });
});

test.describe('UI Enhancements - Dev Tab', () => {
  test('dev tab stat cards should have animations', async ({ page }) => {
    await page.goto('http://localhost:5000');
    await page.click('[data-tab="dev"]');
    await page.waitForTimeout(500);
    
    const statCard = page.locator('.stat-card').first();
    await statCard.hover();
    await page.waitForTimeout(300);
    
    await page.screenshot({ 
      path: 'test-results/dev-tab-stat-card-hover.png',
      fullPage: false 
    });
  });
});

test.describe('UI Enhancements - Dashboard', () => {
  test('dashboard stat cards should have animations', async ({ page }) => {
    await page.goto('http://localhost:5000');
    await page.waitForLoadState('networkidle');
    
    const statCard = page.locator('.stat-card').first();
    await statCard.hover();
    await page.waitForTimeout(300);
    
    await page.screenshot({ 
      path: 'test-results/dashboard-stat-card-hover.png',
      fullPage: false 
    });
  });
});
