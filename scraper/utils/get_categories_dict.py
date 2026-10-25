import time
import requests
from bs4 import BeautifulSoup
from models import Category, CategoryWithSubcategories


def get_categories_dict(url_arr: list[Category]) -> list[CategoryWithSubcategories]:

    result: list[CategoryWithSubcategories] = []

    for i, url_dict in enumerate(url_arr):
        name, url = url_dict['name'], url_dict['url']

        print("{}: Getting sub categories for {}".format(i, name))

        category_entry = {
            'category': { 'name': name, 'url': url },
            'subcategories': []
        }

        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        subcategories = soup.find(id='subcategories').find_all('a', class_='subcategory-name')

        for s in subcategories:
            name = s.text.strip()
            url = s['href']

            subcat_entry = { 'name': name, 'url': url }
            category_entry['subcategories'].append(subcat_entry)

        result.append(category_entry)
        time.sleep(.5)

    print("Finished getting sub categories")
    return result
