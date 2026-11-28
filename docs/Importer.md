# Importer danych do PrestaShop (BACK-2 / BACK-3)

## 1. Opis

Importer przenosi wyniki scrapera do PrestaShop 8 przez Webservice API: kategorie z hierarchią (BACK-2) oraz produkty z cenami, VAT, atrybutami, wariantami, stanami, zdjęciami, promocjami i cenami Omnibus (BACK-3, D3). Ponowne uruchomienie aktualizuje istniejące rekordy zamiast tworzyć duplikaty.

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
| `promotions.py`         | Synchronizacja promocji (`specific_prices`) |
| `omnibus.py`            | Wysyłka najniższej ceny z 30 dni do modułu `omnibusprice` |
| `import_attributes.py`  | Osobny import samych atrybutów             |
| `cleanup_demo.py`       | Usuwanie danych demo (`make cleanup-demo`, część `make init`) |

## 3. Konfiguracja

Importer czyta zmienne z `.env`:

| Zmienna                    | Zastosowanie                                                 |
| -------------------------- | ------------------------------------------------------------ |
| `PS_API_KEY`               | Klucz dostępu do Webservice API                              |
| `HTTPS_PORT`               | Port sklepu w domyślnym adresie `https://localhost:<port>`   |
| `SHOP_URL`                 | Adres sklepu, gdy inny niż domyślny (opcjonalnie; kontener `tools` ustawia `https://proxy`) |
| `PS_SHOP_HOST`             | Domena sklepu wysyłana w nagłówku `Host`, gdy `SHOP_URL` wskazuje inny adres niż domena sklepu (ustawia ją kontener `tools`) |
| `PS_VERIFY_SSL`            | Weryfikacja certyfikatu SSL                                  |
| `PS_TAX_RULES_GROUP_MAP`   | Mapowanie stawek VAT na ID grup reguł podatkowych PrestaShop |
| `PS_IMPORT_WORKERS`        | Liczba wątków importu produktów (domyślnie 8, opcjonalnie)   |

ID w `PS_TAX_RULES_GROUP_MAP` muszą odpowiadać grupom reguł podatkowych danej instancji; wartości z `.env.example` pasują do domyślnej polskiej instalacji.

## 4. Działanie importera

### Kategorie (BACK-2)

Źródło: `scraper_results/debug/categories.json`. Kategorie główne trafiają pod `Home`, podkategorie pod swoje kategorie nadrzędne. Istniejące kategorie są rozpoznawane po mapowaniu oraz po nazwie i rodzicu, więc są aktualizowane, a nieaktualne mapowanie się odbudowuje.

### Produkty (BACK-3)

Źródło: JSON-y w `scraper_results/products/`. Importer:

- normalizuje, waliduje i grupuje rekordy (warianty jednego produktu),
- wybiera poprawne produkty: zdjęcie na dysku i niepusty opis. `--limit N` ogranicza ich liczbę; selektor zawsze daje ≥1 produkt w każdej niepustej podkategorii i ≥50 produktów z ≥2 zdjęciami, a przy braku danych kończy się błędem,
- przypisuje produkt do wszystkich kategorii ze źródła; domyślną (okruszki, URL) jest pierwsza,
- ustawia ceny netto i brutto oraz VAT; wariant dostaje dopłatę = różnicę ceny netto względem pierwszego wariantu,
- tworzy grupy atrybutów, wartości i kombinacje,
- tworzy cechy (Kraj, Region, Alkohol, Kolor, Rodzaj, Szczep, Charakter, Wiek) widoczne w „Szczegółach” karty produktu; rozpoznaje je po nazwie, bez pliku mapowania,
- szacuje wagę: 1,5 × litry + 0,25 kg, bez pojemności z gramatury (+0,05 kg), w ostateczności 1,5 kg,
- ustawia stany ze źródła, przy wariantach ograniczając łączny stan do 10. Udziału zer (5–20%) nie wymusza — wynika ze źródła; sprawdza go `docs/stock_validation.sql` (2026-11-28: stany 0–10, 11,02% zer),
- przesyła zdjęcia WebP z `scraper_results/product_photos/`,
- na końcu, sekwencyjnie, synchronizuje promocje i ceny Omnibus (niżej).

**Równoległość.** Produkty idą w 8 wątkach (`--workers N` lub `PS_IMPORT_WORKERS`), każdy wątek obsługuje cały produkt; kategorie, atrybuty i cechy wcześniej, sekwencyjnie. Zapis `products_mapping.json` jest pod blokadą i atomowy. Równoległe zapisy trafiają czasem na deadlock MySQL przy indeksowaniu wyszukiwarki (HTTP 500), więc produkt jest ponawiany do 3 razy przy każdym 5xx (`HTTP 5xx, ponawiam (1/2)` w logu) — bez duplikatów, bo jest odnajdywany po `reference`. Gdy błędy się powtarzają, zmniejsz liczbę wątków (`--workers 1`).

### Promocje i Omnibus (D3)

Etap po imporcie produktów, bo potrzebuje ich ID z mapowania. Dry-run pokazuje tylko liczbę planowanych promocji i cen.

- **Promocje** (`promotions.py`): pole `specific_prices` z JSON-a trafia do zasobu `specific_prices`. Reguła jest dopasowywana po zakresie (produkt, wariant, sklep, waluta, kraj, grupa, klient, koszyk, ilość, typ rabatu), więc ponowny import ją aktualizuje.
- **Omnibus** (`omnibus.py`): `lowest_price_30d_amount` (lub `lowest_price_30d`) produktu i wariantów idzie jednym `POST /module/omnibusprice/sync` do modułu `omnibusprice` (README, sekcja „Promocje i Omnibus”), który musi być zainstalowany (`make omnibus-install`). Rekordy bez ceny lub mapowania są pomijane.

Raport ma osobne sekcje dla promocji i Omnibus; błąd jednego produktu liczy się jako odrzucony i nie przerywa importu.

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
