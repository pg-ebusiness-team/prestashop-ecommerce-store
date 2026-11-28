# prestashop-ecommerce-store

Sklep internetowy na PrestaShop 8.2.8 w kontenerach Docker, z importem danych ze scrapera i testami E2E w Playwright. Etap 1: sklep w Docker Compose, scraper, import danych, konfiguracja sprzedaży. Etap 2 (planowany): Docker Swarm i GA4. Wymagania i ich stan: [docs/WYMAGANIA.md](docs/WYMAGANIA.md).

Autorzy:
Bartosz Pacyga
Jakub Romanowski
Michał Kaźmierowski
Kacper Trznadel

## Uruchomienie

Wymagania: Docker z Compose v2, `make`, `curl` i internet (obrazy Dockera, archiwum zdjęć z Releases, grafiki strony głównej ze sklepu źródłowego). Python nie jest potrzebny: importer i scraper działają w kontenerze `tools`. Testy E2E wymagają Node.js 18+, testy jednostkowe Pythona 3.12.

Z czystego klona, w katalogu projektu:

```bash
make up     # buduje obrazy, uruchamia sklep i czeka na koniec instalacji (ok. 1–3 min)
make init   # zdjęcia, klucz API, import produktów, filtry, opisy kategorii, motyw (ok. 5 min)
```

**`make up`** przy pierwszym uruchomieniu tworzy `.env` z `.env.example` z wygenerowanym kluczem `PS_API_KEY`. Przykładowe hasła wystarczą lokalnie. Inne porty, domenę lub hasła ustaw w `.env` przed pierwszym `make up` (`cp .env.example .env`). Istniejący `.env` nie jest nadpisywany. Polecenie kończy się, gdy kontener `shop` ma status *healthy* (PrestaShop zainstalowany i połączony z bazą). Błąd instalacji lub konfiguracji kończy je kodem błędu, przyczyna jest w `make logs SERVICE=shop`.

**`make init`** wykonuje po kolei kroki z tabeli i zatrzymuje się na pierwszym błędzie. Każdy krok jest idempotentny (ponowne `make init` aktualizuje dane bez duplikatów) i dostępny jako osobne polecenie, np. `make theme`, `make import`.

