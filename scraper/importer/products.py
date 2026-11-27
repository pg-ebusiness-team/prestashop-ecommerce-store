import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

from scraper.importer.api_client import PrestaShopAPI
from scraper.importer.attributes_mapping import load_mapping as load_attributes_mapping
from scraper.importer.combinations import import_combination
from scraper.importer.images import import_product_images
from scraper.importer.products_mapping import (
    add_product_mapping,
    get_product_mapping,
    save_mapping,
)
from scraper.importer.stock import (
    import_stock,
    limit_combination_stock,
)
from scraper.importer.weights import assign_product_weights

LANGUAGE_ID = 1

# Konfiguracja importera
SOURCE_PATH = "scraper_results/products"
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
                raise TypeError("Dane produktu nie są obiektem JSON.")

            products.append({
                "data": product_data,
                "source_file": str(file_path)
            })

        except (json.JSONDecodeError, OSError, ValueError, TypeError) as e:
            print(f"Błąd odczytu pliku '{file_path}': {e}")
            rejected += 1

    print(f"Wczytane produkty: {len(products)}")
    print(f"Odrzucone pliki:   {rejected}")

    return products

def _to_decimal(value: object) -> Decimal | None:
    """Konwertuje wartość liczbową ze źródła bez błędów float."""
    if value is None or value == "":
        return None

    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None

    if not result.is_finite():
        return None

    return result


def _calculate_regular_net(price_gross: object, vat_rate: object) -> float | None:
    """Oblicza regularną cenę netto z regularnej ceny brutto i stawki VAT."""
    gross = _to_decimal(price_gross)
    rate = _to_decimal(vat_rate)

    if gross is None or rate is None or gross < 0 or rate < 0:
        return None

    divisor = Decimal("1") + rate / Decimal("100")
    if divisor <= 0:
        return None

    net = (gross / divisor).quantize(
        Decimal("0.000001"), rounding=ROUND_HALF_UP
    )
    return float(net)


def _extract_source_promotions(product: dict) -> list[dict]:
    """Zwraca promocje źródłowe w jednolitej postaci listy słowników."""
    raw_promotions = product.get("specific_prices")

    if isinstance(raw_promotions, dict):
        return [raw_promotions] if raw_promotions else []
    if isinstance(raw_promotions, list):
        return [item for item in raw_promotions if isinstance(item, dict)]
    return []


def _promotion_key(promotion: dict) -> tuple[str, ...]:
    """Klucz deduplikacji promocji powielonych w rekordach źródłowych."""
    fields = (
        "id_product_attribute",
        "id_shop",
        "id_shop_group",
        "id_currency",
        "id_country",
        "id_group",
        "id_customer",
        "from_quantity",
        "price",
        "reduction",
        "reduction_tax",
        "reduction_type",
        "from",
        "to",
    )
    return tuple(str(promotion.get(field, "")) for field in fields)


