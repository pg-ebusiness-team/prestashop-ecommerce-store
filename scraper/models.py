from typing import TypedDict

from pydantic import BaseModel, Field


class Category(TypedDict):
    name: str
    url: str


class CategoryWithSubcategories(TypedDict):
    main_category: Category
    subcategories: list[Category]

class Product(BaseModel):
    """Schema of a scraped product - only the fields the importer reads, the rest is ignored"""
    id_product: int = Field(gt=0)
    id_product_attribute: int
    name: str = Field(min_length=1)
    description: str
    description_short: str
    price_without_reduction: float = Field(ge=0)
    price_tax_exc: float = Field(ge=0)
    rate: float = Field(ge=0)
    quantity: int
    category: str = Field(min_length=1)
    features: list
    images: list
    # missing for products without variants
    attributes: dict | None = None
