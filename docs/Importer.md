# Importer danych do PrestaShop (BACK-2 / BACK-3)

## 1. Opis

Importer umożliwia przeniesienie danych ze sklepu źródłowego do PrestaShop 8 za pomocą Webservice API.

Obejmuje dwa zakresy:

- **BACK-2 – Kategorie:** import kategorii głównych i podkategorii z zachowaniem hierarchii.
- **BACK-3 – Produkty:** import produktów, cen, VAT, atrybutów, wariantów, stanów magazynowych i zdjęć.

Importer obsługuje tworzenie nowych rekordów oraz aktualizowanie istniejących, ograniczając powstawanie duplikatów przy ponownym uruchomieniu.

## 2. Struktura plików

| Plik                    | Odpowiedzialność                           |
| ----------------------- | ------------------------------------------ |
| `main.py`               | Główny punkt wejścia i koordynacja importu |
| `api_client.py`         | Komunikacja z PrestaShop API               |
| `categories.py`         | Import kategorii                           |
| `categories_mapping.py` | Mapowanie kategorii                        |
| `attributes.py`         | Import grup i wartości atrybutów           |
| `attributes_mapping.py` | Mapowanie atrybutów                        |
| `features.py`           | Import cech produktów (zakładka „Szczegóły”) |
| `products.py`           | Normalizacja, walidacja i import produktów |
| `products_mapping.py`   | Mapowanie produktów i wariantów            |
| `combinations.py`       | Import kombinacji produktów                |
| `stock.py`              | Aktualizacja stanów magazynowych           |
| `images.py`             | Import zdjęć produktów                     |
| `selection.py`          | Wybór poprawnych produktów do importu      |
| `weights.py`            | Wyliczanie wag produktów i wariantów       |
| `import_attributes.py`  | Osobny import samych atrybutów             |
| `cleanup_demo.py`       | Usuwanie danych demo (`make cleanup-demo`, część `make init`) |

## 3. Konfiguracja

Importer korzysta ze zmiennych środowiskowych zapisanych w `.env`.

Najważniejsze ustawienia:

| Zmienna                    | Zastosowanie                                                 |
| -------------------------- | ------------------------------------------------------------ |
| `PS_API_KEY`               | Klucz dostępu do Webservice API                              |
| `HTTPS_PORT`               | Port sklepu w domyślnym adresie `https://localhost:<port>`   |
| `SHOP_URL`                 | Adres sklepu, gdy inny niż domyślny (opcjonalnie; kontener `tools` ustawia `https://proxy`) |
| `PS_SHOP_HOST`             | Domena sklepu wysyłana w nagłówku `Host`, gdy `SHOP_URL` wskazuje inny adres niż domena sklepu (ustawia ją kontener `tools`) |
| `PS_VERIFY_SSL`            | Weryfikacja certyfikatu SSL                                  |
| `PS_TAX_RULES_GROUP_MAP`   | Mapowanie stawek VAT na ID grup reguł podatkowych PrestaShop |
| `PS_IMPORT_WORKERS`        | Liczba wątków importu produktów (domyślnie 8, opcjonalnie)   |

**Mapowanie VAT:** identyfikatory w `PS_TAX_RULES_GROUP_MAP` muszą odpowiadać grupom reguł podatkowych istniejącym w danej instancji PrestaShop. Przykładowe wartości z `.env.example` nie muszą być prawidłowe dla innego sklepu.

## 4. Działanie importera

### Kategorie (BACK-2)

Dane kategorii pobierane są z `scraper_results/debug/categories.json`.

Importer:

- Tworzy kategorie główne pod kategorią `Home`.
- Tworzy podkategorie we właściwych kategoriach nadrzędnych.
- Wykorzystuje lokalne mapowanie identyfikatorów.
- Weryfikuje istniejące kategorie i aktualizuje mapowanie, aby ponowne uruchomienie nie tworzyło duplikatów.
- Aktualizuje istniejące kategorie zamiast tworzyć duplikaty.

### Produkty (BACK-3)

Dane produktów pobierane są z plików JSON znajdujących się w `scraper_results/products/`.

Importer:

- Normalizuje i waliduje dane.
- Grupuje rekordy dotyczące tego samego produktu.
- Wybiera wszystkie poprawne produkty, czyli takie, które mają zdjęcie na dysku i niepusty opis (pusty HTML też odpada). `--limit N` ogranicza import do N produktów (np. `--limit 1100`). Selektor zawsze zapewnia co najmniej 1 produkt w każdej niepustej podkategorii i co najmniej 50 produktów z ≥2 zdjęciami. Gdy danych lub zdjęć jest za mało, kończy się błędem.
- Przypisuje produkt do wszystkich kategorii, w których występuje w źródle. Kategorią domyślną (okruszki, adres URL) jest pierwsza z nich.
- Importuje ceny netto, brutto i odpowiednie stawki VAT.
- Tworzy grupy atrybutów, wartości i kombinacje wariantów. Wariant dostaje dopłatę do ceny: różnicę ceny netto względem pierwszego wariantu produktu.
- Wylicza wagę produktu na podstawie rozpoznanej pojemności lub objętości; gdy nie można jej ustalić, stosuje wartość domyślną.
- Ustawia stany magazynowe produktów i ich kombinacji w zakresie 0–10 sztuk. Udział produktów ze stanem 0 jest utrzymywany w zakresie 5–20%.
- Tworzy cechy produktów (Kraj, Region, Alkohol, Kolor, Rodzaj, Szczep, Charakter, Wiek) i ich wartości, a następnie przypisuje je produktom — sklep pokazuje je w sekcji „Szczegóły” karty produktu. Cechy i wartości są rozpoznawane po nazwie (bez pliku mapowania), kolejność cech odpowiada źródłu.
- Ustawia stany magazynowe produktów i ich kombinacji.
- Szacuje wagę (w kg) z pojemności (1,5 × litry + 0,25), a gdy jej brak — z gramatury (+ 0,05 na opakowanie). Gdy nie da się ustalić żadnej, przyjmuje 1,5 kg.
- Ustawia stany magazynowe ze źródła. Przy produktach z wariantami ogranicza łączny stan do 10 sztuk. Udziału produktów ze stanem 0 (wymagane 5–20%) importer nie wymusza, wynika on z danych źródłowych. Zakres i udział sprawdza `docs/stock_validation.sql` (ostatni pomiar: 10,45%, wpis z 2026-11-20 w `AI_LOG.md`).
- Przesyła zdjęcia z lokalnego katalogu `scraper_results/product_photos/` w formacie WEBP.
- Importuje produkty równolegle (domyślnie 8 wątków, `--workers N` lub `PS_IMPORT_WORKERS`). Każdy wątek obsługuje cały jeden produkt: dane, kombinacje, stany i zdjęcia. Kategorie, atrybuty i cechy importują się wcześniej, sekwencyjnie. Zapis `products_mapping.json` jest chroniony blokadą i atomowy (plik tymczasowy + podmiana). Równoległe zapisy produktów trafiają czasem na deadlock MySQL przy indeksowaniu wyszukiwarki (`Search::indexation`). PrestaShop zwraca wtedy HTTP 500 z pustą treścią, więc importer ponawia produkt do 3 razy przy każdym błędzie 5xx (`PRODUCT_ATTEMPTS` w `main.py`, w logu `HTTP 5xx, ponawiam (1/2)`). Ponowienie nie tworzy duplikatów, bo produkt jest odnajdywany po `reference` (sekcja 5). Gdy błędy 5xx lub timeouty powtarzają się mimo to, zmniejsz liczbę wątków (`--workers 1` = dawny import sekwencyjny).

## 5. Mapowanie i idempotencja

Importer wykorzystuje pliki mapowania w `scraper/importer/`, które przechowują powiązania identyfikatorów źródłowych z identyfikatorami PrestaShop.

Mapowania pozwalają rozpoznawać wcześniej zaimportowane kategorie, produkty, atrybuty i warianty.

Gdy produktu nie ma w mapowaniu albo wskazane ID już nie istnieje, importer szuka go w sklepie po polu `reference` (`SRC<id źródłowe>`). Zdjęcia są rozpoznawane wyłącznie po mapowaniu, dlatego:

- przy działającym sklepie **nie usuwaj** `products_mapping.json` — ponowny import wgra zdjęcia drugi raz,
- `make reset` sam usuwa mapowania — stare ID mogłyby trafić na inne produkty w nowej bazie. Jeśli bazę czyścisz inaczej (np. `docker compose down -v`), usuń je ręcznie: `rm -f scraper/importer/*_mapping.json`.

Pliki mapowania są zależne od konkretnej instancji sklepu i powinny pozostać lokalne. Nie należy zastępować ich mapowaniami pochodzącymi z innej instancji PrestaShop. Przy synchronizacji kategorii importer weryfikuje je również na podstawie istniejącej kategorii i jej kategorii nadrzędnej, dzięki czemu może odbudować nieaktualne lokalne mapowanie.

## 6. Uruchomienie

Pełny import jest częścią `make init` (patrz [README](../README.md), krok 3). Osobno importer uruchamiają polecenia make, które wykonują go w kontenerze narzędziowym `tools` (Python z zależnościami, montowane repo; opis w [Docker_Docs.md](Docker_Docs.md)). Na komputerze nie potrzeba więc Pythona. Polecenia wykonuje się z katalogu głównego projektu, przy działającym sklepie (`make up`). Zdjęcia muszą być w `scraper_results/product_photos/` (`make photos`), także przy dry-run.

**Import przez Makefile:**

```bash
make import             # pełny import
make import-categories  # import kategorii
make import-products    # import produktów
```

**Dry-run – sprawdzenie importu bez modyfikowania sklepu:**

```bash
make import IMPORT_ARGS=--dry-run
```

**Import z inną liczbą wątków lub limitem produktów:**

```bash
make import IMPORT_ARGS="--execute --workers 4"
make import IMPORT_ARGS="--execute --limit 100"
```

Bez make, w środowisku Pythona z zależnościami z `scraper/requirements.txt` (README, sekcja „Testy jednostkowe i linter”), importer łączy się z `https://localhost:<HTTPS_PORT>`:

```bash
python -m scraper.importer.main --dry-run
python -m scraper.importer.main --execute
```

Dry-run sprawdza dane wejściowe, ich poprawność, grupowanie oraz przewidywane operacje. Nie wykonuje zapisów w PrestaShop i nie łączy się ze sklepem, więc podział na „utworzone” i „zaktualizowane” wynika tylko z lokalnych mapowań.

Właściwy import wymaga działającego sklepu, poprawnej konfiguracji `.env` i włączonego Webservice API.
