import xml.etree.ElementTree as ET

from scraper.importer.attributes_mapping import get_attribute_mapping
from scraper.importer.products_mapping import add_combination_mapping
from scraper.importer.products_mapping import save_mapping as save_products_mapping


def get_prestashop_attribute_ids(
    combination: dict,
    attributes_mapping: dict
) -> list[int]:
    """
    Zwraca ID wartości atrybutów w PrestaShop
    na podstawie mapowania ID źródłowych.
    """

    prestashop_ids = []

    for attribute in combination["attributes"].values():
        source_attribute_id = attribute["id_attribute"]

        mapping = get_attribute_mapping(
            attributes_mapping,
            source_attribute_id
        )

        if mapping is None:
            raise ValueError(
                f"Brak mapowania wartości atrybutu "
                f"{source_attribute_id} ({attribute['name']})."
            )

        prestashop_ids.append(mapping["prestashop_id"])

    return sorted(set(prestashop_ids))


def build_combination_xml(
    product_id: int,
    combination: dict,
    attribute_ids: list[int],
    combination_id: int | None = None
) -> str:
    """
    Buduje XML kombinacji zgodny z PrestaShop Webservice.
    """

    root = ET.Element(
        "prestashop",
        {"xmlns:xlink": "http://www.w3.org/1999/xlink"}
    )

    combination_element = ET.SubElement(root, "combination")

    if combination_id is not None:
        ET.SubElement(
            combination_element,
            "id"
        ).text = str(combination_id)

    ET.SubElement(
        combination_element,
        "id_product"
    ).text = str(product_id)

    ET.SubElement(
        combination_element,
        "minimal_quantity"
    ).text = "1"

    ean13 = combination.get("ean13")

    if ean13 and len(str(ean13)) == 13 and str(ean13).isdigit():
        ET.SubElement(
            combination_element,
            "ean13"
        ).text = str(ean13)

    # Powiązanie z wartościami atrybutów
    associations = ET.SubElement(
        combination_element,
        "associations"
    )

    option_values = ET.SubElement(
        associations,
        "product_option_values",
        {
            "nodeType": "product_option_value",
            "api": "product_option_values"
        }
    )

    for attribute_id in attribute_ids:
        option_value = ET.SubElement(
            option_values,
            "product_option_value"
        )

        ET.SubElement(
            option_value,
            "id"
        ).text = str(attribute_id)

    return ET.tostring(root, encoding="unicode")


def find_existing_combination(
    api,
    product_id: int,
    attribute_ids: list[int]
) -> int | None:
    """
    Wyszukuje kombinację produktu o dokładnie tych samych
    wartościach atrybutów.
    """

    response = api.get(
        "combinations",
        params={
            "filter[id_product]": f"[{product_id}]",
            "display": "full",
            "limit": "0,1000"
        }
    )

    root = ET.fromstring(response)

    expected_ids = sorted(attribute_ids)

    for combination in root.findall("./combinations/combination"):
        combination_id = combination.findtext("id")

        existing_ids = [
            int(element.text)
            for element in combination.findall(
                "./associations/product_option_values/"
                "product_option_value/id"
            )
            if element.text
        ]

        if sorted(existing_ids) == expected_ids:
            return int(combination_id)

    return None


def create_combination(
    api,
    combination_xml: str
) -> int:
    """
    Tworzy kombinację i zwraca jej ID w PrestaShop.
    """

    response = api.post(
        "combinations",
        combination_xml
    )

    root = ET.fromstring(response)

    combination_id = root.findtext("./combination/id")

    if combination_id is None:
        raise RuntimeError(
            "PrestaShop nie zwrócił ID utworzonej kombinacji."
        )

    return int(combination_id)


def update_combination(
    api,
    combination_id: int,
    combination_xml: str
) -> None:
    """
    Aktualizuje istniejącą kombinację,
    zachowując pozostałe pola zasobu.
    """

    response = api.get(f"combinations/{combination_id}")

    root = ET.fromstring(response)

    existing = root.find("./combination")

    if existing is None:
        raise RuntimeError(
            f"Nie znaleziono kombinacji {combination_id}."
        )

    new_root = ET.fromstring(combination_xml)
    new_combination = new_root.find("./combination")

    if new_combination is None:
        raise RuntimeError("Nieprawidłowy XML kombinacji.")

    for field in ["ean13", "minimal_quantity"]:
        new_value = new_combination.find(field)
        old_value = existing.find(field)

        if new_value is not None and old_value is not None:
            old_value.text = new_value.text

    # Aktualizuj także powiązane wartości atrybutów, jeśli źródło się zmieniło.
    new_associations = new_combination.find("associations")
    old_associations = existing.find("associations")
    if new_associations is not None:
        if old_associations is not None:
            existing.remove(old_associations)
        existing.append(new_associations)

    api.put(
        "combinations",
        combination_id,
        ET.tostring(root, encoding="unicode")
    )


def import_combination(
    api,
    product_id: int,
    combination: dict,
    products_mapping: dict,
    attributes_mapping: dict
) -> tuple[int, str] | None:
    """
    Tworzy lub aktualizuje kombinację produktu.

    Zwraca ID kombinacji w PrestaShop oraz rodzaj operacji.
    Pomija rekordy bez wartości atrybutów.
    """

    if not combination.get("attributes"):
        return None

    source_id = combination["source_id"]
    source_attribute_id = combination["source_attribute_id"]

    attribute_ids = get_prestashop_attribute_ids(
        combination,
        attributes_mapping
    )

    if not attribute_ids:
        return None

    product_mapping = products_mapping.get(str(source_id))

    if product_mapping is None:
        raise KeyError(
            f"Brak mapowania produktu źródłowego {source_id}."
        )

    # Sprawdzenie lokalnego mapowania kombinacji
    existing_id = product_mapping["combinations"].get(
        str(source_attribute_id)
    )

    # Jeżeli nie ma mapowania, szukamy kombinacji w PrestaShop
    if existing_id is None:
        existing_id = find_existing_combination(
            api,
            product_id,
            attribute_ids
        )

    combination_xml = build_combination_xml(
        product_id,
        combination,
        attribute_ids,
        existing_id
    )

    if existing_id is not None:
        try:
            update_combination(api, existing_id, combination_xml)
            operation = "updated"
        except RuntimeError as exc:
            # Lokalne mapowanie mogło wskazywać usuniętą kombinację.
            if "404" not in str(exc):
                raise
            existing_id = find_existing_combination(api, product_id, attribute_ids)
            if existing_id is not None:
                update_combination(api, existing_id, combination_xml)
                operation = "updated"
            else:
                existing_id = create_combination(api, combination_xml)
                operation = "created"
    else:
        existing_id = create_combination(api, combination_xml)
        operation = "created"

    # Zapis mapowania kombinacji
    add_combination_mapping(
        products_mapping,
        source_id,
        source_attribute_id,
        existing_id
    )

    save_products_mapping(products_mapping)

    return existing_id, operation
