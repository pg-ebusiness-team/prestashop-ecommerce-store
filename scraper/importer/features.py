"""Import cech produktów (zakładka „Szczegóły” na karcie produktu).

W źródle cechy to pary nazwa-wartość, np. Kraj: Szkocja, Alkohol: 40%. Jedna cecha może mieć kilka
wartości (np. Rodzaj: Smakowa, Ziołowy) - PrestaShop łączy je wtedy w jedną pozycję, wartości w osobnych liniach.

Cechy i wartości rozpoznajemy po nazwie, a nie po lokalnym pliku mapowania: przed importem pobieramy
wszystkie istniejące (dwa zapytania), więc ponowne uruchomienie albo reset bazy nie tworzy duplikatów
i nie zostawia nieaktualnych ID.
"""
import xml.etree.ElementTree as ET

from scraper.importer.api_client import PrestaShopAPI

LANGUAGE_ID = 1


def collect_features(products: list[dict]) -> dict[str, tuple[int, set[str]]]:
    """
    Zbiera cechy z produktów: nazwa -> (pozycja w źródle, zbiór wartości).

    Pozycja ze źródła wyznacza kolejność cech na karcie produktu (Kraj, Region, Alkohol...).
    """

    features: dict[str, tuple[int, set[str]]] = {}

    for product in products:
        for feature in product.get("features") or []:
            name = str(feature["name"]).strip()
            value = str(feature["value"]).strip()

            if not name or not value:
                continue

            _, values = features.setdefault(name, (int(feature.get("position") or 0), set()))
            values.add(value)

    return features


def _language_text(element: ET.Element | None, language_id: int = LANGUAGE_ID) -> str | None:
    if element is None:
        return None

    for language in element.findall("language"):
        if language.get("id") == str(language_id):
            return (language.text or "").strip()

    return None


def _lang_element(parent: ET.Element, tag: str, text: str, language_id: int = LANGUAGE_ID) -> None:
    element = ET.SubElement(parent, tag)
    ET.SubElement(element, "language", {"id": str(language_id)}).text = text


def _created_id(response: str, node: str) -> int:
    id_element = ET.fromstring(response).find(f"./{node}/id")

    if id_element is None or not id_element.text:
        raise RuntimeError(f"PrestaShop nie zwrócił ID utworzonego zasobu {node}.")

    return int(id_element.text)


def load_existing_features(api: PrestaShopAPI) -> dict[str, int]:
    """Zwraca istniejące cechy sklepu: nazwa -> ID."""

    response = api.get("product_features", params={"display": "[id,name]", "limit": "0,1000"})
    result: dict[str, int] = {}

    for feature in ET.fromstring(response).findall(".//product_feature"):
        name = _language_text(feature.find("name"))
        id_element = feature.find("id")

        if name and id_element is not None and id_element.text:
            result.setdefault(name, int(id_element.text))

    return result


def load_existing_values(api: PrestaShopAPI) -> dict[tuple[int, str], int]:
    """Zwraca istniejące wartości predefiniowane: (ID cechy, wartość) -> ID wartości."""

    response = api.get(
        "product_feature_values",
        params={"display": "[id,id_feature,value,custom]", "limit": "0,100000"}
    )
    result: dict[tuple[int, str], int] = {}

    for value in ET.fromstring(response).findall(".//product_feature_value"):
        id_element = value.find("id")
        feature_id = value.find("id_feature")
        custom = value.find("custom")
        text = _language_text(value.find("value"))

        if custom is not None and custom.text == "1":
            continue  # wartości własne są przypięte do jednego produktu, nie używamy ich ponownie

        if text and id_element is not None and id_element.text and feature_id is not None and feature_id.text:
            result.setdefault((int(feature_id.text), text), int(id_element.text))

    return result


def build_feature_xml(name: str, position: int) -> str:
    root = ET.Element("prestashop")
    feature = ET.SubElement(root, "product_feature")
    ET.SubElement(feature, "position").text = str(position)
    _lang_element(feature, "name", name)

    return ET.tostring(root, encoding="unicode")


def build_feature_value_xml(feature_id: int, value: str) -> str:
    root = ET.Element("prestashop")
    feature_value = ET.SubElement(root, "product_feature_value")
    ET.SubElement(feature_value, "id_feature").text = str(feature_id)
    ET.SubElement(feature_value, "custom").text = "0"  # predefiniowana: wspólna dla wielu produktów
    _lang_element(feature_value, "value", value)

    return ET.tostring(root, encoding="unicode")


def import_features(api: PrestaShopAPI, products: list[dict]) -> tuple[dict, dict[tuple[str, str], tuple[int, int]]]:
    """
    Tworzy brakujące cechy i ich wartości.

    Zwraca licznik operacji oraz mapowanie (nazwa, wartość) -> (ID cechy, ID wartości),
    z którego korzysta build_product_xml.
    """

    counts = {"created": 0, "updated": 0, "rejected": 0}
    resolved: dict[tuple[str, str], tuple[int, int]] = {}

    existing_features = load_existing_features(api)
    existing_values = load_existing_values(api)

    # Cechy w kolejności źródła, żeby nowe dostały w sklepie kolejne pozycje w tym samym porządku
    for name, (position, values) in sorted(collect_features(products).items(), key=lambda item: item[1][0]):
        try:
            feature_id = existing_features.get(name)

            if feature_id is None:
                feature_id = _created_id(api.post("product_features", build_feature_xml(name, position)), "product_feature")
                existing_features[name] = feature_id
                counts["created"] += 1
            else:
                counts["updated"] += 1
        except Exception as exc:  # noqa: BLE001
            counts["rejected"] += 1 + len(values)
            print(f"[CECHA] {name}: {exc}")
            continue

        for value in sorted(values):
            try:
                value_id = existing_values.get((feature_id, value))

                if value_id is None:
                    value_id = _created_id(
                        api.post("product_feature_values", build_feature_value_xml(feature_id, value)),
                        "product_feature_value"
                    )
                    existing_values[(feature_id, value)] = value_id
                    counts["created"] += 1
                else:
                    counts["updated"] += 1

                resolved[(name, value)] = (feature_id, value_id)
            except Exception as exc:  # noqa: BLE001
                counts["rejected"] += 1
                print(f"[CECHA] {name}: {value}: {exc}")

    return counts, resolved


def count_features_dry_run(products: list[dict]) -> dict:
    """Podgląd: liczba cech i wartości w źródle, bez zapytań do sklepu."""

    features = collect_features(products)
    print(f"Cechy źródłowe: {len(features)} cech, {sum(len(v) for _, v in features.values())} wartości.")

    return {"created": 0, "updated": 0, "rejected": 0}


def product_feature_ids(product: dict, resolved: dict[tuple[str, str], tuple[int, int]]) -> list[tuple[int, int]]:
    """Zwraca pary (ID cechy, ID wartości) produktu, bez duplikatów, w kolejności ze źródła."""

    result: list[tuple[int, int]] = []

    for feature in product.get("features") or []:
        ids = resolved.get((str(feature["name"]).strip(), str(feature["value"]).strip()))

        if ids is not None and ids not in result:
            result.append(ids)

    return result
