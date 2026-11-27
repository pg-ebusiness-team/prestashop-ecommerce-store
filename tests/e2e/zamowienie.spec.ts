import { test, expect } from '@playwright/test';

// Scenariusz W4 z docs/WYMAGANIA.md: kroki idą po kolei w jednej sesji przeglądarki, bo zamówienie składamy
// na koszyk z kroków 1-3, a kroki 9-10 sprawdzają zamówienie z kroku 8.
test.describe('Scenariusz zamówienia', () => {
  test('koszyk, rejestracja, zamówienie z płatnością przy odbiorze', async ({ page }) => {
    test.setTimeout(300_000); // W4: cały scenariusz ma się zmieścić w 5 min
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
      const pole = page.locator('#quantity_wanted');
      if ((await pole.inputValue()) !== String(ilosc)) {
        const odswiezenie = page.waitForResponse((r) => r.request().postData()?.includes('action=refresh') ?? false);
        await pole.fill(String(ilosc));
        await pole.press('End'); // sklep sprawdza stan dopiero po keyup, samo fill go nie wywołuje
        // odpowiedź zawiera nowy HTML przycisku; disabled = stan nie wystarcza na tę ilość
        const { product_add_to_cart: przycisk } = await (await odswiezenie).json();
        if (/\sdisabled/.test(przycisk)) return false;
      }
      await przyciskDodaj.click();
      await expect(page.locator('#blockcart-modal')).toBeVisible();
      sztuki += ilosc;
      await expect(licznik).toHaveText(new RegExp(`\\b${sztuki}\\b`));
      return true;
    }

    let szukanaFraza = '';
    // stan koszyka po kroku 3 - krok 5 sprawdza, że zamówienie dotyczy tej samej zawartości
    let pozycjeWKoszyku = 0;
    let kwotaProduktow = '';

    // Nowy klient przy każdym uruchomieniu. Prefiks e2e+ odróżnia zamówienia testowe w panelu i w Mailpicie
    // (etap 2, W4: zamówienia testowe rozpoznawalne). Imiona z polskimi znakami - sklep musi je poprawnie zapisać.
    const losuj = <T,>(lista: T[]) => lista[Math.floor(Math.random() * lista.length)];
    // imię i nazwisko z list tej samej płci, żeby nie powstało np. „Jędrzej Żółkiewska”
    const plec = losuj([
      { zwrot: 'Pani', imiona: ['Łucja', 'Małgorzata', 'Zofia'], nazwiska: ['Żółkiewska', 'Wiśniewska', 'Śliwińska'] },
      { zwrot: 'Pan', imiona: ['Jędrzej', 'Mikołaj', 'Józef'], nazwiska: ['Żółkiewski', 'Wiśniewski', 'Głowacki'] },
    ]);
    const klient = {
      zwrot: plec.zwrot,
      imie: losuj(plec.imiona),
      nazwisko: losuj(plec.nazwiska),
      email: `e2e+${Date.now()}@example.com`,
      // litery, cyfry i znak specjalny - spełnia politykę siły hasła PrestaShop
      haslo: `E2e!${Math.random().toString(36).slice(2, 10)}#Qx9`,
    };

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

      pozycjeWKoszyku = liczbaPozycji - 3;
      // textContent, bo innerText zwraca tekst po CSS text-transform („ZŁ” w koszyku, „zł” w podsumowaniu zamówienia)
      kwotaProduktow = ((await page.locator('#cart-subtotal-products .value').textContent()) ?? '').trim();
    });

    await test.step('Krok 4: rejestracja nowego konta', async () => {
      await page.locator('#_desktop_user_info').getByRole('link', { name: /Zaloguj się/i }).click();
      await page.getByRole('link', { name: /Załóż je tutaj/i }).click();
      await expect(page).toHaveURL(/rejestracja/);

      const formularz = page.locator('#customer-form');
      await formularz.getByRole('radio', { name: klient.zwrot, exact: true }).check();
      await formularz.locator('[name=firstname]').fill(klient.imie);
      await formularz.locator('[name=lastname]').fill(klient.nazwisko);
      await formularz.locator('[name=email]').fill(klient.email);
      await formularz.locator('[name=password]').fill(klient.haslo);
      // wymagane zgody: regulamin z polityką prywatności (psgdpr) i informacja o przetwarzaniu danych
      await formularz.locator('[name=psgdpr]').check();
      await formularz.locator('[name=customer_privacy]').check();
      await formularz.getByRole('button', { name: /Zapisz/i }).click();

      // po udanej rejestracji sklep od razu loguje klienta i opuszcza formularz
      await expect(page).not.toHaveURL(/rejestracja/);
      const naglowek = page.locator('#_desktop_user_info');
      await expect(naglowek).toContainText(`${klient.imie} ${klient.nazwisko}`);
      await expect(naglowek.getByRole('link', { name: /Wyloguj/i })).toBeVisible();
      // koszyk gościa przechodzi na nowe konto - bez tego krok 5 nie miałby czego zamówić
      await expect(licznik).toHaveText(new RegExp(`\\b${sztuki}\\b`));
    });

    // kroki zamówienia na /zamowienie; aktywny ma klasę -current, zaliczony -complete
    const krokDane = page.locator('#checkout-personal-information-step');
    const krokAdres = page.locator('#checkout-addresses-step');
    const krokDostawa = page.locator('#checkout-delivery-step');
    const krokPlatnosc = page.locator('#checkout-payment-step');

    await test.step('Krok 5: złożenie zamówienia na zawartość koszyka', async () => {
      await page.locator('#_desktop_cart a').click();
      await expect(page).toHaveURL(/koszyk/);
      await page.getByRole('link', { name: /Przejdź do realizacji zamówienia/i }).click();
      await expect(page).toHaveURL(/zamowienie/);

      // zamówienie obejmuje dokładnie koszyk z kroków 1-3: te same pozycje, sztuki i kwota produktów
      const podsumowanie = page.locator('#js-checkout-summary');
      await expect(podsumowanie.locator('#cart-summary-product-list .media')).toHaveCount(pozycjeWKoszyku);
      await expect(podsumowanie.locator('.cart-summary-products')).toContainText(new RegExp(`\\b${sztuki} szt`));
      await expect(podsumowanie.locator('#cart-subtotal-products .value')).toHaveText(kwotaProduktow);

      // klient zalogowany w kroku 4, więc dane osobowe są już zaliczone, a sklep pyta o adres
      await expect(krokDane).toHaveClass(/-complete/);
      await expect(krokAdres).toHaveClass(/-current/);

      // imię i nazwisko sklep uzupełnia z konta; kraj Polska jest jedynym aktywnym
      await krokAdres.locator('[name=address1]').fill('ul. Długa 12');
      await krokAdres.locator('[name=postcode]').fill('80-831');
      await krokAdres.locator('[name=city]').fill('Gdańsk');
      await krokAdres.getByRole('button', { name: /Dalej/i }).click();

      await expect(krokAdres).toHaveClass(/-complete/);
      await expect(krokDostawa).toHaveClass(/-current/);
      await expect(krokAdres).toContainText('ul. Długa 12'); // zapisany adres widoczny w zwiniętym kroku
      // Classic zawsze ma w HTML ukryty komunikat „adres niekompletny” - sklep pokazuje go, gdy adres odrzuci
      await expect(krokAdres.locator('.js-address-error')).toBeHidden();
    });

    // PrestaShop pyta o przewoźnika przed płatnością, dlatego krok 7 wykonujemy przed krokiem 6
    // (numeracja jak w docs/WYMAGANIA.md)
    const przewoznik = 'Przesyłka kurierska ekspresowa'; // jeden z dwóch nowych przewoźników (shop/scripts/configure-sales.php)

    await test.step('Krok 7: wybór jednego z dwóch nowych przewoźników', async () => {
      const opcje = krokDostawa.locator('.delivery-option');
      // przy braku przewoźników sklep pokazuje tylko komunikat o przekroczonej wadze zamówienia
      await expect(opcje, 'brak przewoźników - czy koszyk nie przekracza limitu 50 kg?').toHaveCount(2);

      const radio = opcje.filter({ hasText: przewoznik }).locator('input[type=radio]');
      if (!(await radio.isChecked())) {
        // wybór zapisuje się w koszyku zapytaniem AJAX; dopiero po nim można przejść dalej
        const zapis = page.waitForResponse((r) => r.url().includes('selectDeliveryOption'));
        await radio.check();
        expect((await zapis).ok()).toBe(true);
      }
      await expect(radio).toBeChecked();

      await krokDostawa.getByRole('button', { name: /Dalej/i }).click();
      await expect(krokDostawa).toHaveClass(/-complete/);
      await expect(krokPlatnosc).toHaveClass(/-current/);
    });

    await test.step('Krok 6: wybór płatności przy odbiorze', async () => {
      // tylko metody stosowane w Polsce: przelew tradycyjny i płatność przy odbiorze
      await expect(krokPlatnosc.locator('input[name=payment-option]')).toHaveCount(2);
      // sprawdzamy tutaj przelew tradycyjny, a w 'pobranie' płatność przy odbiorze
      await expect(krokPlatnosc.locator('input[data-module-name="ps_wirepayment"]')).toHaveCount(1);

      const pobranie = krokPlatnosc.locator('input[data-module-name="ps_cashondelivery"]');
      await pobranie.check();
      await expect(pobranie).toBeChecked();
      // po wyborze sklep rozwija opis wybranej metody
      const opis = page.locator(`#${await pobranie.getAttribute('id')}-additional-information`);
      await expect(opis).toBeVisible();
      await expect(opis).toContainText(/przy dostawie/i);

      // przycisk zamówienia odblokowuje dopiero akceptacja regulaminu
      const zamow = page.locator('#payment-confirmation button');
      await expect(zamow).toBeDisabled();
      await krokPlatnosc.locator('[name="conditions_to_approve[terms-and-conditions]"]').check();
      await expect(zamow).toBeEnabled();
    });

    // numer referencyjny złożonego zamówienia - po nim kroki 9-10 znajdą zamówienie w historii zamówień
    let numerZamowienia = '';

    await test.step('Krok 8: zatwierdzenie zamówienia', async () => {
      const zamow = page.locator('#payment-confirmation button');
      await expect(zamow).toHaveText(/Złóż zamówienie/i);
      await zamow.click();

      // przyjazny URL po polsku; order-confirmation to nazwa kontrolera przy wyłączonych przyjaznych URL-ach
      await expect(page).toHaveURL(/(potwierdzenie-zamowienia|order-confirmation).*id_order=\d+/);
      await expect(page.locator('#content-hook_order_confirmation')).toContainText(/zamówienie zostało potwierdzone/i);
      await expect(page.locator('#content-hook_order_confirmation')).toContainText(klient.email);

      // numer referencyjny: 9 wielkich liter, np. „Numer zamówienia: LBAUXBPIC”
      const numer = page.locator('#order-reference-value');
      await expect(numer).toHaveText(/\b[A-Z]{9}\b/);
      // textContent, bo innerText zwraca tekst po CSS text-transform (jak przy kwocie w kroku 3)
      numerZamowienia = ((await numer.textContent()) ?? '').match(/\b[A-Z]{9}\b/)![0];

      // zamówienie zapisało wybory z kroków 6 i 7 oraz wszystkie pozycje koszyka
      const szczegoly = page.locator('#order-details');
      await expect(szczegoly).toContainText('Płatność przy odbiorze');
      await expect(szczegoly).toContainText(przewoznik);
      await expect(page.locator('#order-items .order-line')).toHaveCount(pozycjeWKoszyku);
      // po złożeniu zamówienia sklep zakłada klientowi nowy, pusty koszyk
      await expect(licznik).toHaveText(/\b0\b/);
    });
  });
});
