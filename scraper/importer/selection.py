import json
from collections import defaultdict
from pathlib import Path


# Katalog zawierający dane pobrane przez scraper
SOURCE_DIR = Path("scraper_results/products")

# Katalog zawierający pobrane zdjęcia produktów
PHOTOS_DIR = Path("scraper_results/product_photos")

# Brak stałego limitu liczby produktów; selector dobiera maksymalną pulę
# zgodną z wymaganiami dotyczącymi stanu magazynowego.
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


def _product_has_promotion(records):
    """Zwraca True, jeśli produkt ma co najmniej jedną importowalną promocję."""
    for record in records:
        promotions = record.get("specific_prices") or []
        if isinstance(promotions, dict) and promotions:
            return True
        if isinstance(promotions, list) and any(
            isinstance(item, dict) for item in promotions
        ):
            return True
    return False


def _make_synthetic_promotion(records):
    """Dodaje techniczną promocję 5% do produktu bez promocji źródłowej."""
    if _product_has_promotion(records):
        return False

    for record in records:
        try:
            regular_price = float(record.get("price_without_reduction"))
            vat_rate = float(record.get("rate"))
        except (TypeError, ValueError):
            continue

        current_raw = record.get("price_amount")
        try:
            current_price = float(current_raw) if current_raw not in (None, "") else regular_price
        except (TypeError, ValueError):
            continue

        existing = record.get("specific_prices") or []
        if isinstance(existing, dict):
            existing = [existing]
        if existing or bool(record.get("has_discount")):
            continue
        if regular_price <= 0 or current_price <= 0 or vat_rate < 0:
            continue
        if current_price < regular_price:
            continue

        # Reguła 5% od regularnej ceny netto. id_product_attribute=0
        # oznacza regułę dla całego produktu, także z wariantami.
        record["specific_prices"] = [{
            "id_product_attribute": 0,
            "id_shop": 0,
            "id_shop_group": 0,
            "id_currency": 0,
            "id_country": 0,
            "id_group": 0,
            "id_customer": 0,
            "id_cart": 0,
            "from_quantity": 1,
            "price": "-1.000000",
            "reduction": "0.05",
            "reduction_tax": 0,
            "reduction_type": "percentage",
            "from": "0000-00-00 00:00:00",
            "to": "0000-00-00 00:00:00",
        }]
        record["_synthetic_promotion"] = True
        return True

    return False


def _product_stock_state(records):
    """Zwraca 'zero', 'positive' albo 'unknown' na poziomie produktu."""
    quantities = [
        record.get("quantity")
        for record in records
        if isinstance(record.get("quantity"), int)
        and not isinstance(record.get("quantity"), bool)
        and record.get("quantity") >= 0
    ]

    if not quantities:
        return "unknown"
    if all(quantity == 0 for quantity in quantities):
        return "zero"
    return "positive"


def _product_has_multiple_photos(product_id, records, photos_dir):
    photo_ids = {
        image.get("id_image")
        for record in records
        for image in (record.get("images") or [])
        if isinstance(image, dict) and image.get("id_image") is not None
    }
    existing_photos = [
        image_id
        for image_id in photo_ids
        if (photos_dir / str(product_id) / f"{image_id}.webp").is_file()
    ]
    return len(existing_photos) >= 2


