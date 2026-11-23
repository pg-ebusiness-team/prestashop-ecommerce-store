import {test} from "@playwright/test";

test.describe('Koszyk', () => {
    test('dodanie 10 produktów, wyszukanie produktu i usunięcie 3 pozycji', async ({ page }) => {
        // Bez tych wpisów baner cookies i okno 18+ zasłaniają stronę (docs/adr/0002-baner-cookies.md)
        await page.addInitScript(() => {
            localStorage.setItem('cookie-consent', JSON.stringify({analytics: false, marketing: false}));
            localStorage.setItem('age-confirmed', '1');
        });
    })
})