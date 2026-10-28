import requests
from bs4 import BeautifulSoup
from utils.get_page_count import get_page_count
import time

def get_products(base_url):

    response = requests.get(base_url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    page_count = get_page_count(soup)

    data = {
        'base_url': base_url,
        'pages': [],
    }

    print(f"Getting products for {base_url}. Page count: {str(page_count)}")

    for page in range(1, page_count + 1):

        print("Getting products for page " + str(page))

        url = "{}?page={}".format(base_url, page)
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
