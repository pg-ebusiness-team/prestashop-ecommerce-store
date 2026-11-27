"""Idempotent synchronization of source promotions to PrestaShop specific_prices."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation
from typing import Any

RESOURCE = "specific_prices"
XMLNS = "http://www.w3.org/1999/xlink"

# Fields that define the target rule's scope and matching identity.
IDENTITY_FIELDS = (
    "id_product",
    "id_product_attribute",
    "id_shop",
    "id_shop_group",
    "id_currency",
    "id_country",
    "id_group",
    "id_customer",
    "id_cart",
    "from_quantity",
    "reduction_type",
)
DATE_FIELDS = ("from", "to")



def _decimal(value: Any, field: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Nieprawidłowa wartość promocji '{field}': {value!r}.") from exc
    if not number.is_finite():
        raise ValueError(f"Wartość promocji '{field}' musi być skończona.")
    return number


def _as_int(value: Any, default: int = 0) -> int:
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Nieprawidłowy identyfikator promocji: {value!r}.") from exc


def _normalize_date(value: Any) -> str:
    """PrestaShop uses its zero date to represent an unbounded date."""
    if value in (None, "", "0000-00-00", "0000-00-00 00:00:00"):
        return "0000-00-00 00:00:00"
    text = str(value).strip()
    if len(text) == 10:
        text += " 00:00:00"
    if len(text) != 19:
        raise ValueError(f"Nieprawidłowa data promocji: {value!r}.")
    return text


def _normalize_reduction(source: dict) -> tuple[str, str, str]:
    """Return reduction, reduction_type and reduction_tax for PrestaShop."""
    reduction_type = str(source.get("reduction_type") or "percentage").lower()
    if reduction_type not in {"percentage", "amount"}:
        raise ValueError(
            f"Nieobsługiwany typ rabatu: {reduction_type!r}; "
            "dozwolone: percentage, amount."
        )

    reduction = _decimal(source.get("reduction"), "reduction")
    if reduction < 0:
        raise ValueError("Rabat nie może być ujemny.")
    if reduction_type == "percentage" and reduction > 1:
        raise ValueError(
            "Rabat procentowy musi być ułamkiem od 0 do 1 "
            "(np. 0.15 oznacza 15%)."
        )

    reduction_tax = _as_int(source.get("reduction_tax"), 1)
    if reduction_tax not in (0, 1):
        raise ValueError("reduction_tax musi mieć wartość 0 albo 1.")

    # Decimal formatting avoids binary float artefacts in the XML payload.
    return format(reduction, "f"), reduction_type, str(reduction_tax)


def _resolve_target_attribute_id(
    source_attribute_id: Any,
    source_product_id: int,
    products_mapping: dict,
) -> int:
    """Translate source variant ID into the PrestaShop combination ID."""
    source_attribute_id = _as_int(source_attribute_id, 0)
    if source_attribute_id == 0:
        return 0

    product_mapping = products_mapping.get(str(source_product_id))
    if not product_mapping:
        raise KeyError(
            f"Brak mapowania produktu źródłowego {source_product_id} "
            "przy mapowaniu promocji wariantu."
        )

    target_id = (product_mapping.get("combinations") or {}).get(
        str(source_attribute_id)
    )
    if target_id is None:
        raise KeyError(
            f"Brak mapowania wariantu źródłowego {source_attribute_id} "
            f"produktu {source_product_id} na kombinację PrestaShop. "
            "Najpierw zaimportuj warianty."
        )
    return _as_int(target_id)


def normalize_promotion(
    source: dict,
    source_product_id: int,
    target_product_id: int,
    products_mapping: dict,
) -> dict:
    """Normalize one source specific-price record to the PrestaShop schema."""
    if not isinstance(source, dict):
        raise TypeError("Rekord promocji musi być słownikiem.")

    reduction, reduction_type, reduction_tax = _normalize_reduction(source)
    target_attribute_id = _resolve_target_attribute_id(
        source.get("id_product_attribute", 0),
        source_product_id,
        products_mapping,
    )

    result = {
        "id_product": str(target_product_id),
        "id_product_attribute": str(target_attribute_id),
        "id_shop": str(_as_int(source.get("id_shop"), 0)),
        "id_shop_group": str(_as_int(source.get("id_shop_group"), 0)),
        "id_currency": str(_as_int(source.get("id_currency"), 0)),
        "id_country": str(_as_int(source.get("id_country"), 0)),
        "id_group": str(_as_int(source.get("id_group"), 0)),
        "id_customer": str(_as_int(source.get("id_customer"), 0)),
        "id_cart": str(_as_int(source.get("id_cart"), 0)),
        "from_quantity": str(max(1, _as_int(source.get("from_quantity"), 1))),
        # -1 means "use the product's current base price" in PrestaShop.
        "price": "-1.000000",
        "reduction": reduction,
        "reduction_tax": reduction_tax,
        "reduction_type": reduction_type,
        "from": _normalize_date(source.get("from")),
        "to": _normalize_date(source.get("to")),
    }
    return result


def build_specific_price_xml(promotion: dict, specific_price_id: int | None = None) -> str:
    """Build a complete specific_price XML resource for POST or PUT."""
    root = ET.Element("prestashop", {"xmlns:xlink": XMLNS})
    element = ET.SubElement(root, "specific_price")
    if specific_price_id is not None:
        ET.SubElement(element, "id").text = str(specific_price_id)

    fields = (
        "id_shop_group",
        "id_shop",
        "id_cart",
        "id_product",
        "id_product_attribute",
        "id_currency",
        "id_country",
        "id_group",
        "id_customer",
        "price",
        "from_quantity",
        "reduction",
        "reduction_tax",
        "reduction_type",
        "from",
        "to",
    )
    for field in fields:
        ET.SubElement(element, field).text = str(promotion[field])
    return ET.tostring(root, encoding="unicode")


def _parse_specific_price_list(response: str) -> list[ET.Element]:
    root = ET.fromstring(response)
    return root.findall("./specific_prices/specific_price")


def _find_existing_specific_price(api, promotion: dict) -> int | None:
    """Find a rule to update, preferring exact dates and avoiding ambiguous matches."""
    response = api.get(
        RESOURCE,
        params={
            "filter[id_product]": f"[{promotion['id_product']}]",
            "display": "full",
            "limit": "0,1000",
        },
    )
    candidates: list[tuple[int, bool]] = []
    for element in _parse_specific_price_list(response):
        existing_id = element.findtext("id")
        if not existing_id:
            continue
        matches = True
        for field in IDENTITY_FIELDS:
            existing_value = element.findtext(field)
            expected_value = str(promotion[field])
            if existing_value is None:
                existing_value = "1" if field == "reduction_tax" else "0"
            if field == "from_quantity":
                try:
                    matches = _decimal(existing_value, field) == _decimal(expected_value, field)
                except ValueError:
                    matches = False
            else:
                matches = str(existing_value) == expected_value
            if not matches:
                break
        if not matches:
            continue

        exact_dates = all(
            _normalize_date(element.findtext(field)) == promotion[field]
            for field in DATE_FIELDS
        )
        candidates.append((int(existing_id), exact_dates))

    exact = [specific_price_id for specific_price_id, dates_match in candidates if dates_match]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        raise RuntimeError(
            "Znaleziono kilka identycznych reguł specific_price; "
            "przerywam, aby nie aktualizować przypadkowej promocji."
        )

    # If the source changed the date range, update only when there is one
    # unambiguous rule with the same product/variant and discount scope.
    if len(candidates) == 1:
        return candidates[0][0]
    if len(candidates) > 1:
        raise RuntimeError(
            "Znaleziono kilka reguł specific_price o tym samym zakresie "
            "bez zgodnych dat; nie można bezpiecznie wskazać reguły do aktualizacji."
        )
    return None



def sync_product_promotions(
    api,
    product: dict,
    products_mapping: dict,
    dry_run: bool = False,
) -> dict[str, int]:
    """Create/update all promotions for one grouped product.

    Expected product fields: source_id, promotions (list), and the local
    products_mapping entry with prestashop_id and combinations mapping.
    Does not delete rules absent from the source.
    """
    source_product_id = _as_int(product.get("source_id"))
    product_mapping = products_mapping.get(str(source_product_id))
    if not product_mapping:
        raise KeyError(f"Brak mapowania produktu {source_product_id}.")
    target_product_id = _as_int(product_mapping.get("prestashop_id"))
    if target_product_id <= 0:
        raise ValueError(f"Nieprawidłowe ID PrestaShop produktu {source_product_id}.")

    promotions = product.get("promotions") or []
    counts = {"created": 0, "updated": 0, "skipped": 0}

    for source_promotion in promotions:
        # Source IDs are not target PrestaShop IDs; explicitly discard them.
        source_promotion = dict(source_promotion)
        source_promotion.pop("id_specific_price", None)
        source_promotion.pop("score", None)

        # Some source products arrive as a simple product record while their
        # default combination ID is still attached to specific_prices. If the
        # importer has no combinations and this is exactly that default
        # combination, apply its promotion to the simple target product.
        source_attribute_id = _as_int(
            source_promotion.get("id_product_attribute"), 0
        )
        default_attribute_id = _as_int(
            product.get("source_default_attribute_id"), 0
        )
        if (
            source_attribute_id > 0
            and not (product.get("combinations") or [])
            and source_attribute_id == default_attribute_id
        ):
            source_promotion["id_product_attribute"] = 0

        normalized = normalize_promotion(
            source_promotion,
            source_product_id,
            target_product_id,
            products_mapping,
        )

        if dry_run:
            counts["updated"] += 1
            continue

        existing_id = _find_existing_specific_price(api, normalized)
        xml_data = build_specific_price_xml(normalized, existing_id)
        if existing_id is None:
            api.post(RESOURCE, xml_data)
            counts["created"] += 1
        else:
            api.put(RESOURCE, existing_id, xml_data)
            counts["updated"] += 1

    return counts


def sync_promotions(
    api,
    products: list[dict],
    products_mapping: dict,
    dry_run: bool = False,
) -> dict[str, int]:
    """Synchronize promotions for a list of grouped products."""
    total = {"created": 0, "updated": 0, "skipped": 0, "rejected": 0}
    for product in products:
        try:
            result = sync_product_promotions(
                api, product, products_mapping, dry_run=dry_run
            )
            for key, value in result.items():
                total[key] += value
        except Exception as exc:  # noqa: BLE001
            total["rejected"] += 1
            print(
                f"[PROMOCJE {product.get('source_id')}] "
                f"{type(exc).__name__}: {exc}"
            )
    return total
