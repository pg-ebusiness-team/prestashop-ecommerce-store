import { test, expect } from '@playwright/test';

test.describe('Koszyk', () => {
  test('dodanie 10 produktów, wyszukanie produktu i usunięcie 3 pozycji', async ({ page }) => {
    // Bez tych wpisów baner cookies i okno 18+ zasłaniają stronę (docs/adr/0002-baner-cookies.md)
    await page.addInitScript(() => {
      localStorage.setItem('cookie-consent', JSON.stringify({ analytics: false, marketing: false }));
      localStorage.setItem('age-confirmed', '1');
    });

    const licznik = page.locator('#_desktop_cart .cart-products-count');
    // zawężenie do formularza produktu: miniatury (np. „produkty powiązane”) mają własne przyciski o tej samej nazwie
    const przyciskDodaj = page.locator('.product-add-to-cart').getByRole('button', { name: 'Dodaj do koszyka' });
    const miniatury = page.locator('.js-product-miniature a.product-thumbnail');
    let sztuki = 0; // oczekiwana łączna liczba sztuk w koszyku

    // Dodaje otwarty produkt do koszyka; false = produkt niedostępny, nic nie dodano
    async function dodajDoKoszyka(ilosc: number): Promise<boolean> {
      await expect(przyciskDodaj).toBeVisible();
      if (await przyciskDodaj.isDisabled()) return false;
      await page.locator('#quantity_wanted').fill(String(ilosc));
      await przyciskDodaj.click();
      await expect(page.locator('#blockcart-modal')).toBeVisible();
      sztuki += ilosc;
      await expect(licznik).toHaveText(new RegExp(`\\b${sztuki}\\b`));
      return true;
    }

    let szukanaFraza = '';

    await test.step('Krok 1: 10 produktów w różnych ilościach z co najmniej 2 kategorii', async () => {
      await page.goto('/');
      const kategorie = await page
        .locator('#top-menu > li > a')
        .evaluateAll((linki) => linki.map((a) => (a as HTMLAnchorElement).href));

      const dodane = new Set<string>();
      let uzyteKategorie = 0;
      for (const kategoria of kategorie) {
        if (dodane.size === 10) break;
        await page.goto(kategoria);
        const produkty = await miniatury.evaluateAll((linki) => linki.map((a) => (a as HTMLAnchorElement).href));

        let zKategorii = 0;
        for (const produkt of produkty) {
          // najwyżej 5 z jednej kategorii, żeby na pewno były co najmniej 2 kategorie
          if (dodane.size === 10 || zKategorii === 5) break;
          if (dodane.has(produkt)) continue;
          await page.goto(produkt);
          if (!(await dodajDoKoszyka((dodane.size % 3) + 1))) continue;
          if (!szukanaFraza) {
            const nazwa = await page.locator('h1').first().innerText();
            // najdłuższe słowo nazwy - wyszukiwarka pomija słowa krótsze niż 3 znaki
            szukanaFraza = (nazwa.match(/\p{L}{3,}/gu) ?? [nazwa]).sort((a, b) => b.length - a.length)[0];
          }
          dodane.add(produkt);
          zKategorii++;
        }
        if (zKategorii > 0) uzyteKategorie++;
      }

      expect(dodane.size).toBe(10);
      expect(uzyteKategorie).toBeGreaterThanOrEqual(2);
    });

    await test.step('Krok 2: wyszukanie produktu po nazwie i dodanie losowego wyniku', async () => {
      await page.goto('/'); // zamyka okno potwierdzenia koszyka, które zasłania wyszukiwarkę
      const pole = page.getByRole('textbox', { name: 'Szukaj' });
      await pole.fill(szukanaFraza);
      await pole.press('Enter');
      await expect(page).toHaveURL(/szukaj/);
      await expect(miniatury.first()).toBeVisible();

      const wyniki = await miniatury.evaluateAll((linki) => linki.map((a) => (a as HTMLAnchorElement).href));
      const start = Math.floor(Math.random() * wyniki.length);
      let dodano = false;
      // od losowego wyniku w kółko, aż trafi się dostępny produkt
      for (let i = 0; i < wyniki.length; i++) {
        if( dodano ) break;
        await page.goto(wyniki[(start + i) % wyniki.length]);
        dodano = await dodajDoKoszyka(1);
      }
      expect(dodano).toBe(true);
    });

    await test.step('Krok 3: usunięcie 3 produktów z koszyka', async () => {
      await page.locator('#blockcart-modal').getByRole('link', { name: /Przejdź do realizacji zamówienia/i }).click();
      await expect(page).toHaveURL(/koszyk/);

      const pozycje = page.locator('.cart-item');
      const suma = page.locator('.cart-total .value');
      const liczbaPozycji = await pozycje.count();
      expect(liczbaPozycji).toBeGreaterThanOrEqual(10);

      for (let usuniete = 1; usuniete <= 3; usuniete++) {
        const sumaPrzed = await suma.innerText();
        const pierwsza = pozycje.first();
        sztuki -= Number(await pierwsza.locator('.js-cart-line-product-quantity').inputValue());
        await pierwsza.locator('.remove-from-cart').click();

        await expect(pozycje).toHaveCount(liczbaPozycji - usuniete);
        await expect(licznik).toHaveText(new RegExp(`\\b${sztuki}\\b`));
        await expect(suma).not.toHaveText(sumaPrzed);
      }
    });
  });
});
