
import os
import xml.etree.ElementTree as ET
from pathlib import Path

from scraper.importer.products_mapping import save_mapping


def _photos_path() -> Path:
    configured = os.getenv("PS_PRODUCT_PHOTOS_DIR")
    if configured:
        return Path(configured)
    candidates = (Path("scraper_results/product_photos"), Path("scraper/product_photos"))
    return next((path for path in candidates if path.is_dir()), candidates[0])


PHOTOS_PATH = _photos_path()


def import_product_images(
    api,
    product_id: int,
    product: dict,
    products_mapping: dict
) -> tuple[int, int]:
    """
    Importuje lokalne zdjęcia produktu do PrestaShop.

    Pomija zdjęcia już zaimportowane.
    Zwraca liczbę utworzonych i pominiętych zdjęć.
    """

    source_id = str(product["source_id"])

    product_mapping = products_mapping.get(source_id)

    if product_mapping is None:
        raise KeyError(
            f"Brak mapowania produktu źródłowego {source_id}."
        )

    product_mapping.setdefault("images", {})
    image_mapping = product_mapping["images"]

    created = 0
    skipped = 0

    for image in (product.get("images") or []):
        source_image_id = image.get("id_image") or image.get("id")

        if source_image_id is None:
            skipped += 1
            continue

        image_key = str(source_image_id)

        if image_key in image_mapping:
            skipped += 1
            continue

        image_path = (
            PHOTOS_PATH
            / source_id
            / f"{source_image_id}.webp"
        )

        if not image_path.is_file():
            print(
                f"Brak lokalnego zdjęcia produktu {source_id}: "
                f"{image_path}"
            )
            skipped += 1
            continue

        image_data = image_path.read_bytes()

        response = api.post_image(
            product_id,
            image_data,
            image_path.name,
            "image/webp"
        )

        root = ET.fromstring(response)

        prestashop_image_id = root.findtext("./image/id")

        if prestashop_image_id is None:
            raise RuntimeError(
                f"PrestaShop nie zwrócił ID zdjęcia "
                f"produktu {product_id}."
            )

        image_mapping[image_key] = int(prestashop_image_id)

        save_mapping(products_mapping)

        created += 1

    return created, skipped
