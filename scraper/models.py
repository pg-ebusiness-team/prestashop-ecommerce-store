from typing import TypedDict


class Category(TypedDict):
    name: str
    url: str


class CategoryWithSubcategories(TypedDict):
    main_category: Category
    subcategories: list[Category]