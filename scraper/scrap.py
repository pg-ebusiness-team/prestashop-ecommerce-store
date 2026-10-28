import shutil

import requests
from bs4 import BeautifulSoup
from utils.get_categories_dict import get_categories_dict
from utils.get_main_categories import get_main_categories
from utils.get_products import get_products
from utils.get_product_details import get_product_details, save_json, json_name
import os
from pathlib import Path

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

        products_data = get_products(sub_category['url'])
        pages = products_data['pages']
        for page in pages:
            page_path = f"{sub_category_folder}/{page['page']}"
            os.makedirs(Path(page_path), exist_ok=True)
            products_urls = page['products']
            for product_url in products_urls:
                # this function returns an array, even if product has no sub-categories
                try:
                    product_details = get_product_details(product_url)
                except Exception as e:
                    print(f"Error for {product_url}: {e}")
                    continue
                for p in product_details:
                    p_name = json_name(p)
                    save_json(page_path, p_name, p)