def select_products(
    valid_products,
    valid_categories,
    target=TARGET_PRODUCTS,
    photos_dir=PHOTOS_DIR,
    minimum_promoted_products=20,
    minimum_zero_stock_ratio=0.05,
    maximum_zero_stock_ratio=0.20,
):
    """
    Wybiera produkty, zachowując wymagania BACK-3-OPT oraz promocje.

    1. Zabezpiecza wszystkie niepuste podkategorie.
    2. Zabezpiecza minimum 50 produktów z co najmniej 2 zdjęciami.
    3. Wybiera minimum 20 różnych produktów z promocją.
    4. Pilnuje udziału produktów ze stanem 0 w zakresie 5-20%.
    5. Uzupełnia pulę do target, zachowując wszystkie rekordy wariantów.
    """
    if not 0 <= minimum_zero_stock_ratio <= maximum_zero_stock_ratio <= 1:
        raise ValueError("Nieprawidłowy zakres udziału produktów ze stanem 0.")

    photos_dir = Path(photos_dir)

    # Domyślnie nie ograniczamy selekcji do 1100 produktów.
    # Dobieramy maksymalną pulę, która może spełnić limit 5-20% produktów
    # ze stanem 0. Produkty ze stanem dodatnim lub nieznanym są kandydatami
    # do pełnej puli; nadmiar produktów ze stanem 0 pozostaje poza selekcją.
    if target is None:
        zero_products = sum(
            _product_stock_state(records) == "zero"
            for records in valid_products.values()
        )
        nonzero_or_unknown_products = len(valid_products) - zero_products

        max_zero_by_upper_ratio = int(
            nonzero_or_unknown_products * maximum_zero_stock_ratio
            / (1 - maximum_zero_stock_ratio)
        ) if maximum_zero_stock_ratio < 1 else zero_products

        target = nonzero_or_unknown_products + min(
            zero_products, max_zero_by_upper_ratio
        )

        # Jeśli produktów ze stanem 0 jest za mało, ograniczamy pulę tak,
        # aby nadal stanowiły co najmniej minimum wymagane procentowo.
        if minimum_zero_stock_ratio > 0:
            target = min(
                target,
                int(zero_products / minimum_zero_stock_ratio)
            )

    if target <= 0:
        raise ValueError(
            "Nie można wybrać produktów z zachowaniem wymaganego udziału "
            "produktów ze stanem 0."
        )

    selected_ids = set()
    selected_categories_required = set()

    # Ograniczenia procentowe liczymy względem docelowej puli produktów.
    minimum_zero_stock = int(target * minimum_zero_stock_ratio + 0.999999)
    maximum_zero_stock = int(target * maximum_zero_stock_ratio)

    def zero_count(product_ids):
        return sum(
            _product_stock_state(valid_products[product_id]) == "zero"
            for product_id in product_ids
        )

    def add_product(product_id, mandatory=False):
        if product_id in selected_ids:
            return True
        if len(selected_ids) >= target:
            return False

        state = _product_stock_state(valid_products[product_id])
        if state == "zero" and zero_count(selected_ids) >= maximum_zero_stock:
            return False

        selected_ids.add(product_id)
        if mandatory:
            selected_categories_required.add(product_id)
        return True

    # ETAP 1: pokrycie wszystkich podkategorii, jak w poprzednim selektorze.
    for category, product_ids in sorted(valid_categories.items()):
        candidates = sorted(product_ids, key=str)
        chosen = next((pid for pid in candidates if add_product(pid, mandatory=True)), None)
        if chosen is None and not any(pid in selected_ids for pid in candidates):
            raise ValueError(
                f"Nie można zabezpieczyć podkategorii {category!r} "
                "bez naruszenia limitu produktów lub stocku."
            )
        if chosen is None:
            selected_categories_required.update(
                pid for pid in candidates if pid in selected_ids
            )

    if len(selected_ids) > target:
        raise ValueError("Limit produktów jest zbyt mały dla wymaganej struktury kategorii.")

    # ETAP 2: minimum 50 produktów z >=2 zdjęciami.
    products_with_multiple_photos = [
        product_id
        for product_id, records in valid_products.items()
        if _product_has_multiple_photos(product_id, records, photos_dir)
    ]
    if len(products_with_multiple_photos) < 50:
        raise ValueError(
            "Za mało produktów z minimum 2 zdjęciami. "
            f"Wymagane: 50, dostępne: {len(products_with_multiple_photos)}."
        )

    selected_multiple_photos = {
        pid for pid in selected_ids if pid in products_with_multiple_photos
    }
    photo_candidates = sorted(
        products_with_multiple_photos,
        key=lambda pid: (
            _product_stock_state(valid_products[pid]) == "zero",
            str(pid),
        ),
    )
    for product_id in photo_candidates:
        if len(selected_multiple_photos) >= 50:
            break
        if product_id not in selected_ids and add_product(product_id):
            selected_multiple_photos.add(product_id)

    if len(selected_multiple_photos) < 50:
        raise ValueError(
            "Nie można wybrać wymaganych 50 produktów z minimum 2 zdjęciami "
            "bez przekroczenia limitu stanu zerowego."
        )

    # ETAP 3: minimum 20 różnych produktów promocyjnych.
    # Najpierw wykorzystujemy promocje ze źródła, następnie tworzymy
    # brakujące promocje 5% dla wybranych produktów bez rabatu.
    promoted_candidates = [
        product_id
        for product_id, records in valid_products.items()
        if _product_has_promotion(records)
    ]

    selected_promoted = {
        pid for pid in selected_ids if _product_has_promotion(valid_products[pid])
    }
    promoted_candidates.sort(
        key=lambda pid: (
            _product_stock_state(valid_products[pid]) == "zero",
            pid not in products_with_multiple_photos,
            str(pid),
        )
    )
    for product_id in promoted_candidates:
        if len(selected_promoted) >= minimum_promoted_products:
            break
        if product_id in selected_ids or add_product(product_id):
            selected_promoted.add(product_id)

    if len(selected_promoted) < minimum_promoted_products:
        synthetic_candidates = sorted(
            (
                pid for pid, records in valid_products.items()
                if not _product_has_promotion(records)
            ),
            key=lambda pid: (
                _product_stock_state(valid_products[pid]) == "zero",
                pid not in products_with_multiple_photos,
                str(pid),
            ),
        )

        for product_id in synthetic_candidates:
            if len(selected_promoted) >= minimum_promoted_products:
                break
            if product_id not in selected_ids and not add_product(product_id):
                continue
            if _make_synthetic_promotion(valid_products[product_id]):
                selected_promoted.add(product_id)

    if len(selected_promoted) < minimum_promoted_products:
        raise ValueError(
            "Nie udało się uzyskać wymaganej liczby produktów promocyjnych. "
            f"Wymagane: {minimum_promoted_products}, dostępne po promocjach "
            f"źródłowych i dodatkowych: {len(selected_promoted)}. "
            "Brakuje produktów z poprawną ceną regularną albo limit selekcji "
            "nie pozwala dodać kolejnych produktów."
        )

    # ETAP 4: zapewniamy minimum 5% produktów ze stanem 0.
    zero_candidates = sorted(
        (
            pid for pid in valid_products
            if _product_stock_state(valid_products[pid]) == "zero"
        ),
        key=lambda pid: (
            pid not in products_with_multiple_photos,
            not _product_has_promotion(valid_products[pid]),
            str(pid),
        ),
    )
    for product_id in zero_candidates:
        if zero_count(selected_ids) >= minimum_zero_stock:
            break
        add_product(product_id)

    if zero_count(selected_ids) < minimum_zero_stock:
        raise ValueError(
            "Nie można osiągnąć minimalnego udziału 5% produktów ze stanem 0. "
            f"Wybrano: {zero_count(selected_ids)}, wymagane: {minimum_zero_stock}."
        )

    # ETAP 5: uzupełnienie do wyliczonej puli; produkty ze stockiem dodatnim/nieznanym
    # wybieramy przed zerowymi, aby nie przekroczyć limitu 20%.
    remaining_candidates = sorted(
        (pid for pid in valid_products if pid not in selected_ids),
        key=lambda pid: (
            _product_stock_state(valid_products[pid]) == "zero",
            str(pid),
        ),
    )
    for product_id in remaining_candidates:
        if len(selected_ids) >= target:
            break
        add_product(product_id)

    if len(selected_ids) < target:
        raise ValueError(
            f"Nie udało się wybrać {target} produktów. "
            f"Wybrano: {len(selected_ids)}. Dostępnych: {len(valid_products)}. "
            "Sprawdź, czy limit stanu zerowego nie ogranicza puli."
        )

    selected_zero_stock = zero_count(selected_ids)
    zero_ratio = selected_zero_stock / target
    if not minimum_zero_stock_ratio <= zero_ratio <= maximum_zero_stock_ratio:
        raise ValueError(
            "Selekcja narusza wymagany udział produktów ze stanem 0: "
            f"{selected_zero_stock}/{target} ({zero_ratio:.1%}); "
            f"dozwolone {minimum_zero_stock_ratio:.0%}-{maximum_zero_stock_ratio:.0%}."
        )

    selected_promotion_count = sum(
        _product_has_promotion(valid_products[pid]) for pid in selected_ids
    )
    if selected_promotion_count < minimum_promoted_products:
        raise ValueError(
            f"Wynik selekcji zawiera tylko {selected_promotion_count} "
            "unikalnych produktów promocyjnych."
        )

    selected_products = {
        product_id: records
        for product_id, records in valid_products.items()
        if product_id in selected_ids
    }

    selected_categories = {}
    for category, product_ids in valid_categories.items():
        selected_category_ids = product_ids.intersection(selected_ids)
        if selected_category_ids:
            selected_categories[category] = selected_category_ids

    print(
        "Selekcja: "
        f"{len(selected_products)} produktów, "
        f"{selected_promotion_count} z promocją, "
        f"{selected_zero_stock} ze stanem 0 ({zero_ratio:.1%}), "
        f"{len(selected_multiple_photos)} z min. 2 zdjęciami."
    )

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
    valid_products = filter_products_with_photos(products)

    # ETAP 4: Aktualizacja struktury kategorii
    valid_categories = filter_categories(
        categories,
        valid_products
    )

    print("\n========== PO FILTROWANIU ==========")
    print("Produkty posiadające zdjęcia:", len(valid_products))
    print("Niepuste podkategorie:", len(valid_categories))

    # ETAP 5: Wybór maksymalnej puli zgodnej z ograniczeniami
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
