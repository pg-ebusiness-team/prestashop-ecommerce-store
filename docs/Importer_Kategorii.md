# Importer kategorii (BACK-2)

Importer kategorii pobranych przez scraper i zapisuje je w PrestaShop za
pomocą Webservice API. Odpowiada za utworzenie kategorii głównych i
podkategorii z zachowaniem oryginalnej hierarchii (wymaganie D2 etapu
1).

## Co robi importer

-   odczytuje dane kategorii z pliku
    `scraper/kategorie_poprawiony.json`,
-   tworzy kategorie główne bezpośrednio pod kategorią `Home` (ID = 2),
-   tworzy podkategorie wewnątrz odpowiednich kategorii głównych,
-   zapisuje identyfikatory kategorii PrestaShop w osobnym pliku
    mapowania,
-   aktualizuje istniejące kategorie zamiast tworzyć duplikaty,
-   odzyskuje identyfikatory istniejących kategorii, jeśli brakuje ich w
    pliku mapowania,
-   generuje raport zawierający liczbę utworzonych, zaktualizowanych i
    odrzuconych kategorii.

## Struktura plików

  --------------------------------------------------------------------------------
  Plik                                         Zastosowanie
  -------------------------------------------- -----------------------------------
  `scraper/kategorie_poprawiony.json`          Źródłowe dane kategorii ze scrapera

  `scraper/importer/categories.py`             Główna logika importowania
                                               kategorii

  `scraper/importer/api_client.py`             Klient komunikujący się z
                                               PrestaShop Webservice API

  `scraper/importer/categories_mapping.py`     Obsługa mapowania adresów URL na
                                               identyfikatory PrestaShop

  `scraper/importer/categories_mapping.json`   Zapisane mapowanie kategorii i ich
                                               identyfikatorów
  --------------------------------------------------------------------------------

## Uruchomienie

Importer korzysta z istniejącej konfiguracji Webservice API
przygotowanej w ramach BACK-1.

Wymagane zmienne środowiskowe:

-   `PS_API_KEY` --- klucz dostępu do Webservice API,
-   `SHOP_URL` --- adres sklepu (opcjonalny; domyślnie
    `http://localhost:$(SHOP_PORT)`).

Uruchomienie importera z katalogu głównego projektu:

``` bash
set -a
source .env
set +a

python3 -m scraper.importer.categories
```

Importer można uruchamiać wielokrotnie. Nie wymaga ręcznego
przygotowywania kategorii w panelu administracyjnym.

## Mapowanie kategorii

Plik `categories_mapping.json` przechowuje powiązanie danych źródłowych
z identyfikatorami nadanymi przez PrestaShop.

Każda kategoria zawiera:

-   `name` --- nazwę kategorii,
-   `url` --- oryginalny adres URL kategorii ze scrapera,
-   `prestashop_id` --- identyfikator kategorii w PrestaShop.

Plik zachowuje oryginalną strukturę z podziałem na kategorie główne i
podkategorie.

Przykładowy fragment:

``` json
[
  {
    "main_category": {
      "name": "Prezenty",
      "url": "https://luksusowealkohole.pl/11-prezenty",
      "prestashop_id": 11
    },
    "subcategories": [
      {
        "name": "Kosze upominkowe",
        "url": "https://luksusowealkohole.pl/38-kosze-upominkowe",
        "prestashop_id": 12
      }
    ]
  }
]
```

Jeśli mapowanie nie zawiera identyfikatora kategorii, importer próbuje
odnaleźć istniejącą kategorię w PrestaShop na podstawie jej kategorii
nadrzędnej (`id_parent`) oraz adresu `link_rewrite`.

Jeśli nie znajdzie istniejącej kategorii, tworzy nową i zapisuje
otrzymane ID w pliku mapowania.

Jeżeli odnalezienie kategorii jest niejednoznaczne, importer zgłasza
błąd zamiast aktualizować przypadkowy rekord.

## Komunikacja z PrestaShop API

Komunikację obsługuje klasa `PrestaShopAPI` z pliku `api_client.py`.

Udostępnia metody:

  Metoda       Operacja HTTP   Zastosowanie
  ------------ --------------- ------------------------
  `get()`      GET             Pobieranie kategorii
  `post()`     POST            Tworzenie kategorii
  `put()`      PUT             Aktualizacja kategorii
  `delete()`   DELETE          Usuwanie kategorii

Żądania wykorzystują Basic Authentication, gdzie klucz API jest loginem,
a hasło pozostaje puste.

Dane przesyłane do PrestaShop są generowane w formacie XML.

**Kodowanie UTF-8:** dane XML są przesyłane jako bajty UTF-8
(`xml_data.encode("utf-8")`). Jest to istotne ze względu na polskie
znaki i znaki specjalne, np. `&`. Przesyłanie tekstu bezpośrednio jako
`str` mogło powodować nieprawidłowe obliczenie nagłówka `Content-Length`
i obcięcie dokumentu XML.

## Idempotencja

Importer jest zaprojektowany tak, aby wielokrotne uruchomienie nie
powodowało powstawania duplikatów.

Mechanizm działa następująco:

1.  Odczytuje identyfikator kategorii z pliku mapowania.
2.  Jeśli identyfikator istnieje, aktualizuje kategorię w PrestaShop.
3.  Jeśli identyfikatora brakuje, próbuje odnaleźć istniejącą kategorię
    przez API.
4.  Jeśli kategoria nie istnieje, tworzy ją i zapisuje jej identyfikator
    w mapowaniu.

Dzięki temu importer może wznowić pracę po częściowym niepowodzeniu bez
konieczności ponownego tworzenia poprawnie zaimportowanych kategorii.

## Raport importu

Po zakończeniu działania importer wyświetla podsumowanie:

``` text
========== RAPORT IMPORTU ==========

Utworzone kategorie:       9
Zaktualizowane kategorie:  30
Odrzucone kategorie:       0
------------------------------------
Łącznie przetworzono:      39
====================================
```

Liczby powyżej przedstawiają wynik jednego z testowych uruchomień, a nie
stały wynik każdego importu.

## Konfiguracja i ograniczenia

-   `ROOT_CATEGORY_ID = 2` --- identyfikator kategorii `Home`, pod którą
    tworzone są kategorie główne.
-   `LANGUAGE_ID = 1` --- identyfikator języka używany przy zapisie nazw
    i adresów `link_rewrite`.
-   Dane źródłowe pozostają w formacie JSON i nie są modyfikowane przez
    importer.
-   Domyślne kategorie PrestaShop pozostają nienaruszone.
-   Importer nie importuje produktów ani ich przypisań do kategorii.
-   Klucz API nie jest przechowywany w kodzie źródłowym --- pobierany
    jest ze zmiennych środowiskowych.

## Weryfikacja

Importer został przetestowany pod kątem:

  Test                                             Wynik
  ------------------------------------------------ -------
  Tworzenie kategorii (POST)                       PASS
  Pobieranie kategorii (GET)                       PASS
  Aktualizacja kategorii (PUT)                     PASS
  Usuwanie kategorii (DELETE)                      PASS
  Obsługa polskich znaków i znaków specjalnych     PASS
  Import 39 kategorii                              PASS
  Kompletność mapowania (39/39)                    PASS
  Idempotencja --- ponowny import bez duplikatów   PASS
  Poprawność hierarchii (39/39)                    PASS
  Zgodność nazw i `link_rewrite` (39/39)           PASS

Poprawność struktury została dodatkowo sprawdzona w panelu
administracyjnym PrestaShop, w sekcji **Katalog → Kategorie**.
