import json
from pathlib import Path

MAPPING_PATH = Path("scraper/importer/attributes_mapping.json")


def load_mapping() -> dict:
    """
    Wczytuje mapowanie atrybutów z pliku JSON.

    Jeśli plik nie istnieje, zwraca pusty słownik.
    """

    if not MAPPING_PATH.exists():
        return {
            "groups": {},
            "attributes": {}
        }

    with MAPPING_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_mapping(mapping: dict) -> None:
    """
    Zapisuje mapowanie atrybutów do pliku JSON.
    """

    with MAPPING_PATH.open("w", encoding="utf-8") as file:
        json.dump(mapping, file, indent=4, ensure_ascii=False)
        
def get_group_mapping(mapping: dict, source_group_id: int) -> dict | None:
    """
    Zwraca mapowanie grupy atrybutów na podstawie ID źródłowego.
    """

    return mapping["groups"].get(str(source_group_id))

def add_group_mapping(
    mapping: dict,
    source_group_id: int,
    prestashop_group_id: int,
    name: str
) -> None:
    """
    Dodaje mapowanie grupy atrybutów.
    """

    mapping["groups"][str(source_group_id)] = {
        "prestashop_id": prestashop_group_id,
        "name": name
    }
    
def get_attribute_mapping(mapping: dict, source_attribute_id: int) -> dict | None:
    """
    Zwraca mapowanie wartości atrybutu na podstawie ID źródłowego.
    """

    return mapping["attributes"].get(str(source_attribute_id))

def add_attribute_mapping(
    mapping: dict,
    source_attribute_id: int,
    prestashop_attribute_id: int,
    source_group_id: int,
    name: str
) -> None:
    """
    Dodaje mapowanie wartości atrybutu.
    """

    mapping["attributes"][str(source_attribute_id)] = {
        "prestashop_id": prestashop_attribute_id,
        "group_source_id": source_group_id,
        "name": name
    }