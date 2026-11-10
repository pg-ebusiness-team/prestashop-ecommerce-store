import html
import json
import re

from bs4 import BeautifulSoup
from models import Category


def _soup(page_html):
    return BeautifulSoup(page_html, 'html.parser')


def parse_main_categories(page_html) -> list[Category]:
    """Main categories from the top menu of any shop page"""
    header_top_box = _soup(page_html).find("div", class_="header-top")
    categories = header_top_box.select('li.category:has(> a[data-depth="0"])')

    result: list[Category] = []
    for c in categories:
        main_cat = c.find("a", attrs={"data-depth": 0})
        if main_cat is None:
            continue
        result.append({"name": main_cat.get_text(strip=True), "url": main_cat["href"]})

    return result


def parse_subcategories(page_html) -> list[Category]:
    """Subcategories from a category page, empty list if it has none"""
    subcategories_box = _soup(page_html).find(id='subcategories')
    if subcategories_box is None:
        return []

    return [
        {'name': a.text.strip(), 'url': a['href']}
        for a in subcategories_box.find_all('a', class_='subcategory-name')
    ]


def parse_page_count(page_html) -> int:
    """Number of pages of a category listing, 1 if there's no pagination"""
    pagination = _soup(page_html).find('ul', class_='page-list')
    if pagination is None:
        return 1

    pages = [
        int(a.get_text(strip=True))
        for a in pagination
        if a.get_text(strip=True).isdigit()
    ]
    return max(pages, default=1)


def parse_product_urls(page_html) -> list[str] | None:
    """Product urls from one listing page, None if there's no product list (empty category or different layout)"""
    product_list = _soup(page_html).select_one('.product_list.grid.gridcount')
    if product_list is None:
        return None

    return [
        box.select_one('.product-thumbnail').get('href').strip()
        for box in product_list.find_all('li', class_='product_item')
    ]


def parse_variant_select(page_html) -> tuple[str | None, list[str]]:
    """(group_id, [attribute_id, ...]) from the product page's variants select, (None, []) without variants"""
    select = _soup(page_html).select_one(".product-variants select[data-product-attribute]")
    if not select:
        return None, []

    return select.get('data-product-attribute'), [o.get('value') for o in select.find_all('option')]


def parse_product_ajax(response_text) -> dict:
    """Product data (data-product attribute) from PrestaShop's AJAX refresh response"""
    data = json.loads(response_text)
    match = re.search(r'data-product="([^"]+)"', data.get("product_details", ""))
    if not match:
        raise ValueError("No data-product in AJAX response")

    return json.loads(html.unescape(match.group(1)))


def parse_product_id(product_url) -> str:
    """Product id from its url, e.g. .../wodka/1026-wodka-crystal-head -> '1026'"""
    match = re.search(r"/(\d+)-", product_url)
    if not match:
        raise ValueError(f"No product id in url {product_url}")
    return match.group(1)
