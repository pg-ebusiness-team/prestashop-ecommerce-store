import json
from pathlib import Path


# Konfiguracja importera
SOURCE_PATH = "scraper/products"
MAPPING_PATH = "scraper/importer/products_mapping.json"


def load_products(source_path: str | Path = SOURCE_PATH) -> list[dict]:
    """
    Wczytuje wszystkie pliki JSON z katalogu produktów.

    Zwraca listę rekordów zawierających:
    - data: dane produktu,
    - source_file: ścieżkę do pliku źródłowego.

    Nie usuwa duplikatów, ponieważ mogą reprezentować warianty
    tego samego produktu.
    """

    source_directory = Path(source_path)

    if not source_directory.exists():
        raise FileNotFoundError(
            f"Nie znaleziono katalogu z produktami: {source_directory}"
        )

    if not source_directory.is_dir():
        raise NotADirectoryError(
            f"Ścieżka nie jest katalogiem: {source_directory}"
        )

    product_files = sorted(source_directory.rglob("*.json"))

    products = []
    rejected = 0

    for file_path in product_files:
        try:
            with file_path.open("r", encoding="utf-8") as file:
                product_data = json.load(file)

            if not isinstance(product_data, dict):
                raise ValueError("Dane produktu nie są obiektem JSON.")

            products.append({
                "data": product_data,
                "source_file": str(file_path)
            })

        except (json.JSONDecodeError, OSError, ValueError) as e:
            print(f"Błąd odczytu pliku '{file_path}': {e}")
            rejected += 1

    print(f"Wczytane produkty: {len(products)}")
    print(f"Odrzucone pliki:   {rejected}")

    return products

def normalize_product(product: dict) -> dict:
    """
    Normalizuje dane produktu pobrane przez scraper.

    Wybiera tylko pola potrzebne do importu do PrestaShop
    i nadaje im spójne nazwy.
    """

    data = product["data"]

    return {
        # Identyfikatory produktu i wariantu w sklepie źródłowym
        "source_id": data.get("id_product"),
        "source_attribute_id": data.get("id_product_attribute"),

        # Podstawowe informacje o produkcie
        "name": data.get("name"),
        "description": data.get("description", ""),
        "description_short": data.get("description_short", ""),

        # Ceny i podatek VAT
        "price_gross": data.get("price_without_reduction"),
        "price_net": data.get("price_tax_exc"),
        "vat_rate": data.get("rate"),

        # Kategoria źródłowa
        "category": data.get("category"),
        "source_category_id": data.get("id_category_default"),

        # Dodatkowe informacje
        "attributes": data.get("attributes", {}),
        "features": data.get("features", []),

        # Zdjęcia produktu
        "images": data.get("images", [])
    }
    
def validate_product(product: dict) -> list[str]:
    """
    Sprawdza poprawność znormalizowanych danych produktu.

    Zwraca listę błędów. Pusta lista oznacza poprawne dane.
    """

    errors = []

    # Sprawdzenie wymaganych pól
    required_fields = [
        "source_id",
        "name",
        "price_gross",
        "price_net",
        "vat_rate",
        "category"
    ]

    for field in required_fields:
        if product.get(field) is None or product.get(field) == "":
            errors.append(f"Brak wymaganego pola: {field}")

    # Sprawdzenie identyfikatora produktu
    if product.get("source_id") is not None:
        if not isinstance(product["source_id"], int) or product["source_id"] <= 0:
            errors.append("Nieprawidłowy identyfikator produktu.")

    # Sprawdzenie cen
    for field in ["price_gross", "price_net"]:
        value = product.get(field)

        if value is not None:
            if not isinstance(value, (int, float)) or value < 0:
                errors.append(f"Nieprawidłowa wartość pola: {field}")

    # Sprawdzenie stawki VAT
    vat_rate = product.get("vat_rate")

    if vat_rate is not None:
        if not isinstance(vat_rate, (int, float)) or vat_rate < 0:
            errors.append("Nieprawidłowa stawka VAT.")

    # Sprawdzenie struktury dodatkowych danych
    if not isinstance(product.get("attributes"), dict):
        errors.append("Pole attributes musi być słownikiem.")

    if not isinstance(product.get("features"), list):
        errors.append("Pole features musi być listą.")

    if not isinstance(product.get("images"), list):
        errors.append("Pole images musi być listą.")

    return errors