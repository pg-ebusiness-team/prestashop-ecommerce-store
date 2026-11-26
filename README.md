# prestashop-ecommerce-store

Sklep internetowy oparty na PrestaShop 8.2.8, uruchamiany w kontenerach Docker, wyposażony w automatyczny import danych ze scrapera oraz testy E2E w Playwright. Etap 1 obejmuje sklep w Docker Compose, scraper, import danych i konfigurację sprzedaży. Wdrożenie na klaster Docker Swarm i analityka GA4 są planowane w etapie 2. Wymagania i ich stan: [docs/WYMAGANIA.md](docs/WYMAGANIA.md).

Autorzy:
Bartosz Pacyga
Jakub Romanowski
Michał Kaźmierowski
Kacper Trznadel

## Uruchomienie projektu

Wymagania: Docker z Compose v2, `make`, `openssl`, `curl` i Python 3.12 (`make init` i `make import` uruchamiają skrypty Pythona na hoście). Testy E2E wymagają dodatkowo Node.js 18+.

### 1. Sklonuj repozytorium

Sklonuj repozytorium i przejdź do katalogu projektu:

```bash
cd prestashop-ecommerce-store
```

### 2. Przygotuj plik konfiguracyjny `.env`

Po sklonowaniu repozytorium skopiuj przykładowy plik konfiguracyjny `.env.example` do pliku `.env`:

```bash
cp .env.example .env
```

Następnie otwórz plik `.env` i uzupełnij wszystkie wymagane zmienne środowiskowe poprawnymi wartościami.

Klucz Webservice API (`PS_API_KEY`) musi mieć dokładnie 32 znaki `A-Z0-9`. Wygeneruj go poleceniem:

```bash
openssl rand -hex 16 | tr a-f A-F
```

Zainstaluj też zależności Pythona w środowisku wirtualnym. Środowisko musi być aktywne przy `make init` i `make import`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r scraper/requirements.txt
```

### 3. Uruchom sklep

Z poziomu głównego katalogu projektu wykonaj polecenie:

```bash
make up
```

Polecenie zbuduje wymagane obrazy Docker i uruchomi kontenery w tle.

Przy pierwszym uruchomieniu proces może potrwać dłużej, ponieważ Docker musi pobrać wymagane obrazy i zbudować środowisko.

### 4. Zainicjalizuj dane

Gdy instalacja PrestaShop się zakończy (w `make logs` pojawi się `Almost ! Starting web server now`), wykonaj:

```bash
make init
```
Polecenie włącza Webservice API i rejestruje klucz `PS_API_KEY` z `.env` z uprawnieniami GET/POST/PUT/DELETE wyłącznie do zasobów `categories`, `products`, `combinations`, `stock_availables`, `images`, `product_options`, `product_option_values`, `product_features`, `product_feature_values`. Na końcu usuwa przez API kategorie i produkty demonstracyjne z instalatora. Można je uruchamiać wielokrotnie — nie tworzy duplikatów, a po zmianie klucza w `.env` zastępuje stary klucz nowym.

Poprawność konfiguracji API sprawdzisz poleceniem:

```bash
make api-check
```

Następnie włącz motyw sklepu:

```bash
make theme
```

Polecenie aktywuje motyw potomny `custom-child-theme` (dziedziczy po Classic), pobiera grafiki strony głównej ze sklepu źródłowego (lista w `deploy/init/home-images.txt`, wymaga internetu, do konsultacji), wgrywa treści strony głównej z `deploy/init/theme.sql` (slider, kafelki kategorii, banery, logo), treści stron CMS (Dostawa, Polityka prywatności, Regulamin, O nas, Płatności) z plików HTML w `shop/cms/` (metadane w `deploy/init/cms.sql`) i czyści cache. Można je uruchamiać wielokrotnie — treści ustawione w panelu dla slidera, bloku tekstowego i stron CMS zostaną nadpisane wersją z repo.

### 5. Zaimportuj produkty

Produkty i kategorie pochodzą z `scraper_results/` (w repo), ale zdjęć w repo nie ma. Bez nich `make import` kończy się błędem, bo importer wybiera tylko produkty ze zdjęciami na dysku.

1. Pobierz archiwum zdjęć z zakładki **Releases** repozytorium (wydanie `photos_v0.1`).
2. Rozpakuj je tak, aby pliki leżały w `scraper_results/product_photos/<id_produktu>/<id_zdjecia>.webp`.
3. Uruchom import:

```bash
make import
```

Import tworzy kategorie, atrybuty, 1100 produktów z wariantami, stany magazynowe i zdjęcia. Ponowne uruchomienie aktualizuje istniejące rekordy. Podgląd bez zapisu: `make import IMPORT_ARGS=--dry-run`. Szczegóły: [docs/Importer.md](docs/Importer.md).

Po imporcie ustaw filtry w lewej kolumnie list produktów i wgraj opisy kategorii:

```bash
make facets
make categories
```

`make facets` zakłada w module `ps_facetedsearch` zestawy filtrów dla grup kategorii, tak jak w sklepie źródłowym (lista w `deploy/init/facets.php`), i przebudowuje indeks filtrów. `make categories` wpisuje opisy kategorii z plików HTML w `shop/categories/` (lista kategorii w `deploy/init/categories.sql`). Część pliku po znaczniku `<!-- więcej -->` jest zwinięta pod przyciskiem „Pokaż więcej”. Oba polecenia dopasowują kategorie (i cechy) po nazwie, więc przed importem zgłoszą ich brak. Uruchom je ponownie po każdym imporcie. Filtry i opisy ustawione w panelu zostaną nadpisane wersją z repo.

### 6. Sprawdź status kontenerów

Aby sprawdzić, czy kontenery zostały uruchomione poprawnie, wykonaj:

```bash
make ps
```

Jeżeli chcesz obserwować logi na bieżąco, użyj:

```bash
make logs
```

Domyślnie pokazuje to logi wszystkich kontenerów. Aby zawęzić je do jednego, podaj nazwę usługi, np. `make logs SERVICE=proxy`.

### 7. Otwórz sklep

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

Motyw jest kopiowany do obrazu, więc po każdej zmianie w jego plikach wykonaj `make up` (przebudowa obrazu, dane zostają) i `make theme` (czyści cache).

## Testy E2E (Playwright)

Wymagany Node.js 18+. Przy uruchomionym sklepie wykonaj:

```bash
make test-e2e
```

Polecenie instaluje zależności i przeglądarkę Chromium, a następnie uruchamia testy z katalogu `tests/e2e/` na adresie `https://localhost:${HTTPS_PORT}`. Inny adres sklepu podasz przez `make test-e2e SHOP_URL=https://adres`.

