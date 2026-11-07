import xml.etree.ElementTree as ET

from .api_client import PrestaShopAPI
from .attributes_mapping import (
    add_attribute_mapping,
    add_group_mapping,
    get_attribute_mapping,
    get_group_mapping,
    load_mapping,
    save_mapping,
)

LANGUAGE_ID = 1


def build_group_xml(name: str, language_id: int = LANGUAGE_ID) -> str:
    """
    Buduje XML grupy atrybutów PrestaShop.
    """

    root = ET.Element("prestashop")
    group = ET.SubElement(root, "product_option")

    is_color_group = ET.SubElement(group, "is_color_group")
    is_color_group.text = "0"

    group_type = ET.SubElement(group, "group_type")
    group_type.text = "select"

    name_element = ET.SubElement(group, "name")
    language = ET.SubElement(name_element, "language")
    language.set("id", str(language_id))
    language.text = name

    public_name = ET.SubElement(group, "public_name")
    language = ET.SubElement(public_name, "language")
    language.set("id", str(language_id))
    language.text = name

    return ET.tostring(root, encoding="unicode")


def build_attribute_xml(
    name: str,
    group_id: int,
    language_id: int = LANGUAGE_ID
) -> str:
    """
    Buduje XML wartości atrybutu PrestaShop.
    """

    root = ET.Element("prestashop")
    attribute = ET.SubElement(root, "product_option_value")

    id_group = ET.SubElement(attribute, "id_attribute_group")
    id_group.text = str(group_id)

    name_element = ET.SubElement(attribute, "name")
    language = ET.SubElement(name_element, "language")
    language.set("id", str(language_id))
    language.text = name

    return ET.tostring(root, encoding="unicode")

def find_existing_group(
    api: PrestaShopAPI,
    name: str,
    language_id: int = LANGUAGE_ID
) -> int | None:
    """
    Wyszukuje grupę atrybutów w PrestaShop po nazwie.

    Zwraca ID znalezionej grupy lub None.
    """

    response = api.get(
        "product_options",
        params={
            "display": "[id,name]",
            "limit": "0,1000"
        }
    )

    response_xml = ET.fromstring(response)
    groups = response_xml.findall(".//product_option")

    matching_groups = []

    for group in groups:
        id_element = group.find("id")

        if id_element is None or id_element.text is None:
            continue

        name_element = group.find("name")

        if name_element is None:
            continue

        for language in name_element.findall("language"):
            if (
                language.get("id") == str(language_id)
                and language.text == name
            ):
                matching_groups.append(int(id_element.text))

    if len(matching_groups) > 1:
        raise ValueError(
            f"Znaleziono wiele grup atrybutów o nazwie '{name}'."
        )

    if not matching_groups:
        return None

    return matching_groups[0]


def create_attribute_group(
    api: PrestaShopAPI,
    name: str
) -> int:
    """
    Tworzy grupę atrybutów w PrestaShop.

    Zwraca ID utworzonej grupy.
    """

    xml_data = build_group_xml(name)

    response = api.post("product_options", xml_data)

    response_xml = ET.fromstring(response)

    id_element = response_xml.find(".//product_option/id")

    if id_element is None or id_element.text is None:
        raise ValueError(
            "PrestaShop API nie zwróciło ID utworzonej grupy atrybutów."
        )

    return int(id_element.text)

def import_attribute_group(
    api: PrestaShopAPI,
    source_group_id: int,
    name: str,
    mapping: dict
) -> int:
    """
    Importuje grupę atrybutów lub aktualizuje jej mapowanie.

    Zwraca ID grupy w PrestaShop.
    """

    # 1. Sprawdzenie lokalnego mapowania
    existing_mapping = get_group_mapping(mapping, source_group_id)

    if existing_mapping is not None:
        return existing_mapping["prestashop_id"]

    # 2. Wyszukanie grupy w PrestaShop
    prestashop_id = find_existing_group(api, name)

    # 3. Utworzenie grupy, jeśli nie istnieje
    if prestashop_id is None:
        prestashop_id = create_attribute_group(api, name)

    # 4. Zapisanie mapowania
    add_group_mapping(
        mapping,
        source_group_id,
        prestashop_id,
        name
    )

    save_mapping(mapping)

    return prestashop_id

def find_existing_attribute(
    api: PrestaShopAPI,
    name: str,
    group_id: int,
    language_id: int = LANGUAGE_ID
) -> int | None:
    """
    Wyszukuje wartość atrybutu w określonej grupie.

    Zwraca ID znalezionej wartości lub None.
    """

    response = api.get(
        "product_option_values",
        params={
            "filter[id_attribute_group]": f"[{group_id}]",
            "display": "[id,id_attribute_group,name]",
            "limit": "0,1000"
        }
    )

    response_xml = ET.fromstring(response)
    attributes = response_xml.findall(".//product_option_value")

    matching_attributes = []

    for attribute in attributes:
        id_element = attribute.find("id")

        if id_element is None or id_element.text is None:
            continue

        name_element = attribute.find("name")

        if name_element is None:
            continue

        for language in name_element.findall("language"):
            if (
                language.get("id") == str(language_id)
                and language.text == name
            ):
                matching_attributes.append(int(id_element.text))

    if len(matching_attributes) > 1:
        raise ValueError(
            f"Znaleziono wiele wartości '{name}' "
            f"w grupie o ID {group_id}."
        )

    if not matching_attributes:
        return None

    return matching_attributes[0]

def create_attribute_value(
    api: PrestaShopAPI,
    name: str,
    group_id: int
) -> int:
    """
    Tworzy wartość atrybutu w PrestaShop.

    Zwraca ID utworzonej wartości.
    """

    xml_data = build_attribute_xml(name, group_id)

    response = api.post("product_option_values", xml_data)

    response_xml = ET.fromstring(response)

    id_element = response_xml.find(
        ".//product_option_value/id"
    )

    if id_element is None or id_element.text is None:
        raise ValueError(
            "PrestaShop API nie zwróciło ID utworzonej wartości atrybutu."
        )

    return int(id_element.text)

def import_attribute_value(
    api: PrestaShopAPI,
    source_attribute_id: int,
    source_group_id: int,
    name: str,
    prestashop_group_id: int,
    mapping: dict
) -> int:
    """
    Importuje wartość atrybutu lub aktualizuje jej mapowanie.

    Zwraca ID wartości w PrestaShop.
    """

    # 1. Sprawdzenie lokalnego mapowania
    existing_mapping = get_attribute_mapping(
        mapping,
        source_attribute_id
    )

    if existing_mapping is not None:
        return existing_mapping["prestashop_id"]

    # 2. Wyszukanie wartości w PrestaShop
    prestashop_id = find_existing_attribute(
        api,
        name,
        prestashop_group_id
    )

    # 3. Utworzenie wartości, jeśli nie istnieje
    if prestashop_id is None:
        prestashop_id = create_attribute_value(
            api,
            name,
            prestashop_group_id
        )

    # 4. Zapisanie mapowania
    add_attribute_mapping(
        mapping,
        source_attribute_id,
        prestashop_id,
        source_group_id,
        name
    )

    save_mapping(mapping)

    return prestashop_id

