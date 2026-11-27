import json
import re
from collections import defaultdict
from pathlib import Path

# Katalog zawierający dane pobrane przez scraper
SOURCE_DIR = Path("scraper_results/products")

# Katalog zawierający pobrane zdjęcia produktów
PHOTOS_DIR = Path("scraper_results/product_photos")

# Docelowa liczba produktów do importu; None = wszystkie poprawne (ze zdjęciem i opisem)
TARGET_PRODUCTS = None


def collect_products(source_dir=SOURCE_DIR):
    """
    Wczytuje pliki JSON i grupuje je według ID produktu.

    Dodatkowo zbiera informacje o kategoriach,
    w których występuje każdy produkt.
    """

    products = defaultdict(list)
    categories = defaultdict(set)

    # Pobieramy wszystkie pliki JSON z podkatalogów
    product_files = sorted(source_dir.rglob("*.json"))

    for file_path in product_files:

        # Odczytujemy zawartość pliku JSON
        with file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        # Pobieramy ID produktu
        product_id = data.get("id_product")

        # Pomijamy rekordy bez ID
        if product_id is None:
            continue

        # Dodajemy rekord do odpowiedniego produktu
        data["_source_file"] = str(file_path)
        products[product_id].append(data)

        # Odczytujemy ścieżkę względem katalogu products
        relative_path = file_path.relative_to(source_dir)

        # Pobieramy nazwę kategorii głównej i podkategorii
        main_category = relative_path.parts[0]
        subcategory = relative_path.parts[1]

        # Dodajemy produkt do odpowiedniej podkategorii
        categories[(main_category, subcategory)].add(product_id)

    return products, categories


def count_product_photos(products, photos_dir=PHOTOS_DIR):
    """
    Sprawdza liczbę zdjęć każdego unikalnego produktu.

    Zwraca:
    - no_photos: produkty bez zdjęć
    - one_photo: produkty z jednym zdjęciem
    - multiple_photos: produkty z minimum dwoma zdjęciami
    """

    no_photos = 0
    one_photo = 0
    multiple_photos = 0

    # Sprawdzamy każdy unikalny produkt
    for product_id, records in products.items():

        # Zbieramy identyfikatory zdjęć ze wszystkich rekordów
        photo_ids = set()

        for record in records:
            for image in record.get("images") or []:
                image_id = image.get("id_image")

                if image_id is not None:
                    photo_ids.add(image_id)

        # Sprawdzamy, które zdjęcia faktycznie istnieją na dysku
        existing_photos = [
            image_id
            for image_id in photo_ids
            if (photos_dir / str(product_id) / f"{image_id}.webp").is_file()
        ]

        # Przypisujemy produkt do odpowiedniej grupy
        if len(existing_photos) == 0:
            no_photos += 1
        elif len(existing_photos) == 1:
            one_photo += 1
        else:
            multiple_photos += 1

    return no_photos, one_photo, multiple_photos


def filter_products_with_photos(products, photos_dir=PHOTOS_DIR):
    """
    Pozostawia wyłącznie produkty posiadające przynajmniej
    jedno zdjęcie istniejące lokalnie na dysku.

    Zachowuje wszystkie rekordy danego produktu,
    w tym informacje o jego wariantach.
    """

    valid_products = {}

    for product_id, records in products.items():

        # Zbieramy identyfikatory wszystkich zdjęć produktu
        photo_ids = set()

        for record in records:
            for image in record.get("images") or []:

                image_id = image.get("id_image")

                if image_id is not None:
                    photo_ids.add(image_id)

        # Sprawdzamy, czy przynajmniej jedno zdjęcie istnieje na dysku
        has_photo = any(
            (photos_dir / str(product_id) / f"{image_id}.webp").is_file()
            for image_id in photo_ids
        )

        # Zachowujemy produkt wraz ze wszystkimi jego rekordami
        if has_photo:
            valid_products[product_id] = records

    return valid_products


