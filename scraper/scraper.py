import json
import os
from utils.get_soup import get_soup
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from utils.get_page_count import get_page_count
from utils.get_product_details import refresh_variant, get_variant_select
import time
import re
from pathlib import Path
import shutil
from utils.get_product_details import save_json, json_name
from utils.get_categories_dict import get_categories_dict
from utils.get_main_categories import get_main_categories

class Scraper:
    def __init__( self, site_url ):
        self.site_url = site_url
        self.soup = get_soup(self.site_url)
        self.cache_path = 'cache/cache.json'
        self.session = requests.Session()

    def run(self):
        self.session.headers.update({"User-Agent": "Mozilla/5.0"})
        # retry on timeouts and server errors, with growing pauses (2s, 4s, 8s). POST is safe here - refresh only reads data
        retry = Retry(total=3, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504],
                      allowed_methods=["GET", "POST"])
        self.session.mount("https://", HTTPAdapter(max_retries=retry))

    def get_cache( self ) -> dict:
        if os.path.exists( self.cache_path ):
            try:
                with open(self.cache_path, 'r') as f:
                    return json.load(f)
            except FileNotFoundError:
                print('[cache] File not found: {}'.format(self.cache_path))
                return {}
        else:
            return {}

    def get_products(self, category_url):
        """returns list of all products from a category"""

        response = self.session.get(category_url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        page_count = get_page_count(soup)

        data = {
            'base_url': category_url,
            'pages': [],
        }

        print(f"Getting products for {category_url}. Page count: {str(page_count)}")

        for page in range(1, page_count + 1):

            print("Getting products for page " + str(page))

            url = "{}?page={}".format(category_url, page)
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            product_list = soup.select_one('.product_list.grid.gridcount')
            # empty category or different layout (e.g. gift card) - no products on this page
            if product_list is None:
                print(f"No product list on {url}, skipping")
                break

            product_boxes = product_list.find_all('li', class_='product_item')
            products = []

            for box in product_boxes:
                p_url = box.select_one('.product-thumbnail').get('href').strip()
                products.append(p_url)

            data['pages'].append({
                'page': page,
                'products': products
            })

            time.sleep(.5)

        return data

    def get_product_details(self, product_url):
        """Returns list of data-product dicts - one per variant, or a single one for product without variants"""
        response = self.session.get(product_url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        id_input = soup.select_one('input[name="id_product"]')

        if id_input:
            p_id = id_input.get('value')
        else:
            p_id = re.search(r"/(\d+)-", product_url).group(1)

        group_id, values = get_variant_select(soup)

        if not values:
            _, product = refresh_variant(p_id, product_url, {})
            return [product]

        products_arr = []
        for value in values:
            _, product = refresh_variant(p_id, product_url, {group_id: value})
            products_arr.append(product)

        return products_arr

    def scrap(self):
        RESULTS_PATH = "../scraper_results/products"
        # delete old folder is exists (TODO: start at the scrapers last record)
        folder = Path(RESULTS_PATH)
        if folder.exists():
            shutil.rmtree(folder)
        folder.mkdir(parents=True)

        response = requests.get('https://luksusowealkohole.pl/')
        soup = BeautifulSoup(response.text, 'html.parser')

        categories = get_categories_dict(get_main_categories(soup))

        for category in categories:
            category_folder = f"{RESULTS_PATH}/{category['main_category']['name']}"
            os.makedirs(Path(category_folder), exist_ok=True)

            for sub_category in category['subcategories']:
                name = sub_category['name']
                sub_category_folder = f"{category_folder}/{name}"
                os.makedirs(Path(sub_category_folder), exist_ok=True)

                products_data = self.get_products(sub_category['url'])
                pages = products_data['pages']
                for page in pages:
                    page_path = f"{sub_category_folder}/{page['page']}"
                    os.makedirs(Path(page_path), exist_ok=True)
                    products_urls = page['products']
                    for product_url in products_urls:
                        # this function returns an array, even if product has no sub-categories
                        try:
                            product_details = self.get_product_details(product_url)
                        except Exception as e:
                            print(f"Error for {product_url}: {e}")
                            continue
                        for p in product_details:
                            p_name = json_name(p)
                            save_json(page_path, p_name, p)