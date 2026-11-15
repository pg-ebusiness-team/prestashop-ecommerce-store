import { test, expect } from '@playwright/test';

// Test dymny: sprawdza tylko, że konfiguracja działa i sklep odpowiada.
test('strona główna się ładuje', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/.+/);
});
