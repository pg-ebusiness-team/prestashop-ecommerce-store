# prestashop-ecommerce-store

Sklep internetowy oparty na PrestaShop 8.2.8, uruchamiany w kontenerach Docker, wyposażony w automatyczny import danych ze scrapera oraz testy E2E w Playwright. Projekt obejmuje pełną obsługę zamówień, płatności i dostaw, analitykę GA4 oraz integrację z klastrem Docker Swarm.

Autorzy:
Bartosz Pacyga
Jakub Romanowski
Michał Kaźmierowski
Kacper Trznadel

## Uruchomienie projektu

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

Polecenie włącza Webservice API i rejestruje klucz `PS_API_KEY` z `.env` z uprawnieniami GET/POST/PUT/DELETE wyłącznie do zasobów `categories`, `products`, `combinations`, `stock_availables`, `images`. Można je uruchamiać wielokrotnie — nie tworzy duplikatów, a po zmianie klucza w `.env` zastępuje stary klucz nowym.

Poprawność konfiguracji API sprawdzisz poleceniem:

```bash
make api-check
```

Następnie włącz motyw sklepu:

```bash
make theme
```

Polecenie aktywuje motyw potomny `custom-child-theme` (dziedziczy po Classic) i czyści cache. Można je uruchamiać wielokrotnie.

### 5. Sprawdź status kontenerów

Aby sprawdzić, czy kontenery zostały uruchomione poprawnie, wykonaj:

```bash
make ps
```

Jeżeli chcesz obserwować logi na bieżąco, użyj:

```bash
make logs
```

Domyślnie pokazuje to logi wszystkich kontenerów. Aby zawęzić je do jednego, podaj nazwę usługi, np. `make logs SERVICE=proxy`.

### 6. Otwórz sklep

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

## Wygląd sklepu (motyw potomny)

Wygląd sklepu zmieniamy wyłącznie w motywie potomnym `shop/themes/custom-child-theme`. Plików motywu Classic nie edytujemy — pochodzi z obrazu PrestaShop i jest dziedziczony.

- `config/theme.yml` — konfiguracja motywu (`parent: classic`, `use_parent_assets: true`); sekcje `global_settings` i `theme_settings` są skopiowane z Classic, aby zachować hooki modułów, typy obrazków i układy stron.
- `assets/css/custom.css` — wszystkie własne style; PrestaShop ładuje go automatycznie po CSS Classic.

Motyw jest kopiowany do obrazu, więc po każdej zmianie w jego plikach wykonaj `make up` (przebudowa obrazu, dane zostają) i `make theme` (czyści cache).

## Rozwiązywanie problemów

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

Uwaga: `make reset` kasuje bazę danych oraz wygenerowany certyfikat.

### Przeglądarka ostrzega o niezaufanym certyfikacie

To oczekiwane zachowanie, ponieważ certyfikat jest samopodpisany. Certyfikat zapisuje się w wolumenie Dockera, więc przy kolejnych uruchomieniach pozostaje ten sam i wyjątek w przeglądarce nie musi być dodawany ponownie. Dopiero `make reset` generuje nowy certyfikat.

### E-maile ze sklepu nie pojawiają się w Mailpicie

Sprawdź logi sklepu:

```bash
make logs SERVICE=shop
```

Przy starcie kontenera powinna pojawić się linia `10-configure-mail: ustawiam SMTP mail:1025`. Jeżeli zamiast tego widzisz `10-configure-mail: BLAD`, ustawienia poczty nie zostały zapisane (brak zmiennych `MAIL_SMTP_HOST` i `MAIL_SMTP_PORT` albo błąd konsoli PrestaShop).

Jeżeli linia z ustawieniem SMTP jest, a wiadomości nadal nie docierają, sprawdź, czy `MAIL_SMTP_HOST` w `deploy/compose.yaml` jest taki sam jak nazwa usługi z Mailpitem (`mail`). Niezgodność nie powoduje błędu w logach, tylko brak wiadomości w Mailpicie.