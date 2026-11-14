import { defineConfig, devices } from '@playwright/test';

// Konfiguracja testów E2E (end-to-end) sklepu PrestaShop.
// Dokumentacja opcji: https://playwright.dev/docs/test-configuration
export default defineConfig({
  // Folder z plikami testów (*.spec.ts)
  testDir: './e2e',

  // Raport HTML zapisywany do tests/playwright-report/.
  // open: 'never' - nie otwiera przeglądarki z raportem po testach (ważne np. w CI).
  // Ręczne podejrzenie raportu: npx playwright show-report
  reporter: [['html', { open: 'never' }]],

  // Ustawienia wspólne dla wszystkich testów
  use: {
    // Adres sklepu. Dzięki niemu w testach piszemy page.goto('/') zamiast pełnego URL.
    // Można go nadpisać zmienną środowiskową, np. BASE_URL=https://inny-adres npm run test:e2e
    // Domyślnie localhost:8443 - zgodnie z HTTPS_PORT w .env i domeną sklepu (PS_DOMAIN).
    baseURL: process.env.BASE_URL ?? 'https://localhost:8443',

    // Sklep używa własnego (self-signed) certyfikatu SSL, którego przeglądarka nie zna.
    // Bez tej flagi każdy test kończyłby się błędem certyfikatu.
    ignoreHTTPSErrors: true,

    // Zrzut ekranu robiony tylko gdy test się nie powiedzie; trafia do tests/test-results/
    // i jest podpięty w raporcie HTML.
    screenshot: 'only-on-failure',
  },

  // Przeglądarki, na których uruchamiamy testy. Na razie tylko Chromium.
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
});
