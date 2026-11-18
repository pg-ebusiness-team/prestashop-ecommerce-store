import re
from decimal import Decimal, ROUND_HALF_UP


DEFAULT_WEIGHT = 1.5
PACKAGE_WEIGHT = 0.05

VOLUME_PATTERN = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(ml|l)\b",
    re.IGNORECASE
)

GRAMMAGE_PATTERN = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(kg|g)\b",
    re.IGNORECASE
)


def round_weight(value: float) -> float:
    """Zaokrągla wagę do dwóch miejsc po przecinku."""

    return float(
        Decimal(str(value)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )
    )


def extract_volume_liters(text: str) -> float | None:
    """Wyciąga jednoznaczną pojemność z tekstu i przelicza ją na litry."""

    matches = VOLUME_PATTERN.findall(str(text or ""))
    volumes = set()

    for value, unit in matches:
        volume = float(value.replace(",", "."))

        if unit.lower() == "ml":
            volume /= 1000

        if volume > 0:
            volumes.add(round(volume, 4))

    if len(volumes) != 1:
        return None

    return volumes.pop()


def extract_grammage_kg(text: str) -> float | None:
    """Wyciąga jednoznaczną gramaturę z tekstu i przelicza ją na kilogramy."""

    matches = GRAMMAGE_PATTERN.findall(str(text or ""))
    weights = set()

    for value, unit in matches:
        weight = float(value.replace(",", "."))

        if unit.lower() == "g":
            weight /= 1000

        if weight > 0:
            weights.add(round(weight, 4))

    if len(weights) != 1:
        return None

    return weights.pop()


def find_product_volume(product: dict) -> float | None:
    """Szuka pojemności w atrybutach, a następnie w nazwie produktu."""

    for attribute in (product.get("attributes") or {}).values():
        if "pojem" in str(attribute.get("group", "")).lower():
            volume = extract_volume_liters(attribute.get("name"))

            if volume is not None:
                return volume

    # Akcesoria, np. torby na butelki, nie powinny
    # otrzymywać wagi na podstawie pojemności z nazwy.
    if str(product.get("category", "")).lower() == "akcesoria":
        return None

    return extract_volume_liters(product.get("name", ""))


def find_product_grammage(product: dict) -> float | None:
    """Szuka gramatury w atrybutach, a następnie w nazwie produktu."""

    for attribute in (product.get("attributes") or {}).values():
        if "gramat" in str(attribute.get("group", "")).lower():
            grammage = extract_grammage_kg(attribute.get("name"))

            if grammage is not None:
                return grammage

    return extract_grammage_kg(product.get("name", ""))


def calculate_product_weight(product: dict) -> float:
    """
    Oblicza szacowaną wagę produktu.

    Priorytet:
    1. Pojemność.
    2. Gramatura + narzut na opakowanie.
    3. Waga domyślna.
    """

    volume = find_product_volume(product)

    if volume is not None:
        return round_weight(1.5 * volume + 0.25)

    grammage = find_product_grammage(product)

    if grammage is not None:
        return round_weight(grammage + PACKAGE_WEIGHT)

    return DEFAULT_WEIGHT


def assign_product_weights(product: dict) -> None:
    """
    Przypisuje wagi produktowi i jego wariantom.

    Produkt bez wariantów:
        product["weight"] = waga produktu

    Produkt z wariantami:
        product["weight"] = najniższa waga wariantu
        combination["weight"] = bezwzględna waga wariantu
        combination["weight_delta"] = różnica względem wagi bazowej
    """

    combinations = product.get("combinations") or []

    if not combinations:
        product["weight"] = calculate_product_weight(product)
        return

    for combination in combinations:
        combination["weight"] = calculate_product_weight(combination)

    base_weight = min(
        combination["weight"] for combination in combinations
    )

    product["weight"] = base_weight

    for combination in combinations:
        combination["weight_delta"] = round_weight(
            combination["weight"] - base_weight
        )
