import os
import re
import xml.etree.ElementTree as ET

from .api_client import PrestaShopAPI
from .categories_mapping import (
    add_mapping,
    get_prestashop_id,
    load_mapping,
)

# Konfiguracja importera
SOURCE_PATH = "scraper/kategorie_poprawiony.json"
MAPPING_PATH = "scraper/importer/categories_mapping.json"

SHOP_URL = os.getenv(
    "SHOP_URL",
    f"https://localhost:{os.getenv('HTTPS_PORT', '8443')}"
)
API_KEY = os.getenv("PS_API_KEY")

if not API_KEY:
    raise RuntimeError("Brak klucza API. Ustaw PS_API_KEY w pliku .env.")

LANGUAGE_ID = 1
ROOT_CATEGORY_ID = 2

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

def find_existing_category(api: PrestaShopAPI, name: str, parent_id: int) -> int | None:
    link_rewrite = generate_link_rewrite(name)

    response = api.get(
        "categories",
        params={
            "filter[id_parent]": f"[{parent_id}]",
            "filter[link_rewrite]": f"[{link_rewrite}]",
            "display": "[id,id_parent,link_rewrite]"
        }
    )

    response_xml = ET.fromstring(response)
    categories = response_xml.findall(".//category")

    if len(categories) > 1:
        raise ValueError(
            f"Znaleziono wiele kategorii o link_rewrite '{link_rewrite}' "
            f"i id_parent '{parent_id}'."
        )

    if len(categories) == 0:
        return None

    id_element = categories[0].find("id")

    if id_element is None or id_element.text is None:
        raise ValueError("API nie zwróciło ID znalezionej kategorii.")

    return int(id_element.text)

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

def import_categories():

    api = PrestaShopAPI(SHOP_URL, API_KEY)

    mapping = load_mapping(SOURCE_PATH, MAPPING_PATH)
    
    report = {
        "created": 0,
        "updated": 0,
        "rejected": 0
    }

    language_id = LANGUAGE_ID
    root_category_id = ROOT_CATEGORY_ID
    
    for category_group in mapping:
        main_category = category_group["main_category"]

        name = main_category["name"]
        url = main_category["url"]

        prestashop_id = get_prestashop_id(mapping, url)

        try:
            if prestashop_id is None:
                prestashop_id = find_existing_category(
                    api,
                    name,
                    root_category_id
                )

                if prestashop_id is not None:
                    add_mapping(mapping, url, prestashop_id, MAPPING_PATH)

            if prestashop_id is None:
                create_category(
                    api,
                    mapping,
                    name,
                    url,
                    root_category_id,
                    language_id
                )
                report["created"] += 1

            else:
                update_category(
                    api,
                    mapping,
                    name,
                    url,
                    root_category_id,
                    language_id
                )
                report["updated"] += 1

        except (RuntimeError, ValueError, ET.ParseError, OSError) as e:
            print(f"Błąd importu kategorii '{name}': {e}")
            report["rejected"] += 1
            
        if get_prestashop_id(mapping, main_category["url"]) is None:
            skipped = len(category_group["subcategories"])
            report["rejected"] += skipped

            print(
                f"Pominięto {skipped} podkategorii kategorii "
                f"'{main_category['name']}' – brak ID kategorii nadrzędnej."
            )
            continue
            
        for subcategory in category_group["subcategories"]:
            name = subcategory["name"]
            url = subcategory["url"]

            prestashop_id = get_prestashop_id(mapping, url)

            try:
                
                parent_id = get_parent_id(mapping, url, root_category_id)
                
                if prestashop_id is None:
                    prestashop_id = find_existing_category(
                        api,
                        name,
                        parent_id
                    )

                    if prestashop_id is not None:
                        add_mapping(mapping, url, prestashop_id, MAPPING_PATH)

                if prestashop_id is None:
                    create_category(
                        api,
                        mapping,
                        name,
                        url,
                        root_category_id,
                        language_id
                    )
                    report["created"] += 1

                else:
                    update_category(
                        api,
                        mapping,
                        name,
                        url,
                        root_category_id,
                        language_id
                    )
                    report["updated"] += 1

            except (RuntimeError, ValueError, ET.ParseError, OSError) as e:
                print(f"Błąd importu podkategorii '{name}': {e}")
                report["rejected"] += 1
    return report

def print_import_report(report: dict) -> None:

    created = report["created"]
    updated = report["updated"]
    rejected = report["rejected"]

    total = created + updated + rejected

    print("\n========== RAPORT IMPORTU ==========\n")

    print(f"Utworzone kategorie:       {created}")
    print(f"Zaktualizowane kategorie:  {updated}")
    print(f"Odrzucone kategorie:       {rejected}")

    print("------------------------------------")
    print(f"Łącznie przetworzono:      {total}")
    print("====================================")
    
if __name__ == "__main__":
    report = import_categories()
    print_import_report(report)