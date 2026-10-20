from utils.get_categories_dict import get_categories_dict
from utils.get_main_categories import get_main_categories


categories = get_categories_dict(get_main_categories())
print(categories)