# prestashop-ecommerce-store

Sklep internetowy oparty na PrestaShop 8.x, uruchamiany w kontenerach Docker, wyposażony w automatyczny import danych ze scrapera oraz testy E2E w Playwright. Projekt obejmuje pełną obsługę zamówień, płatności i dostaw, analitykę GA4 oraz integrację z klastrem Docker Swarm.

## Uruchomienie projektu

### 1. Sklonuj repozytorium

Sklonuj repozytorium i przejdź do katalogu projektu:

```bash
cd prestashop-ecommerce-store
```

### 2. Przygotuj plik konfiguracyjny `.env`

Po sklonowaniu repozytorium skopiuj przykładowy plik konfiguracyjny `.example.env` do pliku `.env`:

```bash
cp .example.env .env
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

Jeżeli chcesz obserwować logi sklepu na bieżąco, użyj:

```bash
make logs
```

Adres sklepu oraz port, pod którym będzie dostępny, zależą od konfiguracji w pliku `.env`.

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