def has_description(records) -> bool:
    """Czy któryś rekord produktu ma niepusty opis (po usunięciu tagów HTML)."""
    return any(
        re.sub(r"<[^>]*>|&nbsp;|\s", "", record.get("description") or "")
        for record in records
    )


def filter_products_with_description(products):
    """Pozostawia wyłącznie produkty z niepustym opisem."""
    return {
        product_id: records
        for product_id, records in products.items()
        if has_description(records)
    }


def filter_categories(categories, valid_products):
    """
    Aktualizuje strukturę kategorii na podstawie produktów,
    które przeszły filtrowanie zdjęć.

    Usuwa produkty niedopuszczone do importu oraz puste podkategorie.
    """

    valid_product_ids = set(valid_products.keys())
    valid_categories = {}

    for category, product_ids in categories.items():

        # Pozostawiamy wyłącznie produkty posiadające zdjęcia
        filtered_ids = product_ids.intersection(valid_product_ids)

        # Zapisujemy tylko niepuste podkategorie
        if filtered_ids:
            valid_categories[category] = filtered_ids

    return valid_categories


def select_products(
    valid_products,
    valid_categories,
    target=TARGET_PRODUCTS,
    photos_dir=PHOTOS_DIR
):
    """
    Wybiera docelową liczbę produktów.

    1. Najpierw zabezpiecza każdą niepustą podkategorię.
    2. Następnie uzupełnia pulę do docelowej liczby produktów.
    3. Zachowuje wszystkie rekordy wybranych produktów.
    """

    if target is None:
        target = len(valid_products)

    selected_ids = set()

    # ETAP 1: Zabezpieczenie wszystkich niepustych podkategorii.
    # Wybieramy przynajmniej jeden produkt z każdej podkategorii.
    for category, product_ids in sorted(valid_categories.items()):

        for product_id in sorted(product_ids, key=str):

            if product_id not in selected_ids:
                selected_ids.add(product_id)
                break

    # Sprawdzamy, czy liczba wymaganych produktów
    # z podkategorii nie przekracza naszego limitu.
    if len(selected_ids) > target:
        raise ValueError(
            "Limit produktów jest zbyt mały dla wymaganej "
            "struktury kategorii."
        )


    # ETAP 2: Zabezpieczenie minimum 50 produktów
    # posiadających co najmniej 2 zdjęcia lokalne.

    products_with_multiple_photos = []

    # Sprawdzamy wszystkie produkty, które przeszły filtr zdjęć.
    for product_id, records in valid_products.items():

        photo_ids = set()

        # Zbieramy identyfikatory zdjęć ze wszystkich rekordów produktu.
        for record in records:
            for image in record.get("images") or []:
                image_id = image.get("id_image")

                if image_id is not None:
                    photo_ids.add(image_id)

        # Sprawdzamy, które zdjęcia rzeczywiście istnieją na dysku.
        existing_photos = [
            image_id
            for image_id in photo_ids
            if (photos_dir / str(product_id) / f"{image_id}.webp").is_file()
        ]

        # Jeżeli produkt ma minimum 2 zdjęcia, kwalifikuje się.
        if len(existing_photos) >= 2:
            products_with_multiple_photos.append(product_id)

    # Sprawdzamy, czy dane źródłowe pozwalają spełnić wymóg.
    if len(products_with_multiple_photos) < 50:
        raise ValueError(
            "Za mało produktów z minimum 2 zdjęciami. "
            f"Wymagane: 50, dostępne: {len(products_with_multiple_photos)}."
        )

    # Sprawdzamy, ile produktów wielozdjęciowych już wybraliśmy
    # podczas zabezpieczania podkategorii.
    selected_multiple_photos = selected_ids.intersection(
        products_with_multiple_photos
    )

    # Dobieramy kolejne produkty, aż osiągniemy wymagane 50.
    for product_id in products_with_multiple_photos:

        if len(selected_multiple_photos) >= 50:
            break

        if product_id not in selected_ids:
            selected_ids.add(product_id)
            selected_multiple_photos.add(product_id)

    # ETAP 3: Uzupełnienie puli do docelowej liczby produktów.
    for product_id in valid_products:

        if product_id in selected_ids:
            continue

        selected_ids.add(product_id)

        if len(selected_ids) == target:
            break

    # Sprawdzamy, czy udało się osiągnąć docelową liczbę.
    if len(selected_ids) < target:
        raise ValueError(
            f"Nie udało się wybrać {target} produktów. "
            f"Dostępnych produktów: {len(selected_ids)}."
        )

    # Budujemy słownik wybranych produktów.
    # Zachowujemy wszystkie rekordy każdego produktu,
    # w tym informacje o jego wariantach.
    selected_products = {
        product_id: records
        for product_id, records in valid_products.items()
        if product_id in selected_ids
    }

    # Aktualizujemy strukturę kategorii na podstawie wybranych produktów.
    selected_categories = {}

    for category, product_ids in valid_categories.items():

        selected_category_ids = product_ids.intersection(selected_ids)

        if selected_category_ids:
            selected_categories[category] = selected_category_ids

    return selected_products, selected_categories

