import requests
from bs4 import BeautifulSoup


def get_categories_dict():
    # request
    url = "https://luksusowealkohole.pl"
    response = requests.get(url)

    # bs
    soup = BeautifulSoup(response.text, 'html.parser')

    header_top_box = soup.find("div", class_="header-top")

    # all <li> category elements. Only the "big" blocks, excludes individual sub-categories to avoid repetition
    categories = header_top_box.select('li.category:has(> a[data-depth="0"])')

    categories_dict = {}

    for c in categories:
        main_cat = c.find("a", attrs={"data-depth": 0})
        if main_cat is None:
            continue

        main_cat_name = main_cat.get_text(strip=True)
        categories_dict[main_cat_name] = []
        sub_cats = c.find_all("a", attrs={"data-depth": 1})

        for sub_category in sub_cats:
            sub_cat_name = sub_category.get_text(strip=True)
            categories_dict[main_cat_name].append(sub_cat_name)

    return categories_dict