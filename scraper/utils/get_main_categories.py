import requests
from bs4 import BeautifulSoup
from models import Category

def get_main_categories() -> list[Category] | None:

    # request
    url = "https://luksusowealkohole.pl"
    try:
        response = requests.get(url, timeout=10)

        # bs
        soup = BeautifulSoup(response.text, 'html.parser')

        header_top_box = soup.find("div", class_="header-top")

        # all <li> category elements. Only the "big" blocks, excludes individual sub-categories to avoid repetition
        categories = header_top_box.select('li.category:has(> a[data-depth="0"])')

        url_arr: list[Category] = []

        for c in categories:
            # print(c.prettify())
            main_cat = c.find("a", attrs={"data-depth": 0})
            if main_cat is None:
                continue

            main_cat_url = main_cat["href"]
            main_cat_name = main_cat.get_text(strip=True)

            cat_object = {
                "name": main_cat_name,
                "url": main_cat_url,
            }
            url_arr.append(cat_object)

        return url_arr

    except requests.exceptions.Timeout:
        print("Error: Timeout")
        return None

    except requests.exceptions.RequestException as e:
        print("Error: {}".format(e))
        return None