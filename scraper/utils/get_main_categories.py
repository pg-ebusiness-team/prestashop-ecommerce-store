from models import Category


def get_main_categories(soup) -> list[Category]:

    header_top_box = soup.find("div", class_="header-top")

    categories = header_top_box.select('li.category:has(> a[data-depth="0"])')

    url_arr: list[Category] = []

    for c in categories:
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
