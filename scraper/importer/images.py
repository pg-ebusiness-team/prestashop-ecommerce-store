import mimetypes
import xml.etree.ElementTree as ET

import requests

from scraper.importer.products_mapping import save_mapping


def get_image_url(image: dict) -> str | None:
    """
    Wybiera największą dostępną wersję zdjęcia.
    """

    sizes = image.get("bySize", {})

    preferred_sizes = [
        "large_default",
        "thickbox_default",
        "home_default",
        "medium_default",
        "small_default"
    ]

    for size in preferred_sizes:
        image_data = sizes.get(size)

        if image_data and image_data.get("url"):
            return image_data["url"]

    # Awaryjnie sprawdzamy pozostałe rozmiary
    for image_data in sizes.values():
        if isinstance(image_data, dict) and image_data.get("url"):
            return image_data["url"]

    return image.get("url")


def download_image(url: str) -> tuple[bytes, str, str]:
    """
    Pobiera zdjęcie i zwraca jego zawartość,
    nazwę pliku oraz typ MIME.
    """

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

    except requests.RequestException as error:
        raise RuntimeError(
            f"Nie udało się pobrać zdjęcia {url}: {error}"
        )

    content_type = response.headers.get(
        "Content-Type",
        "image/jpeg"
    ).split(";")[0]

    extension = mimetypes.guess_extension(content_type) or ".jpg"

    filename = f"image{extension}"

    return response.content, filename, content_type


def import_product_images(
    api,
    product_id: int,
    product: dict,
    products_mapping: dict
) -> tuple[int, int]:
    """
    Importuje zdjęcia produktu do PrestaShop.

    Pomija zdjęcia, które zostały już zaimportowane.

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

    for image in product.get("images", []):
        source_image_id = image.get("id_image") or image.get("id")

        image_url = get_image_url(image)

        if not image_url:
            skipped += 1
            continue

        # ID źródłowego zdjęcia jest podstawą mapowania.
        # Jeżeli go brakuje, używamy URL jako klucza.
        image_key = str(source_image_id or image_url)

        if image_key in image_mapping:
            skipped += 1
            continue

        image_data, filename, content_type = download_image(
            image_url
        )

        response = api.post_image(
            product_id,
            image_data,
            filename,
            content_type
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