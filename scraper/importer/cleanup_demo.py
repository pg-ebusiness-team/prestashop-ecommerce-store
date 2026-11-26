import argparse
import os
import xml.etree.ElementTree as ET

from scraper.importer.api_client import PrestaShopAPI
from scraper.importer.main import load_env_file

DEMO_CATEGORIES = {
    "clothes",
    "art",
    "men",
    "women",
    "stationery",
    "home accessories",
}


def get_text(element, path):
    return (element.findtext(path) or "").strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Wykonaj usuwanie."
    )
    args = parser.parse_args()

    load_env_file()

    shop_url = os.getenv(
        "SHOP_URL",
        f"https://localhost:{os.getenv('HTTPS_PORT', '8443')}"
    )
    api_key = os.getenv("PS_API_KEY")

    if not api_key:
        raise RuntimeError("Brak PS_API_KEY w .env.")

    api = PrestaShopAPI(shop_url, api_key)

    # Pobranie kategorii.
    root = ET.fromstring(api.get(
        "categories",
        {"display": "full", "limit": "0,1000"}
    ))

    categories = {}

    for category in root.findall("./categories/category"):
        category_id = int(get_text(category, "id"))
        parent_id = int(get_text(category, "id_parent"))

        names = {
            (language.text or "").strip().lower()
            for language in category.findall("./name/language")
        }

        categories[category_id] = {
            "parent": parent_id,
            "names": names,
            "is_root": get_text(category, "is_root_category") == "1",
        }
    root_category_ids = {
        category_id
        for category_id, category in categories.items()
        if category["is_root"]
    }   

    demo_ids = {
        category_id
        for category_id, category in categories.items()
        if category["names"] & DEMO_CATEGORIES
    }

    if not demo_ids:
        print("Nie znaleziono kategorii demonstracyjnych. Sklep jest czysty.")
        return

    demo_ids -= root_category_ids
    
    # Dodanie rodziców kategorii demo, z wyłączeniem kategorii głównych.
    changed = True

    while changed:
        changed = False

        for category_id in list(demo_ids):
            parent_id = categories[category_id]["parent"]

            if (
                parent_id in categories
                and parent_id not in root_category_ids
                and parent_id not in demo_ids
            ):
                demo_ids.add(parent_id)
                changed = True

    # Pobranie produktów.
    root = ET.fromstring(api.get(
        "products",
        {"display": "full", "limit": "0,1000"}
    ))

    products_to_delete = []
    product_details = []

    for product in root.findall("./products/product"):
        product_id = int(get_text(product, "id"))

        category_ids = {
            int(value.text)
            for value in product.findall(
                "./associations/categories/category/id"
            )
            if value.text
        }

        default_category = get_text(product, "id_category_default")

        if default_category:
            category_ids.add(int(default_category))

        if category_ids & demo_ids:
            products_to_delete.append(product_id)
            product_details.append({
                "id": product_id,
                "name": " / ".join(
                    (language.text or "").strip()
                    for language in product.findall("./name/language")
                    if language.text
                ),
                "categories": sorted(category_ids),
            })

    print("\nHierarchia wykrytych kategorii:")
    for category_id, category in sorted(categories.items()):
        if category_id in demo_ids or category["parent"] in demo_ids:
            print(
                f"  ID {category_id}: parent={category['parent']}, "
                f"demo={'TAK' if category_id in demo_ids else 'NIE'}"
            )

    print("\nKategorie demonstracyjne:")
    for category_id in sorted(demo_ids):
        names = categories[category_id]["names"]
        print(f"  ID {category_id}: {', '.join(sorted(names))}")

    print(f"\nProdukty do usunięcia: {len(products_to_delete)}")

    for product in product_details:
        print(
            f"  ID {product['id']}: {product['name']} "
            f"(kategorie: {product['categories']})"
        )

    print(f"Kategorie do usunięcia: {len(demo_ids)}")

    if not args.execute:
        print("\nDRY-RUN: niczego nie usunięto.")
        return

    # Najpierw produkty.
    for product_id in products_to_delete:
        api.delete("products", product_id)
        print(f"Usunięto produkt {product_id}")

    # Następnie kategorie, od najgłębiej zagnieżdżonych.
    def depth(category_id):
        result = 0
        parent = categories[category_id]["parent"]

        while parent in categories:
            result += 1
            parent = categories[parent]["parent"]

        return result

    for category_id in sorted(demo_ids, key=depth, reverse=True):
        api.delete("categories", category_id)
        print(f"Usunięto kategorię {category_id}")

    print("\nCzyszczenie zakończone.")


if __name__ == "__main__":
    main()
