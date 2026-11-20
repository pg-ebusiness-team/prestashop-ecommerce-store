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
| `products.py`           | Normalizacja, walidacja i import produktów |
| `products_mapping.py`   | Mapowanie produktów i wariantów            |
| `combinations.py`       | Import kombinacji produktów                |
| `stock.py`              | Aktualizacja stanów magazynowych           |
| `images.py`             | Import zdjęć produktów                     |

## 3. Konfiguracja

Importer korzysta ze zmiennych środowiskowych zapisanych w `.env`.

Najważniejsze ustawienia:

| Zmienna                    | Zastosowanie                                                 |
| -------------------------- | ------------------------------------------------------------ |
| `PS_API_KEY`               | Klucz dostępu do Webservice API                              |
| `HTTP_PORT` / `HTTPS_PORT` | Porty sklepu                                                 |
| `PS_VERIFY_SSL`            | Weryfikacja certyfikatu SSL                                  |
| `PS_TAX_RULES_GROUP_MAP`   | Mapowanie stawek VAT na ID grup reguł podatkowych PrestaShop |

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
- Ogranicza import do maksymalnie 1100 produktów oraz pomija produkty bez dostępnych zdjęć.
- Przypisuje produkty do zaimportowanych kategorii.
- Importuje ceny netto, brutto i odpowiednie stawki VAT.
- Tworzy grupy atrybutów, wartości i kombinacje wariantów.
- Wylicza wagę produktu na podstawie rozpoznanej pojemności lub objętości; gdy nie można jej ustalić, stosuje wartość domyślną.
- Ustawia stany magazynowe produktów i ich kombinacji w zakresie 0–10 sztuk. Udział produktów ze stanem 0 jest utrzymywany w zakresie 5–20%.
- Przesyła zdjęcia z lokalnego katalogu `scraper_results/product_photos/` w formacie WEBP.

## 5. Mapowanie i idempotencja

Importer wykorzystuje pliki mapowania w `scraper/importer/`, które przechowują powiązania identyfikatorów źródłowych z identyfikatorami PrestaShop.

Mapowania pozwalają rozpoznawać wcześniej zaimportowane kategorie, produkty, atrybuty i warianty.

Pliki mapowania są zależne od konkretnej instancji sklepu i powinny pozostać lokalne. Nie należy zastępować ich mapowaniami pochodzącymi z innej instancji PrestaShop. Przy synchronizacji kategorii importer weryfikuje je również na podstawie istniejącej kategorii i jej kategorii nadrzędnej, dzięki czemu może odbudować nieaktualne lokalne mapowanie.

## 6. Uruchomienie

Polecenia należy wykonywać z katalogu głównego projektu.

**Dry-run – sprawdzenie importu bez modyfikowania sklepu:**

```bash
python -m scraper.importer.main --dry-run
```

**Właściwy import:**

```bash
python -m scraper.importer.main --execute
```

**Import przez Makefile:**

```bash
make import-categories  # import kategorii
make import-products    # import produktów
make import             # pełny import
```

Dry-run sprawdza dane wejściowe, ich poprawność, grupowanie oraz przewidywane operacje. Nie wykonuje zapisów w PrestaShop.

Właściwy import wymaga działającego sklepu, poprawnej konfiguracji `.env` i włączonego Webservice API.
