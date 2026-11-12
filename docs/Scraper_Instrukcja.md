# Scraper — instrukcja obsługi

Scraper pobiera kategorie, produkty (z wariantami) i zdjęcia ze sklepu źródłowego [luksusowealkohole.pl](https://luksusowealkohole.pl) do plików, z których korzysta import. Opis działania: [Scraper_Dzialanie.md](Scraper_Dzialanie.md).

## Instalacja

Wymagany Python 3.12 (ta sama wersja co w CI).

```bash
cd scraper
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uruchomienie

```bash
cd scraper
python main.py          # pełny przebieg
python main.py --help   # lista argumentów
```

- Scraper wysyła maks. 2 zapytania na sekundę (wymaganie projektu), więc pełny przebieg trwa długo.
- Przerwanie (Ctrl+C) jest bezpieczne. Kolejne uruchomienie wznawia pracę: pomija ukończone podkategorie i pobrane produkty.
- Wyniki trafiają do `scraper_results/` w katalogu głównym repozytorium, niezależnie od katalogu, z którego uruchomiono scraper.

## Argumenty

| Argument | Działanie |
| --- | --- |
| *(brak)* | Pełny przebieg, wznawia od tego, co już zapisane. |
| `--clean` | Usuwa wszystkie wyniki i zdjęcia przed startem; wszystko pobiera się od nowa. |
| `--category NAZWA` | Tylko jedna kategoria główna, np. `--category "Whisky & Bourbon"`. Wielkość liter bez znaczenia. |
| `--save-categories` | Zapisuje drzewo kategorii do `scraper_results/debug/categories.json`. |
| `--load-categories` | Czyta drzewo kategorii z tego pliku zamiast ze strony. |
| `--save-listings` | Zapisuje URL-e produktów każdej podkategorii do `scraper_results/debug/listings.json`. |

## Typowe scenariusze

**Szybki test na małej kategorii**

```bash
python main.py --category "Wino & Champagne"
```

**Poprawienie uciętych nazw kategorii**

Sklep skraca długie nazwy podkategorii (np. `Zestawy alkoholi na...`), a nazwy trafiają do nazw folderów i dalej do importu.

```bash
python main.py --save-categories
# plik zapisuje się na starcie — po komunikacie "Checking photos of saved products" można przerwać (Ctrl+C)
# popraw nazwy w scraper_results/debug/categories.json
python main.py --load-categories --clean
```

Nie łącz `--save-categories` z `--category` — plik zawierałby wtedy tylko tę jedną kategorię.

**Pobranie wszystkiego od zera**

```bash
python main.py --clean
```

## Wyniki

```
scraper_results/
├── products/<kategoria>/<podkategoria>/<strona>/
│   ├── 1026_variant_1138.json   # produkt 1026, wariant 1138
│   ├── 3092_no_variants.json    # produkt bez wariantów
│   └── _done                    # (w folderze podkategorii) podkategoria ukończona
├── product_photos/<id_produktu>/<id_image>.webp
└── debug/
    ├── categories.json          # --save-categories
    └── listings.json            # --save-listings
```

- Produkt należący do kilku kategorii ma kopię swoich JSON-ów w folderze każdej z nich.
- Zdjęcia są zapisane raz na produkt, w jednym rozmiarze (`large_default`, 881×1000). Pozostałe rozmiary sklep generuje przy imporcie.

## Uwagi do importu

- Zdjęcia są w formacie **WebP**, mimo że sklep źródłowy podaje je pod adresami `.jpg`.
- Zdjęcia wariantu: lista `images` w jego JSON-ie. Pole `associatedVariants` przy zdjęciu to ID wariantów (`id_product_attribute`); pusta lista = zdjęcie wspólne dla produktu.
- Nazwa pliku zdjęcia to jego `id_image`.
- Zdjęcie główne bierz z `cover` — jest ustawione dla produktu, a nie dla wariantu.
- Pole `id_image` na najwyższym poziomie JSON-a (`pl-default`) to obrazek zastępczy — pomiń.
- Cena: `price_amount` (liczba) lub `price` (tekst z twardą spacją przed `zł`).

## Testy i linter

Uruchamiane w CI przy każdym PR do `main`. Lokalnie, z katalogu głównego repozytorium:

```bash
scraper/.venv/bin/ruff check scraper/
scraper/.venv/bin/pytest scraper/
```

Testy nie łączą się ze sklepem — działają na stronach zapisanych w `scraper/fixtures/`.

## Problemy

| Objaw | Przyczyna i rozwiązanie |
| --- | --- |
| `Error for <url>: ...` w konsoli | Błąd jednego produktu. Scraper idzie dalej, a podkategoria nie dostaje `_done` — zostanie powtórzona przy następnym uruchomieniu. |
| `Retry 1/3 for ...` | Timeout albo błąd serwera; zapytanie jest ponawiane po 2, 4 i 8 s. |
| `Category '...' not found. Available: ...` | Zła nazwa w `--category`; użyj jednej z wypisanych. |
| `categories.json not found` | `--load-categories` bez wcześniejszego `--save-categories`. |
| Produktu brakuje w nowej podkategorii po wznowieniu | Podkategorie z `_done` są pomijane. Nowe produkty w sklepie pojawią się dopiero po usunięciu `_done` albo `--clean`. |
