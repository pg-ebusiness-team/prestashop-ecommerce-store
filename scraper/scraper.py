import json
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from utils.get_page_count import get_page_count
from utils.get_product_details import get_variant_select
import time
import re
from pathlib import Path
import shutil
from utils.get_product_details import save_json, json_name
from utils.get_main_categories import get_main_categories
from models import Category, CategoryWithSubcategories
import html

class Scraper:
    def __init__( self, site_url ):
        self.site_url = site_url
        self.RESULTS_PATH = "../scraper_results/products"
        self.session = requests.Session()
        self.cache = set()

    def run(self):
        self.session.headers.update({"User-Agent": "Mozilla/5.0"})
        # retry on timeouts and server errors, with growing pauses (2s, 4s, 8s). POST is safe here - refresh only reads data
        retry = Retry(total=3, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504],
                      allowed_methods=["GET", "POST"])
        self.session.mount("https://", HTTPAdapter(max_retries=retry))

        self.load_cache()


    def clear_result(self):
        # delete old folder is exists (TODO: start at the scrapers last record)
        folder = Path(self.RESULTS_PATH)
        if folder.exists():
            shutil.rmtree(folder)
        folder.mkdir(parents=True)

    def load_cache(self):
        for file in Path(self.RESULTS_PATH).rglob('*.json'):
            self.cache.add(file.name.split('_')[0])
        print(f"Loaded {len(self.cache)} products to cache")

    def get_categories_dict(self, url_arr: list[Category]) -> list[CategoryWithSubcategories]:

        result: list[CategoryWithSubcategories] = []

        for i, url_dict in enumerate(url_arr):
            name, url = url_dict['name'], url_dict['url']

            print("{}: Getting sub categories for {}".format(i, name))

            category_entry = {
                'main_category': {'name': name, 'url': url},
                'subcategories': []
            }

            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            subcategories_box = soup.find(id='subcategories')

            # category without subcategories - treat itself as the only subcategory, so its products are scraped
            if subcategories_box is None:
                category_entry['subcategories'].append({'name': name, 'url': url})
                result.append(category_entry)
                time.sleep(.5)
                continue

            subcategories = subcategories_box.find_all('a', class_='subcategory-name')

            for s in subcategories:
                name = s.text.strip()
                url = s['href']

                subcat_entry = {'name': name, 'url': url}
                category_entry['subcategories'].append(subcat_entry)

            result.append(category_entry)
            time.sleep(.5)

        print("Finished getting sub categories")
        return result

    def get_products(self, category_url):
        """returns list of all products from a category"""

        response = self.session.get(category_url, timeout=10)
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
            # page 1 is the same as category_url, already fetched above
            if page > 1:
                response = self.session.get(url, timeout=10)
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

    def refresh_variant(self, product_id, product_url, selected):
        """Invokes PrestaShop's AJAX for a specific product-variant combination"""

        ajax_url = self.site_url + '/index.php'
        payload = {
            'ajax': '1',
            'action': 'refresh',
            'quantity_wanted': '1'
        }
        for group_id, attribute_id in selected.items():
            payload[f"group[{group_id}]"] = attribute_id

        time.sleep(.5)
        response = self.session.post(
            ajax_url,
            params={"controller": "product", "id_product": product_id, "id_customization": 0},
            data=payload,
            headers={
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": product_url,
                "Origin": self.site_url,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        match = re.search(r'data-product="([^"]+)"', data.get("product_details", ""))
        if not match:
            raise ValueError("Brak data-product w odpowiedzi AJAX")

        return data, json.loads(html.unescape(match.group(1)))

    def get_product_details(self, product_url, p_id):
        """Returns list of data-product dicts - one per variant, or a single one for product without variants"""
        response = self.session.get(product_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        group_id, values = get_variant_select(soup)

        if not values:
            _, product = self.refresh_variant(p_id, product_url, {})
            return [product]

        products_arr = []
        for value in values:
            _, product = self.refresh_variant(p_id, product_url, {group_id: value})
            products_arr.append(product)

        return products_arr

    def scrap(self):

        response = self.session.get(self.site_url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        categories = self.get_categories_dict(get_main_categories(soup))

        for category in categories:
            category_folder = f"{self.RESULTS_PATH}/{category['main_category']['name']}"
            os.makedirs(Path(category_folder), exist_ok=True)

            for sub_category in category['subcategories']:
                name = sub_category['name']
                sub_category_folder = f"{category_folder}/{name}"
                os.makedirs(Path(sub_category_folder), exist_ok=True)

                # marker saved after the whole subcategory was scraped - skip it without any request
                done_marker = Path(sub_category_folder) / "_done"
                if done_marker.exists():
                    print(f"Subcategory {name} already done, skipping")
                    continue
                had_errors = False

                products_data = self.get_products(sub_category['url'])
                pages = products_data['pages']
                for page in pages:
                    page_path = f"{sub_category_folder}/{page['page']}"
                    os.makedirs(Path(page_path), exist_ok=True)
                    products_urls = page['products']
                    for product_url in products_urls:
                        # this function returns an array, even if product has no sub-variations
                        try:
                            p_id = re.search(r"/(\d+)-", product_url).group(1)
                            if p_id in self.cache:
                                print(f"Loaded {p_id} from cache")
                                continue
                            print(f"Fetching {p_id} {product_url}")
                            product_details = self.get_product_details(product_url, p_id)
                        except Exception as e:
                            print(f"Error for {product_url}: {e}")
                            had_errors = True
                            continue
                        for p in product_details:
                            p_name = json_name(p)
                            save_json(page_path, p_name, p)
                        self.cache.add(p_id)

                # don't mark if some product failed, so it's retried on the next run
                if not had_errors:
                    done_marker.touch()
