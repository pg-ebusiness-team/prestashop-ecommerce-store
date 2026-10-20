import requests
from bs4 import BeautifulSoup


def get_main_categories() -> list[dict[str, str]]:
    # request
    url = "https://luksusowealkohole.pl"
    response = requests.get(url)

    # bs
    soup = BeautifulSoup(response.text, 'html.parser')

    header_top_box = soup.find("div", class_="header-top")

    # all <li> category elements. Only the "big" blocks, excludes individual sub-categories to avoid repetition
    categories = header_top_box.select('li.category:has(> a[data-depth="0"])')

    url_arr: list[dict[str, str]] = []

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

