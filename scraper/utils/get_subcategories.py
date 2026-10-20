import requests
from bs4 import BeautifulSoup
from get_main_categories import get_main_categories

url_arr = get_main_categories()

def get_sub_categories(url_arr: list[dict[str, str]]):


    result = []
    # [
    #   { name: 'abc', url: '...', subcategories: [...] },
    #   ...
    # ]


    # for url_dict in url_arr:
    #     name, url = url_dict['name'], url_dict['url']
    #     print(name)
    #     print(url)

    # test scrapowania dla pierwszej pozycji
    name, url = url_arr[0]['name'], url_arr[0]['url']

    category_entry = {}
    category_entry['name'] = name
    category_entry['url'] = url
    category_entry['subcategories'] = []

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    subcategories = soup.find(id='subcategories').find_all('a', class_='subcategory-name')

    for s in subcategories:
        name = s.text.strip()
        url = s['href']

        subcat_entry = { 'name': name, 'url': url }
        category_entry['subcategories'].append(subcat_entry)

    print(category_entry)
    return category_entry

get_sub_categories(url_arr)
