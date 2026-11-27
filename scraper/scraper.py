import json
import logging
import os
import shutil
import time
from pathlib import Path

import requests
from models import Category, CategoryWithSubcategories, Product
from parser import (
    parse_main_categories,
    parse_page_count,
    parse_product_ajax,
    parse_product_id,
    parse_product_urls,
    parse_subcategories,
    parse_variant_select,
)
from protego import Protego


def save_json(path, name, data):
    """Saves data to {path}/<name>.json"""
    with open(Path(path, f"{name}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def json_name(product):
    """Returns file name based on product type: <id>_no_variants or <id>_variant_<variant_id>"""
    if not product.get('attributes'):
        return f"{product['id_product']}_no_variants"
    return f"{product['id_product']}_variant_{product['id_product_attribute']}"


log = logging.getLogger("scraper")


class RobotsDisallowed(Exception):
    """Url blocked by the site's robots.txt"""


class Scraper:
    def __init__( self, site_url ):
        # without trailing slash, so paths can be appended with '/'
        self.site_url = site_url.rstrip('/')
        # paths relative to this file, not the current directory, so it works no matter where it's run from
        results_root = Path(__file__).resolve().parent.parent / "scraper_results"
        self.RESULTS_PATH = results_root / "products"
        # one large_default photo per image: <id_product>/<id_image>.webp (extension read from the content)
        # - the shop generates other sizes on import
        self.PHOTOS_PATH = results_root / "product_photos"
        # debug files (category tree, product listings) - kept outside RESULTS_PATH, so load_cache doesn't read them
        self.DEBUG_PATH = results_root / "debug"
        self.session = requests.Session()
        # identifies the scraper as a bot - also the name matched against robots.txt rules
        self.session.headers.update({"User-Agent": "EbizScraper/1.0"})
        # project limit: max 2 requests per second
        self.MIN_REQUEST_INTERVAL = 0.5
        self.last_request_time = 0.0
        # timeouts, connection errors and these statuses are retried with growing pauses (2s, 4s, 8s)
        self.MAX_RETRIES = 3
        self.RETRY_STATUSES = {429, 500, 502, 503, 504}
        # product id -> folder with its json files (to copy them when the product appears in another category)
        self.cache: dict[str, Path] = {}
        self.robots = self.load_robots()

    def load_robots(self):
        """Fetches the site's robots.txt - every request is checked against it"""
        url = self.site_url + "/robots.txt"
        # the only request outside request() (that one needs robots already) - logged the same way
        log.info("GET %s", url)
        # counts for the rate limit, so the next request waits for it too
        self.last_request_time = time.monotonic()
        response = self.session.get(url, timeout=10)
        # no robots.txt (4xx) means everything is allowed; server errors stop the scraper
        if 400 <= response.status_code < 500:
            return Protego.parse("")
        response.raise_for_status()
        return Protego.parse(response.text)

    def request(self, method, url, **kwargs):
        """All requests go through here - keeps max 2 requests per second (retries included)
        and retries failed ones. POST is safe to retry here - refresh only reads data"""
        # params are part of the url robots.txt rules match (e.g. /*controller=search)
        full_url = requests.Request(method, url, params=kwargs.get("params")).prepare().url
        if not self.robots.can_fetch(full_url, self.session.headers["User-Agent"]):
            raise RobotsDisallowed(f"Blocked by robots.txt: {full_url}")

        for attempt in range(self.MAX_RETRIES + 1):
            if attempt > 0:
                pause = 2 ** attempt
                log.warning(f"Retry {attempt}/{self.MAX_RETRIES} for {url} in {pause}s")
                time.sleep(pause)

            # wait only as long as needed since the previous request
            wait = self.last_request_time + self.MIN_REQUEST_INTERVAL - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self.last_request_time = time.monotonic()

            # every request is logged - the timestamps show the rate limit is kept
            log.info("%s %s", method, full_url)
            try:
                response = self.session.request(method, url, **kwargs)
            except (requests.ConnectionError, requests.Timeout):
                if attempt == self.MAX_RETRIES:
                    raise
                continue
            if response.status_code not in self.RETRY_STATUSES:
                return response

        # all attempts ended with a retryable status
        response.raise_for_status()

    def clear_result(self):
        # delete all scraped products (and so the cache, which is built from them) and their photos
        for folder in (self.RESULTS_PATH, self.PHOTOS_PATH):
            if folder.exists():
                shutil.rmtree(folder)
        self.RESULTS_PATH.mkdir(parents=True)

    def download_photos(self, product):
        """Downloads product's photos (large_default size) that aren't saved yet"""
        for image in product.get('images') or []:
            folder = self.PHOTOS_PATH / str(product['id_product'])
            name = str(image['id_image'])
            # extension depends on the content, so check any of them
            if any((folder / f"{name}.{ext}").exists() for ext in ("webp", "jpg", "png")):
                continue
            response = self.request("GET", image['bySize']['large_default']['url'], timeout=10)
            response.raise_for_status()
            # the shop serves WebP under .jpg urls and an image/jpeg header, so the format is read from the content
            content = response.content
            if content[:4] == b'RIFF' and content[8:12] == b'WEBP':
                extension = "webp"
            elif content[:8] == b'\x89PNG\r\n\x1a\n':
                extension = "png"
            else:
                extension = "jpg"
            path = folder / f"{name}.{extension}"
            folder.mkdir(parents=True, exist_ok=True)
            # write to a temp file first, so an interrupted download doesn't leave a broken photo that would be skipped
            temp_path = folder / f"{name}.part"
            temp_path.write_bytes(content)
            temp_path.replace(path)
            log.info(f"Saved photo {path.relative_to(self.PHOTOS_PATH)}")

    def download_missing_photos(self):
        """Downloads photos for products already saved (e.g. scraped before photos were supported, or a download failed)"""
        log.info("Checking photos of saved products")
        for file in self.RESULTS_PATH.rglob('*.json'):
            try:
                self.download_photos(json.loads(file.read_text(encoding="utf-8")))
            except Exception as e:  # noqa: BLE001 - one broken product mustn't stop the whole run
                log.error(f"Error downloading photos for {file.name}: {e}")

    def load_cache(self):
        for file in Path(self.RESULTS_PATH).rglob('*.json'):
            self.cache.setdefault(file.name.split('_')[0], file.parent)
        log.info(f"Loaded {len(self.cache)} products to cache")

    def copy_from_cache(self, p_id, page_path):
        """Copies already scraped product files to another category folder instead of fetching them again"""
        source = self.cache[p_id]
        target = Path(page_path)
        # product already saved in this folder (resumed run)
        if source.resolve() == target.resolve():
            log.info(f"{p_id} already saved here")
            return
        for file in source.glob(f"{p_id}_*.json"):
            shutil.copy(file, target / file.name)
        log.info(f"Copied {p_id} from {source}")

    def get_categories_dict(self, url_arr: list[Category]) -> list[CategoryWithSubcategories]:

        result: list[CategoryWithSubcategories] = []

        for i, url_dict in enumerate(url_arr):
            name, url = url_dict['name'], url_dict['url']

            log.info(f"{i}: Getting sub categories for {name}")

            response = self.request("GET", url, timeout=10)
            response.raise_for_status()
            subcategories = parse_subcategories(response.text)

            # category without subcategories - treat itself as the only subcategory, so its products are scraped
            if not subcategories:
                subcategories = [{'name': name, 'url': url}]

            result.append({'main_category': {'name': name, 'url': url}, 'subcategories': subcategories})

        log.info("Finished getting sub categories")
        return result

    def get_products(self, category_url):
        """returns list of all products from a category"""

        response = self.request("GET", category_url, timeout=10)
        response.raise_for_status()
        page_html = response.text

        page_count = parse_page_count(page_html)

        data = {
            'base_url': category_url,
            'pages': [],
        }

        log.info(f"Getting products for {category_url}. Page count: {page_count!s}")

        for page in range(1, page_count + 1):

            log.info("Getting products for page " + str(page))

            url = f"{category_url}?page={page}"
            # page 1 is the same as category_url, already fetched above
            if page > 1:
                response = self.request("GET", url, timeout=10)
                response.raise_for_status()
                page_html = response.text

            products = parse_product_urls(page_html)
            # empty category or different layout (e.g. gift card) - no products on this page
            if products is None:
                print(f"No product list on {url}, skipping")
                break

            data['pages'].append({
                'page': page,
                'products': products
            })

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

        response = self.request(
            "POST",
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
        return parse_product_ajax(response.text)

    def get_product_details(self, product_url, p_id):
        """Returns list of data-product dicts - one per variant, or a single one for product without variants"""
        response = self.request("GET", product_url, timeout=10)
        response.raise_for_status()

        group_id, values = parse_variant_select(response.text)

        if not values:
            return [self.refresh_variant(p_id, product_url, {})]

        products_arr = []
        for value in values:
            products_arr.append(self.refresh_variant(p_id, product_url, {group_id: value}))

        return products_arr

    def scrap(self, only_category=None, save_categories=False, save_listings=False, load_categories=False):

        def selected(name):
            return only_category is None or name.lower() == only_category.lower()

        if load_categories:
            categories_file = self.DEBUG_PATH / "categories.json"
            if not categories_file.exists():
                raise SystemExit(f"{categories_file} not found - run with --save-categories first")
            with open(categories_file, encoding="utf-8") as f:
                loaded = json.load(f)
            names = [c['main_category']['name'] for c in loaded]
        else:
            response = self.request("GET", self.site_url, timeout=10)
            response.raise_for_status()
            main_categories = parse_main_categories(response.text)
            names = [c['name'] for c in main_categories]

        if only_category is not None and not any(selected(n) for n in names):
            raise SystemExit(f"Category '{only_category}' not found. Available: {', '.join(names)}")

        if load_categories:
            categories = [c for c in loaded if selected(c['main_category']['name'])]
        else:
            # filter before fetching subcategories, so other categories cost no requests
            categories = self.get_categories_dict([c for c in main_categories if selected(c['name'])])
            # not when loading - it would overwrite the file with the same (or, with --category, filtered) data
            if save_categories:
                os.makedirs(self.DEBUG_PATH, exist_ok=True)
                save_json(self.DEBUG_PATH, "categories", categories)

        listings = []

        self.download_missing_photos()

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
                    log.info(f"Subcategory {name} already done, skipping")
                    continue
                had_errors = False

                products_data = self.get_products(sub_category['url'])
                if save_listings:
                    listings.append({'main_category': category['main_category']['name'], 'subcategory': name, **products_data})
                    # saved after every subcategory, so it's not lost when the run is interrupted
                    os.makedirs(self.DEBUG_PATH, exist_ok=True)
                    save_json(self.DEBUG_PATH, "listings", listings)

                pages = products_data['pages']
                for page in pages:
                    page_path = f"{sub_category_folder}/{page['page']}"
                    os.makedirs(Path(page_path), exist_ok=True)
                    products_urls = page['products']
                    for product_url in products_urls:
                        try:
                            p_id = parse_product_id(product_url)
                            if p_id in self.cache:
                                self.copy_from_cache(p_id, page_path)
                                continue
                            log.info(f"Fetching {p_id} {product_url}")
                            # returns an array, even if product has no sub-variations
                            product_details = self.get_product_details(product_url, p_id)
                            # validate all variants before saving any; ValidationError is logged by the except below
                            for p in product_details:
                                Product.model_validate(p)
                            for p in product_details:
                                p_name = json_name(p)
                                save_json(page_path, p_name, p)
                            self.cache[p_id] = Path(page_path)
                            # variants share photos - already downloaded ones are skipped
                            for p in product_details:
                                self.download_photos(p)
                        except RobotsDisallowed as e:
                            # blocked on every run - not an error, so the subcategory can still be marked _done
                            log.warning(f"Skipping {product_url}: {e}")
                            continue
                        except Exception as e:  # noqa: BLE001 - one broken product mustn't stop the whole run
                            log.error(f"Error for {product_url}: {e}")
                            had_errors = True
                            continue

                # don't mark if some product failed, so it's retried on the next run
                if not had_errors:
                    done_marker.touch()