Raport HTML zapisuje się w `tests/playwright-report/` (podgląd: `cd tests && npx playwright show-report`), a zrzuty ekranu nieudanych testów w `tests/test-results/`.

Jeden plik lub jeden test: `cd tests && BASE_URL=https://localhost:8443 npx playwright test e2e/koszyk.spec.ts` (filtr po nazwie: `-g "Koszyk"`, podgląd przeglądarki: `--headed`).

| Plik | Co sprawdza |
|---|---|
| `tests/e2e/smoke.spec.ts` | strona główna się ładuje |
| `tests/e2e/koszyk.spec.ts` | kroki 1–3 scenariusza W4: 10 produktów z co najmniej 2 kategorii w różnych ilościach, wyszukanie produktu i dodanie losowego wyniku, usunięcie 3 pozycji z koszyka |

Kroki 4–10 scenariusza W4 (rejestracja, zamówienie, płatność, przewoźnik, status, faktura) nie są jeszcze napisane. Cały scenariusz musi trwać ≤5 min.

Test koszyka wymaga zaimportowanych produktów (`make import`) i kategorii w górnym menu, bo z menu wybiera kategorie. Produkty bez wystarczającego stanu pomija. Test, który klika po stronie, musi przed wejściem ustawić w `localStorage` `cookie-consent` i `age-confirmed` (jak w `koszyk.spec.ts`), inaczej baner cookies i okno 18+ zasłaniają stronę ([ADR 0002](docs/adr/0002-baner-cookies.md)).

## Testy jednostkowe i linter

Z aktywnym środowiskiem Pythona (patrz krok 2), bez uruchomionego sklepu. To samo robi CI przy każdym PR do `main`:

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

### `ModuleNotFoundError: No module named 'requests'` przy `make init` lub `make import`

Środowisko Pythona nie jest aktywne albo nie ma zależności (patrz krok 2). Klucz API jest już wtedy zarejestrowany; po naprawie uruchom `make init` ponownie, aby usunąć dane demo.

### `make import` kończy się błędem `Za mało produktów z minimum 2 zdjęciami` lub `Nie udało się wybrać 1100 produktów`

Brakuje zdjęć w `scraper_results/product_photos/` (patrz krok 5).

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

Pierwsze uruchomienie sklepu może potrwać dłuższą chwilę dlatego upewnij się, że sklep zdążył połączyć się z bazą danych.

### Po aktualizacji sklep przekierowuje na zły adres lub w pętli

Domena sklepu i ustawienie SSL są zapisywane w bazie danych przy pierwszej instalacji. Po zmianie `HTTP_PORT`, `HTTPS_PORT` lub `SERVER_NAME` (albo po aktualizacji ze starszej wersji projektu) usuń istniejące dane i uruchom sklep od zera:

```bash
make reset
make up
```

Uwaga: `make reset` kasuje bazę danych, wygenerowany certyfikat i lokalne mapowania importu (`scraper/importer/*_mapping.json`). Potem wykonaj ponownie kroki 4 i 5.

### Przeglądarka ostrzega o niezaufanym certyfikacie

To oczekiwane zachowanie, ponieważ certyfikat jest samopodpisany. Certyfikat zapisuje się w wolumenie Dockera, więc przy kolejnych uruchomieniach pozostaje ten sam i wyjątek w przeglądarce nie musi być dodawany ponownie. Dopiero `make reset` generuje nowy certyfikat.

### E-maile ze sklepu nie pojawiają się w Mailpicie

Sprawdź logi sklepu:

```bash
make logs SERVICE=shop
```

Przy starcie kontenera powinna pojawić się linia `10-configure-mail: ustawiam SMTP mail:1025`. Jeżeli zamiast tego widzisz `10-configure-mail: BLAD`, ustawienia poczty nie zostały zapisane (brak zmiennych `MAIL_SMTP_HOST` i `MAIL_SMTP_PORT` albo błąd konsoli PrestaShop).

Jeżeli linia z ustawieniem SMTP jest, a wiadomości nadal nie docierają, sprawdź, czy `MAIL_SMTP_HOST` w `deploy/compose.yaml` jest taki sam jak nazwa usługi z Mailpitem (`mail`). Niezgodność nie powoduje błędu w logach, tylko brak wiadomości w Mailpicie.