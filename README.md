# prestashop-ecommerce-store

Sklep internetowy oparty na PrestaShop 8.x, uruchamiany w kontenerach Docker, wyposażony w automatyczny import danych ze scrapera oraz testy E2E w Playwright. Projekt obejmuje pełną obsługę zamówień, płatności i dostaw, analitykę GA4 oraz integrację z klastrem Docker Swarm.

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

### 3. Uruchom sklep

Z poziomu głównego katalogu projektu wykonaj polecenie:

```bash
make up
```

Polecenie zbuduje wymagane obrazy Docker i uruchomi kontenery w tle.

Przy pierwszym uruchomieniu proces może potrwać dłużej, ponieważ Docker musi pobrać wymagane obrazy i zbudować środowisko.

### 4. Sprawdź status kontenerów

Aby sprawdzić, czy kontenery zostały uruchomione poprawnie, wykonaj:

```bash
make ps
```

Jeżeli chcesz obserwować logi na bieżąco, użyj:

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