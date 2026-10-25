import requests
from bs4 import BeautifulSoup
from utils.get_categories_dict import get_categories_dict
from utils.get_main_categories import get_main_categories
from utils.get_page_count import get_page_count

response = requests.get('https://luksusowealkohole.pl/')
soup = BeautifulSoup(response.text, 'html.parser')

categories = get_categories_dict(get_main_categories(soup))
print(categories)