def normalize_product(product: dict) -> dict:
    """
    Normalizuje dane produktu pobrane przez scraper.

    Cena bazowa PrestaShop jest regularną ceną netto. Cena po rabacie
    oraz dane promocji są zachowywane osobno do synchronizacji specific_prices.
    """

    data = product["data"]
    regular_gross = data.get("price_without_reduction")
    vat_rate = data.get("rate")
    regular_net = _calculate_regular_net(regular_gross, vat_rate)

    return {
        # Identyfikatory produktu i wariantu w sklepie źródłowym
        "source_id": data.get("id_product"),
        "source_attribute_id": data.get("id_product_attribute"),
        # Default source combination can be present even when scraper returned
        # no usable attribute definitions for the product.
        "source_default_attribute_id": data.get("cache_default_attribute"),

        # Podstawowe informacje o produkcie
        "name": data.get("name"),
        "description": data.get("description", ""),
        "description_short": data.get("description_short", ""),

        # Cena bazowa: regularna cena brutto/netto, nie cena po rabacie
        "price_gross": regular_gross,
        "price_net": regular_net,
        "vat_rate": vat_rate,

        # Dane promocyjne zachowane osobno; nie trafiają do pola products.price
        "source_price_net": data.get("price_tax_exc"),
        "has_discount": bool(data.get("has_discount")),
        "specific_prices": data.get("specific_prices", []),
        "lowest_price_30d": data.get("lowest_price_30d"),
        "lowest_price_30d_amount": data.get("lowest_price_30d_amount"),

        # Stan magazynowy
        "quantity": data.get("quantity"),

        # Kategoria źródłowa
        "category": data.get("category"),
        "source_category_id": data.get("id_category_default"),

        # Dodatkowe informacje
        "attributes": data.get("attributes") or {},
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
    if (
        product.get("source_id") is not None
        and (
            not isinstance(product["source_id"], int)
            or product["source_id"] <= 0
        )
    ):
        errors.append("Nieprawidłowy identyfikator produktu.")

    # Sprawdzenie cen
    for field in ["price_gross", "price_net"]:
        value = product.get(field)

        if value is not None and (
            not isinstance(value, (int, float)) or value < 0
        ):
            errors.append(f"Nieprawidłowa wartość pola: {field}")

    # Sprawdzenie stawki VAT
    vat_rate = product.get("vat_rate")

    if vat_rate is not None and (
        not isinstance(vat_rate, (int, float)) or vat_rate < 0
    ):
        errors.append("Nieprawidłowa stawka VAT.")

    # Sprawdzenie struktury dodatkowych danych
    if not isinstance(product.get("attributes"), dict):
        errors.append("Pole attributes musi być słownikiem.")

    if not isinstance(product.get("features"), list):
        errors.append("Pole features musi być listą.")

    if not isinstance(product.get("images"), list):
        errors.append("Pole images musi być listą.")
        
    # Sprawdzenie stanu magazynowego
    quantity = product.get("quantity")

    if quantity is not None and (
        not isinstance(quantity, int)
        or isinstance(quantity, bool)
        or quantity < 0
    ):
        errors.append("Nieprawidłowa wartość stanu magazynowego.")

    return errors

def find_existing_product(product: dict, mapping: dict) -> dict | None:
    """
    Sprawdza, czy produkt istnieje w mapowaniu.

    Zwraca dane mapowania produktu lub None.
    """

    source_id = product["source_id"]

    return get_product_mapping(mapping, source_id)

def get_product_id(product: dict, mapping: dict) -> int | None:
    """
    Zwraca ID produktu w PrestaShop.

    Jeśli produkt nie istnieje w mapowaniu, zwraca None.
    """

    existing_product = find_existing_product(product, mapping)

    if existing_product is None:
        return None

    return existing_product["prestashop_id"]

def build_product_xml(
    product: dict,
    category_id: int,
    tax_rules_group_id: int,
    product_id: int | None = None
) -> str:
    """
    Buduje XML produktu zgodny z formatem PrestaShop Webservice.
    """

    root = ET.Element("prestashop")
    product_element = ET.SubElement(root, "product")
    
    if product_id is not None:
        ET.SubElement(product_element, "id").text = str(product_id)

    # Techniczny, unikalny identyfikator źródła umożliwia odzyskanie mapowania.
    ET.SubElement(product_element, "reference").text = f"SRC{product['source_id']}"

    # Nazwa produktu
    name = ET.SubElement(product_element, "name")
    language_name = ET.SubElement(name, "language", {"id": str(LANGUAGE_ID)})
    language_name.text = product["name"]

    # Link rewrite
    normalized_name = unicodedata.normalize("NFKD", product["name"])
    normalized_name = normalized_name.encode("ascii", "ignore").decode("ascii")
    link_rewrite = re.sub(r"[^a-zA-Z0-9]+", "-", normalized_name.lower()).strip("-")

    link = ET.SubElement(product_element, "link_rewrite")
    language_link = ET.SubElement(link, "language", {"id": str(LANGUAGE_ID)})
    language_link.text = link_rewrite

    # Opisy produktu
    for field in ["description", "description_short"]:
        element = ET.SubElement(product_element, field)
        language_element = ET.SubElement(
            element, "language", {"id": str(LANGUAGE_ID)}
        )
        language_element.text = product.get(field, "")

    # Cena netto
    ET.SubElement(product_element, "price").text = str(product["price_net"])

    # Kategoria
    ET.SubElement(product_element, "id_category_default").text = str(category_id)

    # Grupa reguł podatkowych VAT
    ET.SubElement(product_element, "id_tax_rules_group").text = str(tax_rules_group_id)

    # Waga bazowa produktu (kg)
    ET.SubElement(product_element, "weight").text = str(product.get("weight", 1.5))

    # Podstawowe ustawienia produktu
    ET.SubElement(product_element, "active").text = "1"
    ET.SubElement(product_element, "state").text = "1"
    ET.SubElement(product_element, "available_for_order").text = "1"
    ET.SubElement(product_element, "show_price").text = "1"
    ET.SubElement(product_element, "visibility").text = "both"

    # Powiązanie produktu z kategorią
    associations = ET.SubElement(product_element, "associations")
    categories = ET.SubElement(associations, "categories")
    category = ET.SubElement(categories, "category")
    ET.SubElement(category, "id").text = str(category_id)

    return ET.tostring(root, encoding="unicode")

def create_product(api: PrestaShopAPI, product_xml: str) -> int:
    """
    Tworzy produkt w PrestaShop i zwraca jego ID.
    """

    response = api.post("products", product_xml)

    root = ET.fromstring(response)

    product_id = root.find("./product/id")

    if product_id is None or product_id.text is None:
        raise RuntimeError(
            "PrestaShop nie zwrócił ID utworzonego produktu."
        )

    return int(product_id.text)

def update_product(
    api: PrestaShopAPI,
    product_id: int,
    product_xml: str
) -> None:
    """
    Aktualizuje istniejący produkt w PrestaShop.
    """

    api.put("products", product_id, product_xml)
    
def find_existing_product_by_source_id(api: PrestaShopAPI, source_id: int) -> int | None:
    """Odzyskuje ID produktu po technicznym reference ustawianym przez importer."""
    reference = f"SRC{source_id}"
    response = api.get(
        "products",
        params={
            "filter[reference]": f"[{reference}]",
            "display": "[id,reference]",
            "limit": "0,10",
        },
    )
    root = ET.fromstring(response)
    matches = root.findall("./products/product")
    if len(matches) > 1:
        raise RuntimeError(
            f"Więcej niż jeden produkt ma techniczny reference {reference}."
        )
    if not matches:
        return None
    value = matches[0].findtext("id")
    return int(value) if value else None


def import_product(
    api: PrestaShopAPI,
    product: dict,
    mapping: dict,
    category_id: int,
    tax_rules_group_id: int
) -> tuple[int, str]:
    """
    Tworzy lub aktualizuje produkt oraz jego kombinacje.

    Zwraca ID produktu w PrestaShop oraz rodzaj operacji.
    """

    existing_product_id = get_product_id(product, mapping)

    # Weryfikacja/odzyskanie ID, gdy lokalne mapowanie jest nieaktualne.
    if existing_product_id is not None:
        try:
            api.get(f"products/{existing_product_id}")
        except RuntimeError as exc:
            if "404" not in str(exc):
                raise
            existing_product_id = find_existing_product_by_source_id(
                api, product["source_id"]
            )
    else:
        existing_product_id = find_existing_product_by_source_id(
            api, product["source_id"]
        )

    product_xml = build_product_xml(
        product,
        category_id,
        tax_rules_group_id,
        existing_product_id
    )

    if existing_product_id is not None:
        product_id = existing_product_id
        update_product(api, product_id, product_xml)
        mapping.setdefault(str(product["source_id"]), {})["prestashop_id"] = product_id
        mapping[str(product["source_id"])].setdefault("combinations", {})
        operation = "updated"
    else:
        product_id = create_product(api, product_xml)
        add_product_mapping(mapping, product["source_id"], product_id)
        operation = "created"

    save_mapping(mapping)
    
    # Import kombinacji produktu i ich stanów magazynowych
    attributes_mapping = load_attributes_mapping()
    combinations = limit_combination_stock(
        product.get("combinations") or []
    )

    if not combinations:
        # Produkt prosty
        quantity = product.get("quantity")

        if quantity is not None:
            import_stock(
                api,
                product_id,
                quantity
            )

    else:
        # Produkt z wariantami
        for combination in combinations:
            result = import_combination(
                api,
                product_id,
                combination,
                mapping,
                attributes_mapping
            )

            if result is None:
                continue

            combination_id, _combination_operation = result
            quantity = combination.get("quantity")

            if quantity is not None:
                import_stock(
                    api,
                    product_id,
                    quantity,
                    combination_id
                )

    created_images, skipped_images = import_product_images(
        api,
        product_id,
        product,
        mapping
    )

    print(
        f"Zdjęcia produktu {product['source_id']}: "
        f"utworzono {created_images}, "
        f"pominięto {skipped_images}."
    )

    return product_id, operation

def group_products(products):
    grouped = {}

    for product in products:
        source_id = product["source_id"]
        attribute_id = product["source_attribute_id"]
        attributes = product.get("attributes") or {}

        if source_id not in grouped:
            grouped[source_id] = {
                **product,
                "source_attribute_id": None,
                "attributes": {},
                "quantity": None,
                "combinations": [],
                "promotions": [],
                "has_discount": False,
            }

        parent = grouped[source_id]

        # Zbieramy promocje również z rekordów wariantów, a nie tylko
        # z pierwszego rekordu produktu. Źródło może powielać je w kategoriach.
        existing_promotion_keys = {
            _promotion_key(promotion) for promotion in parent["promotions"]
        }
        for source_promotion in _extract_source_promotions(product):
            promotion = dict(source_promotion)
            if promotion.get("id_product_attribute") is None:
                promotion["id_product_attribute"] = (
                    product.get("source_attribute_id") or 0
                )
            promotion_key = _promotion_key(promotion)
            if promotion_key not in existing_promotion_keys:
                parent["promotions"].append(promotion)
                existing_promotion_keys.add(promotion_key)

        parent["has_discount"] = (
            parent["has_discount"] or bool(product.get("has_discount"))
        )

        # Scalanie zdjęć ze wszystkich rekordów produktu i wariantów
        existing_image_ids = {
            image.get("id_image") or image.get("id")
            for image in parent.get("images", [])
        }

        for image in product.get("images") or []:
            image_id = image.get("id_image") or image.get("id")

            if image_id is not None and image_id not in existing_image_ids:
                parent.setdefault("images", []).append(image)
                existing_image_ids.add(image_id)

        # Rekord wariantu z prawidłowymi atrybutami
        if attribute_id not in (None, 0) and attributes:
            existing_ids = {
                combination["source_attribute_id"]
                for combination in parent["combinations"]
            }

            if attribute_id not in existing_ids:
                parent["combinations"].append(product)

        # Produkt prosty lub rekord bez możliwych do odtworzenia atrybutów
        elif not attributes and not parent["combinations"]:
            parent["quantity"] = product.get("quantity")

    grouped_products = list(grouped.values())

    for product in grouped_products:
        assign_product_weights(product)

    return grouped_products
