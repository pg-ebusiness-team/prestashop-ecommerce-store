# prestashop-ecommerce-store

Sklep internetowy oparty na PrestaShop 8.2.8, uruchamiany w kontenerach Docker, wyposażony w automatyczny import danych ze scrapera oraz testy E2E w Playwright. Etap 1 obejmuje sklep w Docker Compose, scraper, import danych i konfigurację sprzedaży. Wdrożenie na klaster Docker Swarm i analityka GA4 są planowane w etapie 2. Wymagania i ich stan: [docs/WYMAGANIA.md](docs/WYMAGANIA.md).

Autorzy:
Bartosz Pacyga
Jakub Romanowski
Michał Kaźmierowski
Kacper Trznadel

## Uruchomienie projektu

Wymagania: Docker z Compose v2, `make`, `curl` i dostęp do internetu (obrazy Dockera, archiwum zdjęć z zakładki Releases, grafiki strony głównej ze sklepu źródłowego). Pythona na komputerze nie potrzeba: importer i scraper działają w kontenerze narzędziowym `tools`. Testy E2E wymagają Node.js 18+, a testy jednostkowe scrapera Pythona 3.12 (sekcja [Testy jednostkowe i linter](#testy-jednostkowe-i-linter)).

Z czystego klona sklep z danymi uruchamiają dwie komendy:

```bash
make up     # buduje obrazy, uruchamia sklep i czeka na koniec instalacji
make init   # inicjalizacja danych: zdjęcia, import produktów, filtry, opisy kategorii, motyw
```

U nas `make up` trwa ok. 1–3 min (pierwsze pobieranie obrazów dłużej), a `make init` ok. 5 min.

### 1. Sklonuj repozytorium

Sklonuj repozytorium i przejdź do katalogu projektu:

```bash
cd prestashop-ecommerce-store
```

### 2. Uruchom sklep

Z poziomu głównego katalogu projektu wykonaj polecenie:

```bash
make up
```

Przy pierwszym uruchomieniu polecenie tworzy plik `.env` z `.env.example` i wpisuje do niego wygenerowany klucz Webservice API (`PS_API_KEY`, 32 znaki `A-Z0-9`). Przykładowe hasła z `.env.example` wystarczą do pracy lokalnej. Jeśli chcesz inne porty, domenę lub hasła, utwórz `.env` samodzielnie przed pierwszym `make up` (`cp .env.example .env` i edycja). Zmiana portów lub domeny po instalacji wymaga `make reset` (patrz [Rozwiązywanie problemów](#po-aktualizacji-sklep-przekierowuje-na-zły-adres-lub-w-pętli)). Istniejący `.env` nigdy nie jest nadpisywany.

Następnie polecenie buduje obrazy, uruchamia kontenery w tle i czeka, aż sklep będzie gotowy. Kończy się dopiero wtedy, gdy kontener `shop` ma status *healthy*, czyli PrestaShop jest zainstalowany i połączony z bazą (healthcheck w `deploy/compose.yaml`). Pierwsze uruchomienie trwa dłużej, bo Docker pobiera obrazy, a kontener instaluje PrestaShop. Jeśli instalacja albo konfiguracja sklepu się nie uda, `make up` kończy się błędem, a przyczynę widać w `make logs SERVICE=shop`.

### 3. Zainicjalizuj dane

Po `make up` wykonaj:

```bash
make init
```

Polecenie wykonuje po kolei kroki z tabeli i zatrzymuje się na pierwszym błędzie. Na końcu wypisuje łączny czas i adres sklepu. Każdy krok jest idempotentny, więc ponowne `make init` aktualizuje dane bez tworzenia duplikatów. Kroki są też osobnymi poleceniami (np. `make theme` po zmianie motywu, `make import` po zmianie wyników scrapera).

| Krok | Co robi |
|---|---|
| `check-shop` | Sprawdza, czy sklep działa i ma status *healthy*. Jeśli nie, kończy się z podpowiedzią (`make up` albo `make logs SERVICE=shop`), zanim cokolwiek zmieni. |
| `photos` | Pobiera zdjęcia produktów do `scraper_results/product_photos/` (opis niżej). Idzie przed krokami, które zmieniają bazę, bo nie zależy od sklepu: bez zdjęć `make init` kończy się, zanim cokolwiek w niej zmieni. |
| `webservice` | Włącza Webservice API i rejestruje klucz `PS_API_KEY` z `.env` z uprawnieniami GET/POST/PUT/DELETE wyłącznie do zasobów `categories`, `products`, `combinations`, `stock_availables`, `images`, `product_options`, `product_option_values`, `product_features`, `product_feature_values` (`deploy/init/webservice.sql`). Po zmianie klucza w `.env` zastępuje stary klucz nowym. |
| `cleanup-demo` | Usuwa przez API kategorie i produkty demonstracyjne z instalatora. |
| `import` | Importuje przez API kategorie, atrybuty, cechy i wszystkie poprawne produkty (ze zdjęciem i opisem) z wariantami, stanami magazynowymi i zdjęciami. Ponowne uruchomienie aktualizuje istniejące rekordy. Szczegóły: [docs/Importer.md](docs/Importer.md). |
| `facets` | Zakłada w module `ps_facetedsearch` zestawy filtrów lewej kolumny dla grup kategorii, tak jak w sklepie źródłowym (lista w `deploy/init/facets.php`), i przebudowuje indeks filtrów. |
| `categories` | Wpisuje opisy kategorii z plików HTML w `shop/categories/` (lista w `deploy/init/categories.sql`). Część po znaczniku `<!-- więcej -->` jest zwinięta pod przyciskiem „Pokaż więcej”. |
| `theme` | Aktywuje motyw potomny `custom-child-theme`, pobiera grafiki strony głównej ze sklepu źródłowego (lista w `deploy/init/home-images.txt`), wgrywa treści strony głównej (slider, kafelki, banery, logo, menu, stopka; `deploy/init/theme.sql`) i stron CMS (Dostawa, Polityka prywatności, Regulamin, O nas, Płatności, Oferta dla firm; pliki HTML w `shop/cms/`, metadane w `deploy/init/cms.sql`), a na końcu czyści cache. |

Kolejność wynika z zależności. `facets`, `categories` i `theme` dopasowują kategorie i cechy po nazwie, więc muszą iść po imporcie (`theme` buduje z nich górne menu i stopkę). `theme` idzie ostatni, bo czyszczenie cache obejmuje też zmiany wprowadzone SQL-em w poprzednich krokach. Filtry, opisy kategorii, treści strony głównej i stron CMS ustawione w panelu zostaną przy kolejnym `make init` nadpisane wersją z repo.

**Zdjęcia produktów.** Zdjęć nie ma w repozytorium. `make photos` (krok `make init` zaraz po `check-shop`, skrypt `deploy/init/photos.sh`):

1. pobiera archiwum z zakładki **Releases** (wydanie `photos_v1.0`, adres w zmiennej `PHOTOS_RELEASE_URL` w `makefile`, którą można nadpisać w `.env`) i rozpakowuje je. Po udanym rozpakowaniu zapisuje znacznik `scraper_results/product_photos/.release`, więc kolejne uruchomienia nie pobierają archiwum ponownie;
2. uruchamia scraper w trybie `--photos-only`, który pobiera z adresów zapisanych w wynikach scrapera (`scraper_results/products/`) tylko brakujące zdjęcia, z zachowaniem `robots.txt` i limitu 2 zapytań/s.

Gdy archiwum jest niedostępne, krok 2 pobiera cały zbiór ze sklepu źródłowego (ok. 2900 zdjęć, ok. 25 min). Gdy sklep źródłowy nie odpowiada, a zdjęcia z archiwum są, krok kończy się ostrzeżeniem i `make init` idzie dalej. Błąd zgłasza dopiero brak obu źródeł. Linie `ERROR … 404` przy zdjęciu `1992` są oczekiwane: sklep źródłowy nie ma tego pliku, a importer pomija produkt bez zdjęcia.

**Import z innymi opcjami.** Podgląd bez zapisu: `make import IMPORT_ARGS=--dry-run`. Ograniczenie liczby produktów: `make import IMPORT_ARGS="--execute --limit 100"`.

Poprawność konfiguracji API sprawdzisz poleceniem:

```bash
make api-check
```

### 4. Sprawdź status kontenerów

Aby sprawdzić, czy kontenery zostały uruchomione poprawnie, wykonaj:

```bash
make ps
```

Kontener `shop` powinien mieć status `(healthy)`. Jeżeli chcesz obserwować logi na bieżąco, użyj:

```bash
make logs
```

Domyślnie pokazuje to logi wszystkich kontenerów. Aby zawęzić je do jednego, podaj nazwę usługi, np. `make logs SERVICE=proxy`.

### 5. Otwórz sklep

Sklep jest dostępny wyłącznie przez HTTPS:

- sklep: `https://<SERVER_NAME>:<HTTPS_PORT>` (bazowo: https://localhost:8443)
- panel administratora: `https://<SERVER_NAME>:<HTTPS_PORT>/<ADMIN_FOLDER>`

Zapytania na `http://<SERVER_NAME>:<HTTP_PORT>` (bazowo: http://localhost:8080) są przekierowywane (301) na adres HTTPS.

Certyfikat jest samopodpisany i generowany automatycznie przy pierwszym uruchomieniu, dlatego przeglądarka wyświetli ostrzeżenie o niezaufanym certyfikacie. Aby przejść do sklepu, zaakceptuj wyjątek.

## Poczta testowa (Mailpit)

E-maile wysyłane przez sklep (m.in. po rejestracji konta i po złożeniu zamówienia) nie trafiają do prawdziwych adresatów, tylko do kontenera Mailpit. Interfejs WWW jest dostępny pod adresem:

- `http://localhost:<MAILPIT_PORT>` (bazowo: http://localhost:8025)

Dodatkowe informacje:

- Interfejs Mailpit działa po HTTP. To narzędzie deweloperskie, a wymóg HTTPS dotyczy sklepu.
- Wiadomości nie są zapisywane trwale (brak wolumenu), więc znikają po usunięciu kontenera, np. po `make down`.
- Sklep jest skonfigurowany do wysyłki przez Mailpit automatycznie przy każdym starcie kontenera `shop`. Nie trzeba w tym celu uruchamiać `make init` ani ustawiać niczego w panelu administratora.

## Płatności i dostawa

Konfiguracja sprzedaży ustawia się automatycznie przy każdym starcie kontenera `shop` — nie trzeba niczego klikać w panelu ani uruchamiać dodatkowych komend. Robi to `shop/init-scripts/20-configure-sales.sh`, który wywołuje `shop/scripts/configure-sales.php` (uzasadnienie: [ADR 0003](docs/adr/0003-konfiguracja-sprzedazy.md)).

- **Metody płatności:** przelew tradycyjny (`ps_wirepayment`, fikcyjne dane konta) i płatność przy odbiorze (`ps_cashondelivery`). Płatność czekiem (`ps_checkpayment`), instalowana domyślnie, jest odinstalowywana.
- **Przewoźnicy:** „Przesyłka kurierska” (19,99 zł) i „Przesyłka kurierska ekspresowa” (29,99 zł), ceny brutto z 23% VAT, dostawa tylko na terenie Polski. Przewoźnicy z instalatora i danych demo („Click and collect”, „My carrier” itd.) są wyłączani. Nazwy i ceny zmienia się w tablicy `CARRIERS`, a potem trzeba też poprawić stronę CMS `shop/cms/1-dostawa.html`.
- **Faktura:** zamówienie za pobraniem dostaje fakturę już przy złożeniu — klient może ją pobrać z „Historii zamówień”.
- **Kraje:** aktywna jest tylko Polska — w adresie nie da się wybrać innego kraju. Pozostałe kraje (np. USA i Francja z danych demo) są wyłączane.
- **Darmowa dostawa:** od 2000 zł brutto (włącznie), liczone od wartości produktów po rabatach, bez kosztu dostawy.
- **Limit wagi:** zamówienie cięższe niż 50 kg nie ma dostępnego przewoźnika, więc nie da się go złożyć. Zamówienie ważące dokładnie 50 kg przechodzi. W kroku „Dostawa” klient widzi wtedy komunikat o przekroczonej wadze z linkiem do strony „Dostawa” (szablon `checkout/_partials/steps/shipping.tpl` w motywie potomnym).

Próg darmowej dostawy i limit wagi ustawia się w `deploy/compose.yaml` (zmienne `FREE_SHIPPING_THRESHOLD` i `MAX_ORDER_WEIGHT_KG` usługi `shop`). Po zmianie wystarczy `make up` — kontener uruchomi się ponownie z nowymi wartościami. Pamiętaj też o treści strony CMS `shop/cms/1-dostawa.html`.

Zmiany tych ustawień w panelu administratora zostaną nadpisane przy kolejnym starcie kontenera. Trwałą zmianę wprowadzamy w `shop/scripts/configure-sales.php`, a potem `make up` (przebudowa obrazu).

W logach (`make logs SERVICE=shop`) przy starcie pojawiają się linie `20-configure-sales: ...`, zakończone `konfiguracja sprzedazy zakonczona`. Linia `20-configure-sales: BLAD: ...` oznacza, że konfiguracja się nie udała — wtedy kontener `shop` celowo się zatrzymuje (widać to w `make ps`), żeby sklep nie działał z ustawieniami niezgodnymi z wymaganiami. Przyczyna jest w linii z `BLAD` powyżej.

## Wygląd sklepu (motyw potomny)

Wygląd sklepu zmieniamy wyłącznie w motywie potomnym `shop/themes/custom-child-theme`. Plików motywu Classic nie edytujemy — pochodzi z obrazu PrestaShop i jest dziedziczony.

- `config/theme.yml` — konfiguracja motywu (`parent: classic`, `use_parent_assets: true`); sekcje `global_settings` i `theme_settings` są skopiowane z Classic, aby zachować hooki modułów, typy obrazków i układy stron.
- `assets/css/custom.css` — wszystkie własne style; PrestaShop ładuje go automatycznie po CSS Classic.

Motyw jest kopiowany do obrazu, a przy każdym starcie kontenera skrypt `shop/init-scripts/00-sync-theme.sh` przenosi go do plików sklepu (wolumen `shop_data`). Po każdej zmianie w plikach motywu wykonaj więc `make up` (przebudowa obrazu i restart kontenera, dane zostają) i `make theme` (czyści cache).

## Testy E2E (Playwright)

Wymagany Node.js 18+. Przy uruchomionym sklepie wykonaj:

```bash
make test-e2e
```

Polecenie instaluje zależności i przeglądarkę Chromium, a następnie uruchamia testy z katalogu `tests/e2e/` na adresie `https://localhost:${HTTPS_PORT}`. Inny adres sklepu podasz przez `make test-e2e SHOP_URL=https://adres`.

Raport HTML zapisuje się w `tests/playwright-report/` (podgląd: `cd tests && npx playwright show-report`), a zrzuty ekranu nieudanych testów w `tests/test-results/`.

Jeden plik lub jeden test: `cd tests && BASE_URL=https://localhost:8443 npx playwright test e2e/zamowienie.spec.ts` (filtr po nazwie: `-g "Scenariusz zamówienia"`, podgląd przeglądarki: `--headed`).

| Plik | Co sprawdza |
|---|---|
| `tests/e2e/smoke.spec.ts` | strona główna się ładuje |
| `tests/e2e/zamowienie.spec.ts` | scenariusz W4 w jednym teście, kroki 1–10: 10 produktów z co najmniej 2 kategorii w różnych ilościach, wyszukanie produktu i dodanie losowego wyniku, usunięcie 3 pozycji z koszyka, rejestracja nowego konta, zamówienie na zawartość koszyka z adresem, wybór przewoźnika „Przesyłka kurierska ekspresowa” i płatności przy odbiorze, zatwierdzenie zamówienia i sprawdzenie strony potwierdzenia z numerem referencyjnym, status zamówienia w historii zamówień, pobranie faktury VAT (plik zaczyna się od `%PDF-`) |

Kroki 9–10 dotyczą zamówienia z kroku 8 (numer referencyjny jest w zmiennej `numerZamowienia`): test szuka go w historii zamówień, sprawdza status „Oczekiwanie na płatność przy odbiorze” i pobiera fakturę. Cały scenariusz musi trwać ≤5 min (`test.setTimeout`); kroki 1–8 trwają ok. 25 s, kroki 9–10 kilka sekund.

Każde uruchomienie zakłada nowego klienta `e2e+<timestamp>@example.com` i składa prawdziwe zamówienie za pobraniem — zamówienia testowe rozpoznasz w panelu i w Mailpicie po prefiksie `e2e+`. Zamówienia zmniejszają stany magazynowe, a test bierze produkty tylko z kategorii najwyższego poziomu w górnym menu (losowa kolejność rozkłada zużycie, ale pula jest mała). Po kilku uruchomieniach kroki 1–2 przestają znajdować dostępne produkty (np. `Expected: 10, Received: 8` w kroku 1) — wtedy odśwież stany poleceniem `make import`, który przywraca stany z wyników scrapera.

Scenariusz wymaga zaimportowanych produktów (`make import`) i kategorii w górnym menu, bo z menu wybiera kategorie. Produkty bez wystarczającego stanu pomija. Test, który klika po stronie, musi przed wejściem ustawić w `localStorage` `cookie-consent` i `age-confirmed` (jak w `zamowienie.spec.ts`), inaczej baner cookies i okno 18+ zasłaniają stronę ([ADR 0002](docs/adr/0002-baner-cookies.md)).

## Testy jednostkowe i linter

Na komputerze z Pythonem 3.12, bez uruchomionego sklepu. Raz utwórz środowisko wirtualne z zależnościami:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r scraper/requirements.txt
```

Potem, z aktywnym środowiskiem, uruchom to samo, co CI przy każdym PR do `main`:

```bash
ruff check scraper/
pytest scraper/
```

## Dokumentacja

| Dokument | Zawartość |
| --- | --- |
| [WYMAGANIA.md](docs/WYMAGANIA.md) | Wymagania projektu i ich stan |
| [Docker_Docs.md](docs/Docker_Docs.md) | Architektura kontenerów |
| [Scraper_Instrukcja.md](docs/Scraper_Instrukcja.md), [Scraper_Dzialanie.md](docs/Scraper_Dzialanie.md) | Uruchomienie i budowa scrapera |
| [Importer.md](docs/Importer.md) | Import danych do sklepu |
| [Webservice_API.md](docs/Webservice_API.md) | Konfiguracja Webservice API |
| [wyglad_strony.md](docs/wyglad_strony.md) | Wygląd sklepu i motyw potomny |
| [adr/](docs/adr/) | Decyzje architektoniczne |
| [AI_LOG.md](docs/AI_LOG.md) | Dziennik AI |
| [Business Model Canvas](docs/Business_Model_Canvas_LuksusoweAlkohole.md) | Zadanie z wykładu 2 |

## Rozwiązywanie problemów

### `make init` kończy się na `check-shop: BLAD`

Sklep nie działa albo jeszcze się instaluje. Uruchom `make up` i poczekaj, aż się zakończy. Jeśli `make up` zgłasza błąd albo kontener `shop` ma status `unhealthy`, przyczyna jest w `make logs SERVICE=shop` (np. linia `20-configure-sales: BLAD: ...`).

### `photos: BLAD: brak archiwum i nie udało się pobrać zdjęć z URL-i`

Nie udało się pobrać ani archiwum z Releases, ani zdjęć ze sklepu źródłowego. Sprawdź połączenie z internetem i adres `PHOTOS_RELEASE_URL` (np. czy tag wydania w zakładce Releases nie zmienił nazwy), a potem uruchom `make init` ponownie.

### `make import` kończy się błędem `Za mało produktów z minimum 2 zdjęciami` lub `Nie udało się wybrać N produktów`

Brakuje zdjęć w `scraper_results/product_photos/`. Uruchom `make photos` (patrz [krok 3](#3-zainicjalizuj-dane)).

### Zmienne środowiskowe nie są ustawione

Jeżeli podczas uruchamiania Docker Compose wyświetla ostrzeżenia o brakujących zmiennych, sprawdź, czy:

1. Plik `.env` istnieje w głównym katalogu projektu.
2. Wszystkie wymagane zmienne zostały uzupełnione.

### Sklep nie uruchamia się poprawnie

Sprawdź logi kontenerów:

```bash
make logs
```

Następnie sprawdź status usług:

```bash
make ps
```

`make up` czeka na koniec instalacji, więc jeśli zakończył się bez błędu, sklep działa. Jeśli kontener `shop` się zatrzymał, przyczyna jest w ostatnich liniach jego logu (`make logs SERVICE=shop`).

### Po aktualizacji sklep przekierowuje na zły adres lub w pętli

Domena sklepu i ustawienie SSL są zapisywane w bazie danych przy pierwszej instalacji. Po zmianie `HTTP_PORT`, `HTTPS_PORT` lub `SERVER_NAME` (albo po aktualizacji ze starszej wersji projektu) usuń istniejące dane i uruchom sklep od zera:

```bash
make reset
make up
```

Uwaga: `make reset` kasuje bazę danych, pliki sklepu (wolumen `shop_data`: zdjęcia produktów w sklepie, konfiguracja instalacji), wygenerowany certyfikat i lokalne mapowania importu (`scraper/importer/*_mapping.json`). Pobrane zdjęcia w `scraper_results/product_photos/` zostają. Potem wykonaj ponownie `make init`.

### Przeglądarka ostrzega o niezaufanym certyfikacie

To oczekiwane zachowanie, ponieważ certyfikat jest samopodpisany. Certyfikat zapisuje się w wolumenie Dockera, więc przy kolejnych uruchomieniach pozostaje ten sam i wyjątek w przeglądarce nie musi być dodawany ponownie. Dopiero `make reset` generuje nowy certyfikat.

### E-maile ze sklepu nie pojawiają się w Mailpicie

Sprawdź logi sklepu:

```bash
make logs SERVICE=shop
```

Przy starcie kontenera powinna pojawić się linia `10-configure-mail: ustawiam SMTP mail:1025`. Jeżeli zamiast tego widzisz `10-configure-mail: BLAD`, ustawienia poczty nie zostały zapisane (brak zmiennych `MAIL_SMTP_HOST` i `MAIL_SMTP_PORT` albo błąd konsoli PrestaShop).

Jeżeli linia z ustawieniem SMTP jest, a wiadomości nadal nie docierają, sprawdź, czy `MAIL_SMTP_HOST` w `deploy/compose.yaml` jest taki sam jak nazwa usługi z Mailpitem (`mail`). Niezgodność nie powoduje błędu w logach, tylko brak wiadomości w Mailpicie.