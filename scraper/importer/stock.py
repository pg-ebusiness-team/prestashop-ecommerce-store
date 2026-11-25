"""Obsługa stanów magazynowych PrestaShop 8."""
import os
import xml.etree.ElementTree as ET

MAX_STOCK_QUANTITY = 10


def limit_combination_stock(combinations: list[dict]) -> list[dict]:
    """Ogranicza łączny stan wszystkich kombinacji produktu do 10 sztuk."""
    normalized = []
    quantities = []

    for combination in combinations:
        quantity = combination.get("quantity")

        if (
            not isinstance(quantity, int)
            or isinstance(quantity, bool)
            or quantity < 0
        ):
            raise ValueError(
                f"Nieprawidłowy stan kombinacji: {quantity}"
            )

        normalized.append(dict(combination))
        quantities.append(quantity)

    total = sum(quantities)

    if total <= MAX_STOCK_QUANTITY:
        return normalized

    # Proporcjonalny podział dostępnych 10 sztuk.
    allocations = [
        divmod(quantity * MAX_STOCK_QUANTITY, total)
        for quantity in quantities
    ]

    remaining = MAX_STOCK_QUANTITY - sum(
        allocated for allocated, _ in allocations
    )

    # Pozostałe sztuki przydzielamy wariantom z największą resztą.
    priority = sorted(
        range(len(quantities)),
        key=lambda i: (
            -allocations[i][1],
            -quantities[i],
            i
        )
    )

    for i in priority[:remaining]:
        allocated, remainder = allocations[i]
        allocations[i] = (allocated + 1, remainder)

    for combination, (allocated, _) in zip(normalized, allocations):
        combination["quantity"] = allocated

    return normalized

def _shop_scope() -> tuple[int, int]:
    return (
        int(os.getenv("PS_STOCK_SHOP_ID", "1")),
        int(os.getenv("PS_STOCK_SHOP_GROUP_ID", "0")),
    )


def find_stock_available(api, product_id: int, combination_id: int = 0) -> int | None:
    """Zwraca ID rekordu stock_available w określonym kontekście sklepu."""
    shop_id, shop_group_id = _shop_scope()
    response = api.get(
        "stock_availables",
        params={
            "filter[id_product]": f"[{product_id}]",
            "filter[id_product_attribute]": f"[{combination_id}]",
            "filter[id_shop]": f"[{shop_id}]",
            "filter[id_shop_group]": f"[{shop_group_id}]",
            "display": "[id,id_product,id_product_attribute,id_shop,id_shop_group,quantity]",
            "limit": "0,100",
        },
    )
    root = ET.fromstring(response)
    matches = root.findall("./stock_availables/stock_available")
    if not matches:
        return None
    if len(matches) > 1:
        raise RuntimeError(
            f"Wiele rekordów stock_available dla produktu {product_id}, "
            f"kombinacji {combination_id}, sklepu {shop_id} i grupy {shop_group_id}."
        )
    value = matches[0].findtext("id")
    if not value:
        raise RuntimeError("PrestaShop nie zwrócił ID rekordu stock_available.")
    return int(value)


def _build_stock_xml(
    product_id: int,
    combination_id: int,
    quantity: int,
    stock_id: int | None = None,
) -> str:
    shop_id, shop_group_id = _shop_scope()
    root = ET.Element("prestashop")
    stock = ET.SubElement(root, "stock_available")
    if stock_id is not None:
        ET.SubElement(stock, "id").text = str(stock_id)
    ET.SubElement(stock, "id_product").text = str(product_id)
    ET.SubElement(stock, "id_product_attribute").text = str(combination_id)
    ET.SubElement(stock, "id_shop").text = str(shop_id)
    ET.SubElement(stock, "id_shop_group").text = str(shop_group_id)
    ET.SubElement(stock, "quantity").text = str(quantity)
    ET.SubElement(stock, "depends_on_stock").text = "0"
    ET.SubElement(stock, "out_of_stock").text = "2"
    return ET.tostring(root, encoding="unicode")


def update_stock(api, product_id: int, quantity: int, combination_id: int = 0) -> str:
    """Aktualizuje istniejący rekord albo tworzy go, jeśli go brakuje."""
    if (
        not isinstance(quantity, int)
        or isinstance(quantity, bool)
        or quantity < 0
    ):
        raise ValueError(f"Nieprawidłowa ilość produktu: {quantity}")

    quantity = min(quantity, MAX_STOCK_QUANTITY)

    stock_id = find_stock_available(api, product_id, combination_id)
    if stock_id is None:
        api.post(
            "stock_availables",
            _build_stock_xml(product_id, combination_id, quantity),
        )
        return "created"

    response = api.get(f"stock_availables/{stock_id}")
    root = ET.fromstring(response)
    stock = root.find("./stock_available")
    if stock is None:
        raise RuntimeError(f"Nie znaleziono zasobu stock_available {stock_id}.")

    quantity_element = stock.find("quantity")
    if quantity_element is None:
        raise RuntimeError("Zasób stock_available nie zawiera pola quantity.")
    quantity_element.text = str(quantity)

    # Zachowujemy pola sklepu i ustawienia zwrócone przez PrestaShop.
    api.put("stock_availables", stock_id, ET.tostring(root, encoding="unicode"))
    return "updated"


def import_stock(api, product_id: int, quantity: int, combination_id: int = 0) -> str:
    return update_stock(api, product_id, quantity, combination_id)
