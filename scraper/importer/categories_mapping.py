import json
from pathlib import Path


def load_mapping(source_path: str, mapping_path: str) -> list:
    mapping_file = Path(mapping_path)

    # Jeśli mapa już istnieje, wczytujemy ją
    if mapping_file.exists():
        with mapping_file.open("r", encoding="utf-8") as file:
            return json.load(file)

    # Jeśli nie istnieje, wczytujemy oryginalny plik kategorii
    try:
        with open(source_path, "r", encoding="utf-8") as file:
            categories = json.load(file)

    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Nie znaleziono pliku źródłowego: {source_path}"
        ) from e

    mapping = []

    for category_group in categories:
        main_category = {
            **category_group["main_category"],
            "prestashop_id": None
        }

        subcategories = []

        for subcategory in category_group["subcategories"]:
            new_subcategory = {
                **subcategory,
                "prestashop_id": None
            }

            subcategories.append(new_subcategory)

        mapping.append({
            "main_category": main_category,
            "subcategories": subcategories
        })

    save_mapping(mapping, mapping_path)

    return mapping

def save_mapping(mapping: list, mapping_path: str) -> None:
    with open(mapping_path, "w", encoding="utf-8") as file:
        json.dump(
            mapping,
            file,
            ensure_ascii=False,
            indent=4
        )
        
def get_prestashop_id(mapping: list, url: str) -> int | None:

    for category_group in mapping:
        main_category = category_group["main_category"]

        if main_category["url"] == url:
            return main_category["prestashop_id"]

        for subcategory in category_group["subcategories"]:
            if subcategory["url"] == url:
                return subcategory["prestashop_id"]

    return None

def _update_category_id(category: dict, prestashop_id: int) -> bool:
    current_id = category["prestashop_id"]

    if current_id is not None and current_id != prestashop_id:
        raise ValueError(
            f"Kategoria ma już przypisane ID {current_id}, "
            f"nie można przypisać ID {prestashop_id}."
        )

    category["prestashop_id"] = prestashop_id
    return current_id != prestashop_id
        
def add_mapping(mapping: list, url: str, prestashop_id: int, mapping_path: str) -> bool:

    for category_group in mapping:
        main_category = category_group["main_category"]

        if main_category["url"] == url:
            changed = _update_category_id(main_category, prestashop_id)

            if changed:
                save_mapping(mapping, mapping_path)

            return True

        for subcategory in category_group["subcategories"]:
            if subcategory["url"] == url:
                changed = _update_category_id(subcategory, prestashop_id)

                if changed:
                    save_mapping(mapping, mapping_path)

                return True

    return False