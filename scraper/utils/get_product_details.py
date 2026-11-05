import html
import json
import re
import time
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# # for testing purposes
# BASE_URL = "https://luksusowealkohole.pl"
# AJAX_URL = BASE_URL + "/index.php"
# REQUEST_DELAY = 0.5
# JSONS_DIR = Path(__file__).parent.parent / "jsons"
#
# session = requests.Session()
# session.headers.update({"User-Agent": "Mozilla/5.0"})
#
# # retry on timeouts and server errors, with growing pauses (2s, 4s, 8s). POST is safe here - refresh only reads data
# retry = Retry(total=3, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504],
#               allowed_methods=["GET", "POST"])
# session.mount("https://", HTTPAdapter(max_retries=retry))


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

# ai-assisted
def refresh_variant( product_id, product_url, selected ):
    """Invokes PrestaShop's AJAX for a specific product-variant combination"""
    payload = {
        'ajax': '1',
        'action': 'refresh',
        'quantity_wanted': '1'
    }
    for group_id, attribute_id in selected.items():
        payload[f"group[{group_id}]"] = attribute_id

    time.sleep(REQUEST_DELAY)
    response = session.post(
        AJAX_URL,
        params={"controller": "product", "id_product": product_id, "id_customization": 0},
        data=payload,
        headers={
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": product_url,
            "Origin": BASE_URL,
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    match = re.search(r'data-product="([^"]+)"', data.get("product_details", ""))
    if not match:
        raise ValueError("Brak data-product w odpowiedzi AJAX")

    return data, json.loads(html.unescape(match.group(1)))


def json_name( product ):
    """Returns file name based on product type: <id>_no_variants or <id>_variant_<variant_id>"""
    if not product.get('attributes'):
        return f"{product['id_product']}_no_variants"
    return f"{product['id_product']}_variant_{product['id_product_attribute']}"

