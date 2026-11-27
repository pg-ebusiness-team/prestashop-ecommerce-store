# ADR 0002: Własny baner cookies w motywie potomnym zamiast modułu

- Status: zaakceptowany
- Data: 2026-11-06
- Zadanie: FRONT-4 (strony CMS, baner cookies)

## Kontekst

Sklep ma wyświetlać baner informujący o cookies przy pierwszej wizycie (etap 1). Ticket zakładał „włącz i skonfiguruj
moduł baneru cookie”. Wygląd ma odpowiadać sklepowi źródłowemu (panel „Drogi użytkowniku”,
przyciski Ustawienia / Zatwierdź tylko wymagane / Zaakceptuj wszystkie).

Ograniczenia:

- PrestaShop 8.2 nie ma wbudowanego modułu baneru cookies (`psgdpr` obsługuje zgody w formularzach, nie baner);
- w etapie 2 wymagany jest baner zgodny z **Consent Mode v2** - przed zgodą GA4 nie zapisuje cookies;
- konfiguracja musi przetrwać `make reset` i trafić na klaster, więc nie może istnieć tylko w panelu;
- wynik Lighthouse Accessibility ≥ 85 - baner jest na każdej stronie, więc nie może psuć dostępności.

## Rozważane opcje

1. **Moduł z PrestaShop Addons.** Darmowe moduły zwykle tylko informują (bez kategorii zgód), płatne trzeba kupić;
   kod spoza repo, konfiguracja w bazie, wygląd trudny do dopasowania do źródła.
2. **Zewnętrzny CMP (Cookiebot, CookieYes).** Gotowy Consent Mode v2, ale wymaga konta w obcej usłudze, skrypt
   z zewnętrznej domeny i darmowe limity; wygląd narzucony przez dostawcę.
3. **Własny baner w `custom-child-theme`.** Natywny `<dialog>` + kilkadziesiąt linii JS, wybór w `localStorage`.

## Decyzja

Opcja 3.

- `templates/_partials/cookie-banner.tpl` - treść i przyciski jak w źródle, kategorie Analityczne i Marketingowe
  (odpowiadają `analytics_storage` oraz `ad_storage`/`ad_user_data`/`ad_personalization` w Consent Mode v2).
- `assets/js/custom.js` - pokazuje baner, gdy brak zapisu `cookie-consent`, zapisuje `{analytics, marketing}`.
  PrestaShop ładuje ten plik automatycznie dla motywu.
- Przycisk „Ustawienia cookies” w stopce otwiera baner ponownie - zgodę wycofuje się równie łatwo, jak się ją wyraża.
- `showModal()` daje przyciemnienie tła, utrzymanie fokusu w oknie i obsługę klawiatury bez bibliotek.

## Konsekwencje

- Baner jest w repo i w obrazie Dockera, bez zależności od zewnętrznych usług.
- Zgoda jest na razie tylko zapisywana. Przy GA4 (etap 2) trzeba dodać `gtag('consent', 'default', ...)` z odmową
  przed załadowaniem GA i `gtag('consent', 'update', ...)` po wyborze - w `custom.js` jest oznaczone `shortcut:`.
- Wybór jest w `localStorage`, nie w cookie: serwer go nie widzi. Wystarcza, bo o zgodzie decyduje JS po stronie
  przeglądarki (Consent Mode). Gdyby serwer miał warunkowo wstawiać skrypty, trzeba przejść na cookie.
- Esc zamyka baner bez zapisu - pojawi się ponownie na kolejnej stronie.
- Baner jest w `_partials/footer.tpl`, więc nie ma go w procesie zamówienia (Classic ma tam własną stopkę).
  Pierwsza wizyta prawie zawsze zaczyna się poza zamówieniem.
- Tym samym mechanizmem działa okno potwierdzenia pełnoletności (`_partials/age-gate.tpl`): otwiera się po
  zamknięciu banera cookies, „Tak” zapisuje `age-confirmed` w `localStorage`, „Nie” i Esc nie zamykają okna.
  To potwierdzenie deklaratywne, nie weryfikacja wieku - tę robi kurier przy odbiorze.
  Testy E2E (W4, oba etapy) muszą przed wejściem ustawić `cookie-consent` i `age-confirmed`, inaczej okna zasłonią stronę.
