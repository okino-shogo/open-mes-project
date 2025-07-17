const { test, expect } = require('@playwright/test');

test.describe('Open MES Basic Tests', () => {
  test('homepage loads correctly', async ({ page }) => {
    await page.goto('http://localhost:8000/');
    await expect(page).toHaveTitle(/みんなのMES/);
  });

  test('template rendering works without md5url errors', async ({ page }) => {
    // Listen for console errors
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // Listen for page errors
    const pageErrors = [];
    page.on('pageerror', error => {
      pageErrors.push(error.message);
    });

    await page.goto('http://localhost:8000/');
    await page.waitForLoadState('networkidle');
    
    // Verify no template errors occurred
    expect(consoleErrors.length).toBe(0);
    expect(pageErrors.length).toBe(0);
    
    // Verify page content loaded
    await expect(page.locator('body')).toBeVisible();
  });
});