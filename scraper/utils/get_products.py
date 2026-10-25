import requests
from bs4 import BeautifulSoup
from get_page_count import get_page_count
import time
from pathlib import Path

def get_products():

    base_url = 'https://luksusowealkohole.pl/15-whisky-bourbon'

    response = requests.get(base_url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    page_count = get_page_count(soup)

    data = {
        'base_url': base_url,
        'pages': [],
    }

    print('Getting products. Page count: ' + str(page_count))

    for page in range(1, page_count + 1):

        print("Getting products for page " + str(page))

        url = "{}?page={}".format(base_url, page)
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        product_boxes = soup.select_one('.product_list.grid.gridcount').find_all('li', class_='product_item')
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

print(get_products())