| Krok | Co robi |
|---|---|
| `check-shop` | Sprawdza, czy sklep jest *healthy*; jeśli nie, kończy się, zanim cokolwiek zmieni. |
| `photos` | Pobiera zdjęcia produktów (opis niżej). Jest przed krokami zmieniającymi bazę, bo bez zdjęć import się nie uda. |
| `webservice` | Włącza Webservice API i rejestruje klucz `PS_API_KEY` z uprawnieniami tylko do zasobów potrzebnych importerowi ([Webservice_API.md](docs/Webservice_API.md)). |
| `cleanup-demo` | Usuwa przez API kategorie i produkty demo z instalatora. |
| `omnibus-install` | Instaluje własny moduł `omnibusprice` (sekcja [Promocje i Omnibus](#promocje-i-omnibus)). Przed importem, bo importer wysyła do niego ceny. |
| `import` | Importuje przez API kategorie, atrybuty, cechy i poprawne produkty (ze zdjęciem i opisem) z wariantami, stanami, zdjęciami, promocjami i cenami Omnibus ([Importer.md](docs/Importer.md)). |
| `facets` | Zakłada filtry lewej kolumny (`ps_facetedsearch`) jak w źródle (`deploy/init/facets.php`) i przebudowuje ich indeks. |
| `categories` | Wpisuje opisy kategorii z `shop/categories/*.html`. Część po `<!-- więcej -->` jest zwinięta pod „Pokaż więcej”. |
| `theme` | Włącza motyw `custom-child-theme`, pobiera grafiki strony głównej (`deploy/init/home-images.txt`), wgrywa treści strony głównej (`deploy/init/theme.sql`) i stron CMS (`shop/cms/`, `deploy/init/cms.sql`), czyści cache. |

`facets`, `categories` i `theme` szukają kategorii i cech po nazwie, więc idą po imporcie. `theme` jest ostatni, bo czyści cache po zmianach SQL z wcześniejszych kroków. Filtry, opisy kategorii i treści stron zmienione w panelu kolejne `make init` nadpisze wersją z repo.

**Zdjęcia produktów** nie są w repo. `make photos` (`deploy/init/photos.sh`) pobiera archiwum z Releases (`photos_v1.0`, adres w `PHOTOS_RELEASE_URL`, można nadpisać w `.env`), a potem scraperem `--photos-only` dociąga brakujące zdjęcia z URL-i ze źródła (robots.txt, ≤2 zapytania/s). Bez archiwum pobiera cały zbiór ze źródła (ok. 2900 zdjęć, ok. 25 min). Błąd zgłasza dopiero brak obu źródeł. `ERROR … 404` przy zdjęciu `1992` jest oczekiwany (brak pliku w źródle).

**Import z opcjami:** `make import IMPORT_ARGS=--dry-run` (podgląd), `make import IMPORT_ARGS="--execute --limit 100"`. Sprawdzenie API: `make api-check`.

**Adresy** (tylko HTTPS, certyfikat samopodpisany — zaakceptuj wyjątek w przeglądarce):

- sklep: `https://<SERVER_NAME>:<HTTPS_PORT>` (domyślnie https://localhost:8443); HTTP na `HTTP_PORT` (8080) przekierowuje 301 na HTTPS,
- panel: `https://<SERVER_NAME>:<HTTPS_PORT>/<ADMIN_FOLDER>`,
- Mailpit: `http://localhost:<MAILPIT_PORT>` (domyślnie http://localhost:8025).

Pozostałe polecenia: `make ps`, `make logs [SERVICE=shop]`, `make shell`, `make down`, `make reset` (usuwa też dane), `make help`.

## Poczta testowa (Mailpit)

E-maile ze sklepu (rejestracja, zamówienie) trafiają do Mailpita, nie do adresatów. SMTP ustawia przy każdym starcie kontenera `shop/init-scripts/10-configure-mail.sh`, bez kroków w panelu. Mailpit nie ma wolumenu, więc wiadomości znikają po `make down`.

## Płatności i dostawa

Ustawia je przy każdym starcie kontenera `shop/scripts/configure-sales.php` (przez `20-configure-sales.sh`, [ADR 0003](docs/adr/0003-konfiguracja-sprzedazy.md)):

- **płatności:** przelew tradycyjny (fikcyjne dane konta) i płatność przy odbiorze; płatność czekiem jest odinstalowywana,
- **przewoźnicy:** „Przesyłka kurierska” (19,99 zł) i „Przesyłka kurierska ekspresowa” (29,99 zł) brutto z VAT 23%, tylko Polska; przewoźnicy z instalatora są wyłączani (nazwy i ceny: tablica `CARRIERS`),
- **kraje:** aktywna tylko Polska,
- **faktura:** zamówienie za pobraniem ma fakturę od razu (do pobrania w „Historii zamówień”),
- **darmowa dostawa** od 2000 zł brutto włącznie (wartość produktów po rabatach),
- **limit wagi:** powyżej 50 kg nie ma przewoźnika; klient widzi komunikat z linkiem do strony „Dostawa” (`checkout/_partials/steps/shipping.tpl`).

Próg i limit to zmienne `FREE_SHIPPING_THRESHOLD` i `MAX_ORDER_WEIGHT_KG` usługi `shop` w `deploy/compose.yaml`; po zmianie wystarczy `make up`. Pozostałe zmiany wprowadzamy w `configure-sales.php` (zmiany z panelu nadpisze restart). Przy zmianach popraw też `shop/cms/1-dostawa.html`. Błąd konfiguracji (`20-configure-sales: BLAD: ...` w logu) celowo zatrzymuje kontener.

## Promocje i Omnibus

Promocje ze źródła (pole `specific_prices` w wynikach scrapera) importer zakłada przez API jako ceny specyficzne (`scraper/importer/promotions.py`): sklep pokazuje starą cenę, rabat i nową cenę.

Najniższą cenę z 30 dni (dyrektywa Omnibus) obsługuje własny moduł `shop/modules/omnibusprice`:

- instalacja (`make omnibus-install`) tworzy tabelę `ps_omnibusprice` i podpina hook `displayProductPriceBlock`,
- importer (`scraper/importer/omnibus.py`) wysyła ceny z `lowest_price_30d_amount` produktów i wariantów na `POST /module/omnibusprice/sync`. Kontroler przyjmuje tylko aktywny klucz Webservice API (Basic Auth), sprawdza produkt i wariant i zapisuje cenę bez duplikatów,
- pod ceną na liście i karcie produktu widać „Najniższa cena z 30 dni: …” (cena wariantu, a bez niej produktu).

Moduł jest synchronizowany do wolumenu przy starcie kontenera jak motyw ([Docker_Docs.md](docs/Docker_Docs.md#synchronizacja-motywu-i-modułu-init-scripts)). Odinstalowanie zostawia tabelę z cenami.

## Wygląd sklepu (motyw potomny)

Wygląd zmieniamy tylko w `shop/themes/custom-child-theme` (dziedziczy po Classic, którego nie edytujemy): `config/theme.yml` (hooki, układy) i `assets/css/custom.css` (własne style). Motyw trafia do sklepu przy starcie kontenera (`00-sync-theme.sh`), więc po zmianie: `make up` i `make theme`. Szczegóły: [wyglad_strony.md](docs/wyglad_strony.md).

## Kopia zapasowa i odtwarzanie

```bash
make backup                                   # kopia do backups/backup-<data>.tar
make restore [BACKUP=backups/<plik>.tar]      # odtworzenie (domyślnie najnowsza); USUWA bieżące dane
make config-export / make config-import       # ustawienia sklepu w deploy/config/configuration.json (w repo)
```

Kopia (ok. 415 MB, ok. 20 s; odtworzenie ok. 1 min) zawiera bazę, wolumen `shop_data`, certyfikat i mapowania importera. Ma dane klientów i hasła, więc `backups/` jest w `.gitignore`. Restore dopasowuje sklep do bieżącego `.env`; konta zostają z kopii. Szczegóły: [Backup.md](docs/Backup.md).

## Testy E2E (Playwright)

Przy działającym sklepie z danymi:

```bash
make test-e2e                         # domyślnie https://localhost:<HTTPS_PORT>
make test-e2e SHOP_URL=https://adres
```

Raport HTML: `tests/playwright-report/` (`cd tests && npx playwright show-report`), zrzuty nieudanych testów: `tests/test-results/`. Pojedynczy test: `cd tests && BASE_URL=https://localhost:8443 npx playwright test e2e/zamowienie.spec.ts [--headed]`.

| Plik | Co sprawdza |
|---|---|
| `tests/e2e/smoke.spec.ts` | strona główna się ładuje |
| `tests/e2e/zamowienie.spec.ts` | scenariusz W4, kroki 1–10: 10 produktów z ≥2 kategorii w różnych ilościach, wyszukanie i dodanie losowego wyniku, usunięcie 3 pozycji, rejestracja, zamówienie z adresem, przewoźnik ekspresowy i płatność przy odbiorze, potwierdzenie z numerem, status w historii zamówień, faktura PDF. Ok. 30 s, limit 5 min |

Każde uruchomienie zakłada klienta `e2e+<timestamp>@example.com` i składa prawdziwe zamówienie (rozpoznasz je po `e2e+`). Zamówienia zmniejszają stany, a test bierze produkty z kategorii z górnego menu, więc po kilku uruchomieniach może zabraknąć produktów (np. `Expected: 10, Received: 8`) — przywróć stany przez `make import`. Nowe testy muszą ustawić w `localStorage` `cookie-consent` i `age-confirmed`, inaczej baner cookies i okno 18+ zasłaniają stronę ([ADR 0002](docs/adr/0002-baner-cookies.md)).

## Testy jednostkowe i linter

Bez sklepu, z Pythonem 3.12 — to samo uruchamia CI przy każdym PR do `main`:

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r scraper/requirements.txt
ruff check scraper/
pytest scraper/     # parser scrapera, mapowanie i wybór produktów importera
```

## Dokumentacja

| Dokument | Zawartość |
| --- | --- |
| [WYMAGANIA.md](docs/WYMAGANIA.md) | Wymagania projektu i ich stan |
| [ODSTEPSTWA.md](docs/ODSTEPSTWA.md) | Znane odstępstwa od sklepu źródłowego |
| [Docker_Docs.md](docs/Docker_Docs.md) | Architektura kontenerów |
| [Scraper_Instrukcja.md](docs/Scraper_Instrukcja.md), [Scraper_Dzialanie.md](docs/Scraper_Dzialanie.md) | Uruchomienie i budowa scrapera |
| [Importer.md](docs/Importer.md) | Import danych do sklepu |
| [Webservice_API.md](docs/Webservice_API.md) | Konfiguracja Webservice API |
| [Backup.md](docs/Backup.md) | Kopia zapasowa, odtwarzanie i eksport ustawień |
| [wyglad_strony.md](docs/wyglad_strony.md) | Wygląd sklepu i motyw potomny |
| [adr/](docs/adr/) | Decyzje architektoniczne |
| [AI_LOG.md](docs/AI_LOG.md), [AI_REFLEKSJA.md](docs/AI_REFLEKSJA.md) | Dziennik AI i refleksja zespołu |
| [stock_validation.sql](docs/stock_validation.sql) | Kontrola stanów magazynowych (zakres 0–10, udział zer) |
| [Business Model Canvas](docs/Business_Model_Canvas_LuksusoweAlkohole.md) | Zadanie z wykładu 2 |

## Rozwiązywanie problemów

| Objaw | Co zrobić |
|---|---|
| `check-shop: BLAD` przy `make init` | Sklep nie działa lub się instaluje: `make up` i poczekaj. Przy `unhealthy` przyczyna jest w `make logs SERVICE=shop` (linie z `BLAD`). |
| `photos: BLAD: brak archiwum i nie udało się pobrać zdjęć z URL-i` | Sprawdź internet i `PHOTOS_RELEASE_URL` (czy tag wydania się nie zmienił), potem `make init`. |
| `Za mało produktów z minimum 2 zdjęciami` / `Nie udało się wybrać N produktów` | Brak zdjęć: `make photos`. |
| Ostrzeżenia Compose o brakujących zmiennych | Brak `.env` w katalogu głównym lub w nim zmiennych z `.env.example`. |
| Kontener `shop` się zatrzymał | Przyczyna w ostatnich liniach `make logs SERVICE=shop` (`02-sync-env: BLAD`, `20-configure-sales: BLAD` itd.). |
| Zły adres lub pętla przekierowań po zmianie `HTTP_PORT`, `HTTPS_PORT`, `SERVER_NAME` | `make up` — domenę dopasuje `02-sync-env.sh` ([Docker_Docs.md](docs/Docker_Docs.md#dopasowanie-do-zmiennych-środowiskowych-init-scripts)). Certyfikat dla nowej nazwy: `make down`, `docker volume rm deploy_proxy_certs`, `make up`. W ostateczności `make reset`, `make up`, `make init`. |
| Ostrzeżenie o niezaufanym certyfikacie | Oczekiwane (samopodpisany). Certyfikat jest w wolumenie `proxy_certs`, więc wyjątek dodajesz raz; nowy powstaje po `make reset`. |
| Brak e-maili w Mailpicie | W `make logs SERVICE=shop` powinno być `10-configure-mail: ustawiam SMTP mail:1025`. Przy `BLAD` brakuje `MAIL_SMTP_HOST`/`MAIL_SMTP_PORT`. Gdy linia jest, sprawdź, czy `MAIL_SMTP_HOST` w `compose.yaml` to nazwa usługi `mail`. |

`make reset` kasuje bazę, wolumen `shop_data`, certyfikat i `scraper/importer/*_mapping.json`; pobrane zdjęcia w `scraper_results/product_photos/` zostają.
