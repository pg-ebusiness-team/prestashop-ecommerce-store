"""Unit tests of parser.py on pages saved from the source shop (fixtures/) - no network"""
from pathlib import Path

import pytest
from parser import (
    parse_main_categories,
    parse_page_count,
    parse_product_ajax,
    parse_product_id,
    parse_product_urls,
    parse_subcategories,
    parse_variant_select,
)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def read_fixture(name):
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


@pytest.fixture
def main_page_html():
    return read_fixture("main_page.html")


@pytest.fixture
def category_html():
    """'Prezenty' - category with subcategories"""
    return read_fixture("category_with_subcategories.html")


@pytest.fixture
def listing_html():
    """'Kosze upominkowe' - first page of a listing with 2 pages, no subcategories"""
    return read_fixture("category_listing.html")


@pytest.fixture
def product_ajax():
    """AJAX refresh response for 'WÓDKA Crystal Head', variant 0,7 l"""
    return parse_product_ajax(read_fixture("product_ajax_response.json"))


# categories

def test_parse_main_categories(main_page_html):
    categories = parse_main_categories(main_page_html)

    assert [c["name"] for c in categories] == [
        "Prezenty", "Whisky & Bourbon", "Alkohole & likiery", "Wino & Champagne", "Opakowania & Słodycze",
    ]
    assert categories[0]["url"] == "https://luksusowealkohole.pl/11-prezenty"


def test_parse_subcategories(category_html):
    subcategories = parse_subcategories(category_html)

    assert len(subcategories) == 10
    assert subcategories[0] == {"name": "Kosze upominkowe", "url": "https://luksusowealkohole.pl/38-kosze-upominkowe"}
    assert subcategories[-1]["name"] == "Alkohole na Wielkanoc"


def test_parse_subcategories_without_subcategories(listing_html):
    assert parse_subcategories(listing_html) == []


# listings

def test_parse_page_count(listing_html):
    assert parse_page_count(listing_html) == 2


def test_parse_page_count_without_pagination(main_page_html):
    assert parse_page_count(main_page_html) == 1


def test_parse_product_urls(listing_html):
    urls = parse_product_urls(listing_html)

    assert len(urls) == 36
    assert urls[0] == ("https://luksusowealkohole.pl/prezenty/"
                       "2666-ekskluzywne-pudelko-prezentowe-ze-wstazka-zestaw-bezalkoholowy")
    assert all(url.startswith("https://luksusowealkohole.pl/") for url in urls)


def test_parse_product_urls_without_product_list():
    assert parse_product_urls("<html><body><p>Brak produktów</p></body></html>") is None


# product page

def test_parse_variant_select():
    group_id, values = parse_variant_select(read_fixture("product_with_variants.html"))

    assert group_id == "5"
    assert values == ["28", "32", "36"]


def test_parse_variant_select_without_variants():
    assert parse_variant_select(read_fixture("product_no_variants.html")) == (None, [])


def test_parse_product_id():
    assert parse_product_id("https://luksusowealkohole.pl/wodka/1026-wodka-crystal-head") == "1026"


def test_parse_product_id_invalid_url():
    with pytest.raises(ValueError):
        parse_product_id("https://luksusowealkohole.pl/kontakt")


# product data (AJAX)

def test_parse_product_name(product_ajax):
    assert product_ajax["name"] == "WÓDKA Crystal Head"


def test_parse_product_ids(product_ajax):
    assert product_ajax["id_product"] == 1026
    assert product_ajax["id_product_attribute"] == 1138
    assert product_ajax["attributes"]["5"]["name"] == "0,7 l"


def test_parse_product_price(product_ajax):
    # the shop separates the currency with a non-breaking space
    assert product_ajax["price"] == "330,00\xa0zł"
    assert product_ajax["price_amount"] == 330


def test_parse_product_description(product_ajax):
    assert "Butelka w kształcie czaszki" in product_ajax["description"]


def test_parse_product_images(product_ajax):
    images = product_ajax["images"]

    assert [i["id_image"] for i in images] == [1235, 3221]
    assert all(i["associatedVariants"] == [1138] for i in images)
    assert images[0]["bySize"]["large_default"]["url"] == (
        "https://luksusowealkohole.pl/1235-large_default/wodka-crystal-head.jpg")
    assert product_ajax["cover"]["id_image"] == 3221


def test_parse_product_ajax_without_product_data():
    with pytest.raises(ValueError):
        parse_product_ajax('{"product_details": "<div></div>"}')
