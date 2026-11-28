"""Synchronizacja najniższej ceny z 30 dni z modułem Omnibus PrestaShop."""

from __future__ import annotations

from typing import Any


def _valid_price(product: dict[str, Any]) -> float | None:
    # amount jest polem liczbowym preferowanym przez importer. Fallback do
    # lowest_price_30d obsługuje rekordy, w których cena została zapisana
    # tylko pod polem tekstowym.
    value = product.get("lowest_price_30d_amount")
    if value in (None, ""):
        value = product.get("lowest_price_30d")
    if value is None:
        return None
    try:
        price = float(value)
    except (TypeError, ValueError):
        return None
    return price if price > 0 else None


def sync_omnibus_prices(
    api: Any,
    product: dict[str, Any],
    mapping: dict[str, Any],
) -> dict[str, int]:
    """Wysyła ceny produktu i wariantów do modułu Omnibus."""

    counts = {"sent": 0, "skipped": 0}
    source_id = product.get("source_id")
    product_mapping = mapping.get(str(source_id))

    if not source_id or not product_mapping:
        return {"sent": 0, "skipped": 1}

    prestashop_product_id = product_mapping.get("prestashop_id")
    if not prestashop_product_id:
        return {"sent": 0, "skipped": 1}

    prices: list[dict[str, Any]] = []

    price = _valid_price(product)
    if price is not None:
        prices.append({
            "id_product": int(prestashop_product_id),
            "id_product_attribute": 0,
            "source_id": str(source_id),
            "source_attribute_id": None,
            "lowest_price_30d": price,
        })
    else:
        counts["skipped"] += 1

    combination_mapping = product_mapping.get("combinations") or {}
    for combination in product.get("combinations") or []:
        source_attribute_id = combination.get("source_attribute_id")
        prestashop_attribute_id = combination_mapping.get(
            str(source_attribute_id)
        )

        if source_attribute_id in (None, 0, "0") or not prestashop_attribute_id:
            counts["skipped"] += 1
            continue

        price = _valid_price(combination)
        if price is None:
            counts["skipped"] += 1
            continue

        prices.append({
            "id_product": int(prestashop_product_id),
            "id_product_attribute": int(prestashop_attribute_id),
            "source_id": str(source_id),
            "source_attribute_id": str(source_attribute_id),
            "lowest_price_30d": price,
        })

    if not prices:
        return counts

    shop_url = api.base_url.rsplit("/api/", 1)[0].rstrip("/")
    endpoint = f"{shop_url}/module/omnibusprice/sync"

    response = api.session.post(
        endpoint,
        json={"prices": prices},
        headers={"Accept": "application/json"},
        timeout=20,
    )
    response.raise_for_status()

    counts["sent"] = len(prices)
    return counts
