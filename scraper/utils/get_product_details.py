import json
from pathlib import Path


def get_variant_select( product_soup ):
    """Returns (Group_id, [attribute_id, ...] from variants select"""
    select = product_soup.select_one(".product-variants select[data-product-attribute]")
    if not select:
        return None, []

    group_id = select.get('data-product-attribute')

    values = [o.get('value') for o in select.find_all('option')]

    return group_id, values

def save_json( path, name, data ):
    """Saves decoded data-product to {path}/<name>.json"""
    with open(Path(path, f"{name}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def json_name( product ):
    """Returns file name based on product type: <id>_no_variants or <id>_variant_<variant_id>"""
    if not product.get('attributes'):
        return f"{product['id_product']}_no_variants"
    return f"{product['id_product']}_variant_{product['id_product_attribute']}"

