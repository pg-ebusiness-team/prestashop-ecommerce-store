import requests
import csv
from bs4 import BeautifulSoup

# request
url = "https://luksusowealkohole.pl"
response = requests.get(url)

# bs
soup = BeautifulSoup(response.text, 'html.parser')

header_top_box = soup.find("div", class_="header-top")

# all <li> category elements. Including sub-categories
categories = header_top_box.select("li", class_="category")

main_categories = []
for category in categories:
    main_category = category.find("a", attrs={"data-depth": 0})
    if main_category is not None:
        main_categories.append(main_category.get_text(strip=True))
# print(main_categories)

print(categories)