def run_selection(
    source_dir=SOURCE_DIR,
    photos_dir=PHOTOS_DIR,
    target=TARGET_PRODUCTS
):
    """
    Uruchamia pełny proces selekcji produktów.

    Zwraca:
    - selected_products
    - selected_categories
    """

    source_dir = Path(source_dir)
    photos_dir = Path(photos_dir)

    # Wczytanie danych źródłowych
    products, categories = collect_products(source_dir)

    # Odrzucenie produktów bez lokalnych zdjęć
    valid_products = filter_products_with_photos(
        products,
        photos_dir
    )

    # Odrzucenie produktów bez opisu
    valid_products = filter_products_with_description(valid_products)

    # Aktualizacja struktury kategorii
    valid_categories = filter_categories(
        categories,
        valid_products
    )

    # Wybór docelowej liczby produktów
    selected_products, selected_categories = select_products(
        valid_products,
        valid_categories,
        target,
        photos_dir
    )

    return selected_products, selected_categories

if __name__ == "__main__":

    # ETAP 1: Wczytanie danych źródłowych
    products, categories = collect_products()

    print("\n========== DANE ŹRÓDŁOWE ==========")
    print("Unikalne produkty:", len(products))
    print("Podkategorie:", len(categories))

    # ETAP 2: Diagnostyka zdjęć
    no_photos, one_photo, multiple_photos = count_product_photos(products)

    print("\n========== ZDJĘCIA W DANYCH ŹRÓDŁOWYCH ==========")
    print("Produkty bez zdjęć:", no_photos)
    print("Produkty z jednym zdjęciem:", one_photo)
    print("Produkty z minimum 2 zdjęciami:", multiple_photos)

    # ETAP 3: Odrzucenie produktów bez zdjęć
    valid_products = filter_products_with_description(
        filter_products_with_photos(products)
    )

    # ETAP 4: Aktualizacja struktury kategorii
    valid_categories = filter_categories(
        categories,
        valid_products
    )

    print("\n========== PO FILTROWANIU ==========")
    print("Produkty ze zdjęciem i opisem:", len(valid_products))
    print("Niepuste podkategorie:", len(valid_categories))

    # ETAP 5: Wybór produktów
    selected_products, selected_categories = select_products(
        valid_products,
        valid_categories
    )

    # ETAP 6: Podsumowanie
    print("\n========== WYNIK SELEKCJI ==========")
    print("Wybrane produkty:", len(selected_products))
    print("Zachowane podkategorie:", len(selected_categories))

    # Statystyki zdjęć wybranych produktów
    selected_no_photos, selected_one_photo, selected_multiple_photos = (
        count_product_photos(selected_products)
    )

    print("\n========== ZDJĘCIA WYBRANYCH PRODUKTÓW ==========")
    print("Produkty bez zdjęć:", selected_no_photos)
    print("Produkty z jednym zdjęciem:", selected_one_photo)
    print("Produkty z minimum 2 zdjęciami:", selected_multiple_photos)
