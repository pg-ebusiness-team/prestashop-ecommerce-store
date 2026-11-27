import json
import os
import threading
from pathlib import Path

MAPPING_PATH = Path("scraper/importer/products_mapping.json")
_SAVE_LOCK = threading.Lock()


def load_mapping() -> dict:
    """
    Wczytuje mapowanie produktów z pliku JSON.

    Jeśli plik jeszcze nie istnieje, zwraca pusty słownik.
    """

    if not MAPPING_PATH.exists():
        return {}

    with MAPPING_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_mapping(mapping: dict) -> None:
    """
    Zapisuje mapowanie produktów do pliku JSON (bezpieczne dla wątków).
    """

    with _SAVE_LOCK:
        # shortcut: json.dumps bez indent idzie przez enkoder C bez oddawania GIL, więc to
        # spójna migawka mimo zmian z innych wątków; na Pythonie free-threaded trzeba lock na każdej mutacji
        snapshot = json.loads(json.dumps(mapping))
        tmp_path = MAPPING_PATH.with_suffix(".json.tmp")
        with tmp_path.open("w", encoding="utf-8") as file:
            json.dump(snapshot, file, indent=4, ensure_ascii=False)
        os.replace(tmp_path, MAPPING_PATH)

def get_product_mapping(mapping: dict, source_id: int) -> dict | None:
    """
    Zwraca mapowanie produktu na podstawie jego ID źródłowego.
    Jeśli produktu nie ma w mapowaniu, zwraca None.
    """

    return mapping.get(str(source_id))

def add_product_mapping(
    mapping: dict,
    source_id: int,
    prestashop_id: int
) -> None:
    """
    Dodaje nowy produkt do mapowania.
    """

    mapping[str(source_id)] = {
        "prestashop_id": prestashop_id,
        "combinations": {}
    }
    
def add_combination_mapping(
    mapping: dict,
    source_id: int,
    source_attribute_id: int,
    prestashop_attribute_id: int
) -> None:
    """
    Dodaje mapowanie wariantu produktu.
    """

    product = mapping.get(str(source_id))

    if product is None:
        raise KeyError(f"Produkt {source_id} nie istnieje w mapowaniu.")

    product["combinations"][str(source_attribute_id)] = prestashop_attribute_id