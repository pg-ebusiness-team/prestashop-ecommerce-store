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