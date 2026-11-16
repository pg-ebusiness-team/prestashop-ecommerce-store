
import argparse
import json
import os
from pathlib import Path

from .api_client import PrestaShopAPI
from .attributes import (
    import_attribute_group,
    import_attribute_value,
)
from .attributes_mapping import load_mapping

SOURCE_PATH = Path("scraper_results/products")

SHOP_URL = os.getenv(
    "SHOP_URL",
    f"https://localhost:{os.getenv('HTTPS_PORT', '8443')}"
)
API_KEY = os.getenv("PS_API_KEY")


def collect_source_attributes():
    """Zbiera unikalne grupy i wartości atrybutów ze źródłowych JSON-ów."""

    groups = {}
    attributes = {}

    json_files = list(SOURCE_PATH.rglob("*.json"))

    for file_path in json_files:
        with file_path.open("r", encoding="utf-8") as file:
            product = json.load(file)

        for attribute in (product.get("attributes") or {}).values():
            group_id = int(attribute["id_attribute_group"])
            attribute_id = int(attribute["id_attribute"])

            group_name = attribute["group"]
            attribute_name = attribute["name"]

            if group_id in groups and groups[group_id] != group_name:
                raise ValueError(
                    f"Konflikt nazwy grupy {group_id}: "
                    f"{groups[group_id]} / {group_name}"
                )

            groups[group_id] = group_name

            if attribute_id in attributes:
                existing = attributes[attribute_id]

                if (
                    existing["group_id"] != group_id
                    or existing["name"] != attribute_name
                ):
                    raise ValueError(
                        f"Konflikt wartości atrybutu {attribute_id}"
                    )

            attributes[attribute_id] = {
                "group_id": group_id,
                "name": attribute_name,
            }

    return groups, attributes, len(json_files)


def import_attributes(dry_run=True):
    groups, attributes, files_count = collect_source_attributes()

    print(f"Wczytane pliki JSON: {files_count}")
    print(f"Unikalne grupy atrybutów: {len(groups)}")
    print(f"Unikalne wartości atrybutów: {len(attributes)}")

    for group_id, group_name in sorted(groups.items()):
        print(f"  Grupa {group_id}: {group_name}")

    if dry_run:
        print("\nTryb kontrolny. Nie wykonano żadnych zmian w PrestaShop.")
        return

    if not API_KEY:
        raise RuntimeError(
            "Brak klucza API. Ustaw zmienną środowiskową PS_API_KEY."
        )

    api = PrestaShopAPI(SHOP_URL, API_KEY)
    mapping = load_mapping()

    imported_groups = 0
    imported_attributes = 0

    for group_id, group_name in sorted(groups.items()):
        prestashop_group_id = import_attribute_group(
            api,
            group_id,
            group_name,
            mapping,
        )
        imported_groups += 1

        print(
            f"Grupa: {group_name} "
            f"(źródło: {group_id}, PrestaShop: {prestashop_group_id})"
        )

    for attribute_id, attribute in sorted(attributes.items()):
        group_id = attribute["group_id"]
        attribute_name = attribute["name"]

        prestashop_group_id = mapping["groups"][str(group_id)]["prestashop_id"]

        prestashop_attribute_id = import_attribute_value(
            api,
            attribute_id,
            group_id,
            attribute_name,
            prestashop_group_id,
            mapping,
        )

        imported_attributes += 1

        print(
            f"Wartość: {attribute_name} "
            f"(źródło: {attribute_id}, PrestaShop: {prestashop_attribute_id})"
        )

    print("\nImport atrybutów zakończony.")
    print(f"Obsłużone grupy: {imported_groups}")
    print(f"Obsłużone wartości: {imported_attributes}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Wykonuje rzeczywisty import do PrestaShop.",
    )
    args = parser.parse_args()

    import_attributes(dry_run=not args.execute)
