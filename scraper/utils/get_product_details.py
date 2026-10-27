import html
import json
import re
import time

import requests
from bs4 import BeautifulSoup

# for testing purposes
BASE_URL = "https://luksusowealkohole.pl"
AJAX_URL = BASE_URL + "/index.php"
REQUEST_DELAY = 0.5

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})


def get_variant_select( product_soup ):
    """Returns (Group_id, [attribute_id, ...] from variants select"""
    select = product_soup.select_one(".product-variants select[data-product-attribute]")
    if not select:
        return None, []

    group_id = select.get('data-product-attribute')

    values = [o.get('value') for o in select.find_all('option')]

    return group_id, values

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

# product with no variants
def build_base_product(product):
    base_product = {
        "p_id": product["id_product"],
        'p_ref': product['reference'],
        'name': product['meta_title'],
        'price_tax_incl': product['price_without_reduction'],
        "price_tax_excl": product['price_tax_exc'],
        'ref': product['reference'], # ?
    }
    return base_product

def build_product_combination( product, product_url, group_id, values ):
    combinations = []
    for value in values:
        data, p = refresh_variant( product, product_url, {group_id: value} )
        attr = list(p.get('attributes').values())[0]
        new_combination = {
            'variant_id': p.get('id_product_attribute'),
            'attributes': p.get('attributes'),
            'price_tax_incl': p.get('price_amount'),
            "price_tax_excl": p.get('price_tax_excl'),
            'quantity': p.get('quantity'),
            'name': attr['name'],
            'ref': attr['reference'],
        }
        combinations.append(new_combination)

    return combinations

def get_product_details(product_url):

    response = session.get(product_url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    group_id, values = get_variant_select(soup)

    id_input = soup.select_one('input[name="id_product"]')
    if id_input:
        p_id = id_input.get('value')
    #fallback
    else:
        p_id = re.search(r"/(\d+)-", product_url).group(1)

    data, product = refresh_variant(p_id, product_url, {})
    p = build_base_product(product)

    if not values:
        p["price_tax_incl"] = product.get("price_amount")
        p["price_tax_excl"] = product.get("price_tax_exc")
        p["quantity"] = product.get("quantity")

    combinations = build_product_combination(p_id, product_url, group_id, values)

    p['combinations'] = combinations

    print(f'{p["p_id"]} {p["name"]}')
    for c in p["combinations"]:
        print(
            f'  {c["variant_id"]:>5} | {c['name']} | {c["price_tax_incl"]} zł | ref {c["ref"]} | qty {c["quantity"]}')
    if not p["combinations"]:
        print(f'  bez wariantów | {p["price_tax_incl"]} zł | qty {p["quantity"]}')

    return p



get_product_details('https://luksusowealkohole.pl/bourbon/118-bourbon-jack-daniel-s')
# get_product_details('https://luksusowealkohole.pl/bourbon/118-158-bourbon-jack-daniel-s#/33-pojemnosc-175_l')
# get_product_details('https://luksusowealkohole.pl/whisky/2056-bezalkoholowe-whisky-lyre-s-american-malt')
# get_product_details('https://luksusowealkohole.pl/herbata/2596-herbata-riston-earl-grey-100g')
# get_product_details("https://luksusowealkohole.pl/akcesoria/2172-k-3-kuferek-bejcowany")

