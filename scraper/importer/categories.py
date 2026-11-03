import json
import os
import re
import xml.etree.ElementTree as ET

from .api_client import PrestaShopAPI
from .categories_mapping import (
    load_mapping,
    save_mapping,
    get_prestashop_id,
    add_mapping
)

# Konfiguracja importera
SOURCE_PATH = "scraper/kategorie_poprawiony.json"
MAPPING_PATH = "scraper/importer/categories_mapping.json"

SHOP_URL = os.getenv(
    "SHOP_URL",
    f"http://localhost:{os.getenv('SHOP_PORT', '8080')}"
)
API_KEY = os.getenv("PS_API_KEY")

if not API_KEY:
    raise RuntimeError("Brak klucza API. Ustaw PS_API_KEY w pliku .env.")

LANGUAGE_ISO_CODE = "pl"
ROOT_CATEGORY_FLAG = "1"

def generate_link_rewrite(name: str) -> str:
    polish_chars = {
        "ą": "a", "ć": "c", "ę": "e",
        "ł": "l", "ń": "n", "ó": "o",
        "ś": "s", "ź": "z", "ż": "z",
        "Ą": "A", "Ć": "C", "Ę": "E",
        "Ł": "L", "Ń": "N", "Ó": "O",
        "Ś": "S", "Ź": "Z", "Ż": "Z"
    }

    for char, replacement in polish_chars.items():
        name = name.replace(char, replacement)

    name = name.lower()
    name = re.sub(r"[^a-z0-9]+", "-", name)
    name = name.strip("-")

    return name

def build_category_xml(name: str, parent_id: int, language_id: int) -> str:
    root = ET.Element("prestashop")
    category = ET.SubElement(root, "category")
    
    id_parent = ET.SubElement(category, "id_parent")
    id_parent.text = str(parent_id)
    
    active = ET.SubElement(category, "active")
    active.text = "1"
    
    name_element = ET.SubElement(category, "name")
    
    language = ET.SubElement(name_element, "language")
    language.set("id", str(language_id))
    language.text = name
    
    link_rewrite_element = ET.SubElement(category, "link_rewrite")

    language = ET.SubElement(link_rewrite_element, "language")
    language.set("id", str(language_id))
    language.text = generate_link_rewrite(name)
    
    return ET.tostring(root, encoding="unicode")

def get_parent_id(mapping: list, url: str, root_category_id: int) -> int:
    for category_group in mapping:
        main_category = category_group["main_category"]

        # Kategoria główna — jej rodzicem jest root PrestaShop
        if main_category["url"] == url:
            return root_category_id

        # Podkategoria — jej rodzicem jest kategoria główna
        for subcategory in category_group["subcategories"]:
            if subcategory["url"] == url:
                parent_id = main_category["prestashop_id"]

                if parent_id is None:
                    raise ValueError(
                        f"Kategoria nadrzędna nie ma przypisanego ID: "
                        f"{main_category['name']}"
                    )

                return parent_id

    raise ValueError(f"Nie znaleziono kategorii o URL: {url}")

def create_category(api: PrestaShopAPI, mapping: list, name: str, url: str, root_category_id: int, language_id: int) -> int:
    parent_id = get_parent_id(mapping, url, root_category_id)
    
    xml_data = build_category_xml(name, parent_id, language_id)
    
    response = api.post("categories", xml_data)
    
    response_xml = ET.fromstring(response)

    id_element = response_xml.find(".//category/id")

    if id_element is None or id_element.text is None:
        raise ValueError("PrestaShop API nie zwróciło ID utworzonej kategorii.")

    prestashop_id = int(id_element.text)
    
    if not add_mapping(mapping, url, prestashop_id, MAPPING_PATH):
        raise ValueError(f"Nie znaleziono kategorii w mapowaniu: {url}")

    return prestashop_id

def update_category(api: PrestaShopAPI, mapping: list, name: str, url: str, root_category_id: int, language_id: int) -> int:
    prestashop_id = get_prestashop_id(mapping, url)

    if prestashop_id is None:
        raise ValueError(f"Nie znaleziono ID kategorii w mapowaniu: {url}")

    parent_id = get_parent_id(mapping, url, root_category_id)

    xml_data = build_category_xml(name, parent_id, language_id)

    response_xml = ET.fromstring(xml_data)

    category_element = response_xml.find("./category")

    id_element = ET.Element("id")
    id_element.text = str(prestashop_id)

    category_element.insert(0, id_element)

    xml_data = ET.tostring(response_xml, encoding="unicode")

    api.put("categories", prestashop_id, xml_data)

    return prestashop_id