"""Główny, idempotentny importer danych do PrestaShop 8.

Uruchamianie z katalogu głównego repozytorium:
    python -m scraper.importer.main --dry-run
    python -m scraper.importer.main --execute

Wymagane w .env przy --execute:
    SHOP_URL=https://localhost:8443
    PS_API_KEY=...
    PS_TAX_RULES_GROUP_MAP={"0":ID,"5":ID,"8":ID,"23":ID}

Mapowanie musi zawierać osobne ID tax_rules_group dla każdej stawki VAT
występującej w danych. Nie należy przypisywać jednej grupy wszystkim produktom.

"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


def load_env_file(path: Path = Path(".env")) -> None:
    """Wczytuje prosty plik .env bez nadpisywania zmiennych środowiskowych."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def resolve_products_dir(cli_value: str | None) -> Path:
    """Wykrywa katalog danych zarówno ze starszego, jak i nowszego scrapera."""
    configured = cli_value or os.getenv("PS_PRODUCTS_DIR")
    if configured:
        path = Path(configured)
        if not path.is_dir():
            raise FileNotFoundError(f"Nie znaleziono katalogu produktów: {path}")
        return path

    for candidate in (Path("scraper_results/products"), Path("scraper/products")):
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(
        "Nie znaleziono danych produktów. Oczekiwano scraper_results/products "
        "lub scraper/products."
    )


def report_section(title: str, counts: Counter[str]) -> None:
    print(f"\n{title}")
    print(f"  Utworzone:      {counts['created']}")
    print(f"  Zaktualizowane: {counts['updated']}")
    print(f"  Odrzucone:      {counts['rejected']}")


def import_all_categories(
    api: Any,
    dry_run: bool,
    selected_categories: dict
) -> tuple[Counter[str], dict[str, int], dict[str, int]]:
    """Importuje kategorie główne i podkategorie."""
    from scraper.importer import categories as cat
    from scraper.importer.categories_mapping import (
        add_mapping,
        get_prestashop_id,
        load_mapping,
        save_mapping,
    )

    mapping = load_mapping(cat.SOURCE_PATH, cat.MAPPING_PATH)
    counts: Counter[str] = Counter()
    name_to_id: dict[str, int] = {}
    url_to_id: dict[str, int] = {}
    dry_id = -1
    root_id = int(os.getenv("PS_ROOT_CATEGORY_ID", cat.ROOT_CATEGORY_ID))
    language_id = int(os.getenv("PS_LANGUAGE_ID", cat.LANGUAGE_ID))

    def process(item: dict, parent_id: int) -> int:
        nonlocal dry_id
        name, url = item["name"], item["url"]
        current_id = get_prestashop_id(mapping, url)

        if dry_run:
            if current_id is not None:
                counts["updated"] += 1
                return int(current_id)

            counts["created"] += 1
            placeholder = dry_id
            dry_id -= 1
            return placeholder

        # Zawsze szukamy kategorii po stabilnym kluczu:
        # link_rewrite + id_parent.
        existing_id = cat.find_existing_category(api, name, parent_id)

        if existing_id is not None:
            add_mapping(mapping, url, existing_id, cat.MAPPING_PATH)
            cat.update_category(
                api, mapping, name, url, root_id, language_id
            )
            counts["updated"] += 1
            return int(existing_id)

        current_id = cat.create_category(
            api, mapping, name, url, root_id, language_id
        )
        counts["created"] += 1
        return int(current_id)

    selected_category_keys = {
    (
        cat.generate_link_rewrite(main_name),
        cat.generate_link_rewrite(sub_name)
    )
    for main_name, sub_name in selected_categories
}

    for group in mapping:
        main = group["main_category"]

        selected_subcategories = [
            sub
            for sub in group.get("subcategories", [])
            if (
                cat.generate_link_rewrite(main["name"]),
                cat.generate_link_rewrite(sub["name"])
            ) in selected_category_keys
        ]

        if not selected_subcategories:
            continue

        try:
            main_id = process(main, root_id)
            main["prestashop_id"] = main_id
            url_to_id[main["url"]] = main_id
            name_to_id[cat.generate_link_rewrite(main["name"])] = main_id

        except Exception as exc:  # noqa: BLE001
            counts["rejected"] += 1
            print(f"[KATEGORIA] {main.get('name')}: {exc}")
            counts["rejected"] += len(selected_subcategories)
            continue

        for sub in selected_subcategories:
            try:
                sub_id = process(sub, main_id)
                sub["prestashop_id"] = sub_id
                url_to_id[sub["url"]] = sub_id
                name_to_id[cat.generate_link_rewrite(sub["name"])] = sub_id

            except Exception as exc:  # noqa: BLE001
                counts["rejected"] += 1
                print(f"[PODKATEGORIA] {sub.get('name')}: {exc}")

    if not dry_run:
        save_mapping(mapping, cat.MAPPING_PATH)
    return counts, url_to_id, name_to_id

def load_category_name_map(selected_categories: dict) -> dict[str, int]:
    """Wczytuje ID wcześniej zaimportowanych kategorii."""
    from scraper.importer import categories as cat
    from scraper.importer.categories_mapping import load_mapping

    mapping = load_mapping(cat.SOURCE_PATH, cat.MAPPING_PATH)

    selected_category_keys = {
        (
            cat.generate_link_rewrite(main_name),
            cat.generate_link_rewrite(sub_name)
        )
        for main_name, sub_name in selected_categories
    }

    name_to_id: dict[str, int] = {}
    missing: list[str] = []

    for group in mapping:
        main = group["main_category"]

        selected_subcategories = [
            sub
            for sub in group.get("subcategories", [])
            if (
                cat.generate_link_rewrite(main["name"]),
                cat.generate_link_rewrite(sub["name"])
            ) in selected_category_keys
        ]

        if not selected_subcategories:
            continue

        main_id = main.get("prestashop_id")

        if main_id is None:
            missing.append(main["name"])
        else:
            name_to_id[cat.generate_link_rewrite(main["name"])] = int(main_id)

        for sub in selected_subcategories:
            sub_id = sub.get("prestashop_id")

            if sub_id is None:
                missing.append(sub["name"])
            else:
                name_to_id[cat.generate_link_rewrite(sub["name"])] = int(sub_id)

    if missing:
        raise RuntimeError(
            "Brak ID zaimportowanych kategorii: "
            + ", ".join(missing)
            + ". Najpierw wykonaj make import-categories."
        )

    return name_to_id

def collect_attributes(
    source_records: list[dict]
) -> tuple[dict[int, str], dict[int, tuple[int, str]], int]:

    groups: dict[int, str] = {}
    values: dict[int, tuple[int, str]] = {}
    rejected_files = 0

    for raw in source_records:
        file_path = raw.get("source_file", "<nieznany plik>")

        try:
            data = raw["data"]
            attrs = data.get("attributes") or {}

            if not isinstance(attrs, dict):
                raise TypeError("Pole attributes nie jest obiektem.")

            for attr in attrs.values():
                if not isinstance(attr, dict):
                    raise TypeError("Nieprawidłowy rekord atrybutu.")

                group_id = int(attr["id_attribute_group"])
                attr_id = int(attr["id_attribute"])
                group_name = str(attr["group"])
                attr_name = str(attr["name"])

                if group_id in groups and groups[group_id] != group_name:
                    raise ValueError(f"Konflikt nazwy grupy {group_id}.")

                if attr_id in values and values[attr_id] != (group_id, attr_name):
                    raise ValueError(f"Konflikt wartości atrybutu {attr_id}.")

                groups[group_id] = group_name
                values[attr_id] = (group_id, attr_name)

        except (KeyError, TypeError, ValueError) as exc:
            rejected_files += 1
            print(f"[ATRYBUTY — REKORD] {file_path}: {exc}")

    return groups, values, rejected_files


def import_all_attributes(
    api: Any,
    dry_run: bool,
    source_records: list[dict]
) -> tuple[Counter[str], dict]:

    from scraper.importer.attributes import (
        import_attribute_group,
        import_attribute_value,
    )
    from scraper.importer.attributes_mapping import load_mapping

    mapping = load_mapping()
    counts: Counter[str] = Counter()

    groups, values, bad_files = collect_attributes(source_records)
    counts["rejected"] += bad_files

    if dry_run:
        counts["created"] = sum(
            str(k) not in mapping["groups"] for k in groups
        )
        counts["updated"] = sum(
            str(k) in mapping["groups"] for k in groups
        )
        counts["created"] += sum(
            str(k) not in mapping["attributes"] for k in values
        )
        counts["updated"] += sum(
            str(k) in mapping["attributes"] for k in values
        )

        print(
            f"Atrybuty wybranych produktów: "
            f"{len(groups)} grup, {len(values)} wartości."
        )

        return counts, mapping

    for source_group_id, group_name in sorted(groups.items()):
        try:
            import_attribute_group(
                api, source_group_id, group_name, mapping
            )
            counts["updated"] += 1

        except Exception as exc:  # noqa: BLE001
            counts["rejected"] += 1
            print(f"[GRUPA ATRYBUTÓW] {group_name}: {exc}")

    for source_attribute_id, (source_group_id, name) in sorted(values.items()):
        group_mapping = mapping["groups"].get(str(source_group_id))

        if not group_mapping:
            counts["rejected"] += 1
            print(
                f"[ATRYBUT] {name}: "
                f"brak mapowania grupy {source_group_id}."
            )
            continue

        try:
            import_attribute_value(
                api,
                source_attribute_id,
                source_group_id,
                name,
                int(group_mapping["prestashop_id"]),
                mapping,
            )
            counts["updated"] += 1

        except Exception as exc:  # noqa: BLE001
            counts["rejected"] += 1
            print(f"[ATRYBUT] {name}: {exc}")

    return counts, mapping


def resolve_category_id(
    source_file_name: str,
    category_name_map: dict[str, int],
    products_dir: Path
) -> int | None:
    """Dopasowuje kategorię po nazwie katalogu, a nie po slugu URL."""
    from scraper.importer.categories import generate_link_rewrite

    source_file = Path(source_file_name)

    try:
        relative = source_file.relative_to(products_dir)
    except ValueError:
        try:
            relative = source_file.resolve().relative_to(products_dir.resolve())
        except (ValueError, OSError):
            relative = source_file

    # Struktura: kategoria/podkategoria/ID/pliki.json
    directory_names = list(relative.parts[:-2])

    # Najpierw szukamy najbardziej szczegółowej kategorii.
    for directory_name in reversed(directory_names):
        normalized_name = generate_link_rewrite(directory_name)

        category_id = category_name_map.get(normalized_name)

        if category_id is not None:
            return category_id

    return None


def normalize_vat_rate(value: Any) -> str:
    try:
        return format(Decimal(str(value)).normalize(), "f")
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Nieprawidłowa stawka VAT: {value}") from exc


def load_tax_rules_map(cli_default_id: int | None, products: list[dict]) -> dict[str, int]:
    """Wczytuje mapowanie stawka VAT -> ID tax_rules_group w PrestaShop."""
    raw = os.getenv("PS_TAX_RULES_GROUP_MAP", "").strip()
    mapping: dict[str, int] = {}
    if raw:
        try:
            parsed = json.loads(raw)
            if not isinstance(parsed, dict):
                raise TypeError("PS_TAX_RULES_GROUP_MAP musi być obiektem JSON.")
            mapping = {
                normalize_vat_rate(rate): int(group_id)
                for rate, group_id in parsed.items()
            }
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise ValueError(f"Nieprawidłowe PS_TAX_RULES_GROUP_MAP: {exc}") from exc

    rates = sorted({normalize_vat_rate(product["vat_rate"]) for product in products})
    legacy = cli_default_id
    if not mapping and legacy is None:
        legacy_raw = os.getenv("PS_TAX_RULES_GROUP_ID", "")
        if legacy_raw.isdigit():
            legacy = int(legacy_raw)

    if not mapping and legacy:
        if len(rates) == 1:
            mapping[rates[0]] = legacy
        else:
            raise ValueError(
                "Źródło zawiera kilka stawek VAT "
                f"({', '.join(rates)}). Ustaw PS_TAX_RULES_GROUP_MAP."
            )

    missing = [rate for rate in rates if rate not in mapping]
    if missing:
        raise ValueError(
            "Brak mapowania grup podatkowych dla stawek VAT: "
            + ", ".join(missing)
            + ". Uzupełnij PS_TAX_RULES_GROUP_MAP."
        )
    invalid = {rate: group_id for rate, group_id in mapping.items() if group_id <= 0}
    if invalid:
        raise ValueError(f"ID grup reguł podatkowych muszą być dodatnie: {invalid}")
    return mapping


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Idempotentny importer produktów, kategorii i wariantów do PrestaShop."
    )

    start_time = time.perf_counter()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--execute", action="store_true", help="Wykonaj import do PrestaShop.")
    mode.add_argument("--dry-run", action="store_true", help="Podgląd bez zmian (domyślnie).")
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument(
        "--categories-only",
        action="store_true",
        help="Importuj wyłącznie kategorie."
    )
    scope.add_argument(
        "--products-only",
        action="store_true",
        help="Importuj atrybuty, produkty i warianty bez importowania kategorii."
    )
    parser.add_argument("--products-dir", default=None, help="Katalog źródłowych JSON-ów.")
    parser.add_argument("--tax-rules-group-id", type=int, default=None)
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Maksymalna liczba produktów (domyślnie wszystkie poprawne)."
    )
    parser.add_argument(
        "--workers", type=int, default=None,
        help="Liczba wątków importu produktów (domyślnie PS_IMPORT_WORKERS lub 8)."
    )
    args = parser.parse_args()

    load_env_file()
    workers = max(1, args.workers or int(os.getenv("PS_IMPORT_WORKERS", "8")))
    dry_run = not args.execute
    products_dir = resolve_products_dir(args.products_dir)

    shop_url = os.getenv("SHOP_URL", f"https://localhost:{os.getenv('HTTPS_PORT', '8443')}")
    api_key = os.getenv("PS_API_KEY")

    print("=" * 68)
    print("IMPORTER PRESTASHOP — PODGLĄD" if dry_run else "IMPORTER PRESTASHOP — IMPORT")
    print(f"Katalog danych: {products_dir}")
    print("=" * 68)

    if not dry_run and not api_key:
        print("BŁĄD: brak PS_API_KEY w .env.", file=sys.stderr)
        return 2

    from scraper.importer.api_client import PrestaShopAPI
    from scraper.importer.features import (
        count_features_dry_run,
        import_features,
        product_feature_ids,
    )
    from scraper.importer.products import (
        group_products,
        import_product,
        normalize_product,
        validate_product,
    )
    from scraper.importer.products_mapping import load_mapping as load_products_mapping
    from scraper.importer.selection import PHOTOS_DIR, run_selection

    selected_products, selected_categories = run_selection(
        source_dir=products_dir,
        photos_dir=PHOTOS_DIR,
        target=args.limit
    )

    if args.categories_only:
        api = PrestaShopAPI(shop_url, api_key) if not dry_run else None

        category_counts, _, _ = import_all_categories(
            api, dry_run, selected_categories
        )

        report_section("KATEGORIE", category_counts)

        elapsed = time.perf_counter() - start_time
        minutes, seconds = divmod(int(elapsed), 60)
        print(f"\nCzas wykonania: {minutes} min {seconds} s")
        print(
            "\nPodgląd nie modyfikował sklepu."
            if dry_run else "\nImport kategorii zakończony."
        )

        return 1 if category_counts["rejected"] else 0

    raw_products = [
        {
            "data": record,
            "source_file": record["_source_file"]
        }
        for records in selected_products.values()
        for record in records
    ]

    print(f"\nSelektor wybrał {len(selected_products)} unikalnych produktów.")
    print(f"Wybrane rekordy źródłowe: {len(raw_products)}")
    print(f"Zachowane podkategorie: {len(selected_categories)}")

    normalized: list[dict] = []
    rejected_records = 0

    for raw in raw_products:
        try:
            product = normalize_product(raw)
            product["source_file"] = raw.get("source_file", "")
            errors = validate_product(product)
            if errors:
                rejected_records += 1
                print(f"[PRODUKT {product.get('source_id')}] {'; '.join(errors)}")
                continue
            normalized.append(product)
        except Exception as exc:  # noqa: BLE001
            rejected_records += 1
            print(f"[PRODUKT] Błąd normalizacji: {exc}")

    grouped = group_products(normalized)

    try:
        if dry_run and not os.getenv("PS_TAX_RULES_GROUP_MAP") and not args.tax_rules_group_id and not os.getenv("PS_TAX_RULES_GROUP_ID"):
            tax_map = {}
            detected_rates = sorted({normalize_vat_rate(p["vat_rate"]) for p in grouped})
            print("Wykryte stawki VAT: " + ", ".join(detected_rates))
        else:
            tax_map = load_tax_rules_map(args.tax_rules_group_id, grouped)
    except ValueError as exc:
        print(f"BŁĄD KONFIGURACJI VAT: {exc}", file=sys.stderr)
        return 2

    api = PrestaShopAPI(shop_url, api_key, pool_size=workers) if not dry_run else None

    # Kategorie importujemy tylko wtedy, gdy nie wybrano trybu products-only.
    if args.products_only:
        category_counts: Counter[str] = Counter()
        category_names = load_category_name_map(selected_categories)
        print("\nUżywam istniejącego mapowania kategorii.")
    else:
        category_counts, _category_ids, category_names = import_all_categories(
            api, dry_run, selected_categories
        )

    attribute_counts, _ = import_all_attributes(
        api, dry_run, raw_products
    )

    if not dry_run and attribute_counts["rejected"] > 0:
        print(
            "\nBŁĄD: Import atrybutów zakończył się błędami "
            f"({attribute_counts['rejected']} odrzuconych). "
            "Przerywam import produktów, aby nie tworzyć "
            "produktów bez poprawnych kombinacji.",
            file=sys.stderr,
        )
        return 1

    grouped = group_products(normalized)

    # Cechy (zakładka „Szczegóły”) po nazwie, przed produktami - produkt dostaje je w tym samym zapytaniu
    resolved_features: dict | None = None
    if dry_run:
        feature_counts = Counter(count_features_dry_run(grouped))
    else:
        try:
            counts, resolved_features = import_features(api, grouped)
            feature_counts = Counter(counts)
        except Exception as exc:  # noqa: BLE001
            # Bez cech import produktów idzie dalej, a ich obecne cechy w sklepie zostają nietknięte
            feature_counts = Counter({"rejected": 1})
            print(f"[CECHY] Pominięto import cech: {type(exc).__name__}: {exc}")

    product_counts: Counter[str] = Counter()
    mapping = load_products_mapping()

    def import_one(product: dict, category_ids: list[int]) -> str:
        tax_group_id = tax_map[normalize_vat_rate(product["vat_rate"])]
        feature_ids = (
            product_feature_ids(product, resolved_features)
            if resolved_features is not None else None
        )
        _, operation = import_product(
            api, product, mapping, category_ids, tax_group_id, feature_ids
        )
        return operation

    to_import: list[tuple[dict, list[int]]] = []
    for product in grouped:
        source_id = product.get("source_id")
        # dict.fromkeys: bez duplikatów (pliki wariantów), z zachowaniem kolejności - pierwsza = domyślna
        category_ids = list(dict.fromkeys(
            category_id
            for source_file in product["source_files"]
            if (category_id := resolve_category_id(source_file, category_names, products_dir)) is not None
        ))
        if not category_ids:
            product_counts["rejected"] += 1
            print(f"[PRODUKT {source_id}] Nie znaleziono kategorii dla: {product.get('source_file')}")
        elif dry_run:
            product_counts["updated" if str(source_id) in mapping else "created"] += 1
        else:
            to_import.append((product, category_ids))

    if to_import:
        print(f"\nImport {len(to_import)} produktów w {workers} wątkach.")
        # Każdy wątek pracuje na innym produkcie, więc ruszają tylko własne klucze mapowania
        executor = ThreadPoolExecutor(max_workers=workers)
        try:
            futures = {
                executor.submit(import_one, product, category_ids): product.get("source_id")
                for product, category_ids in to_import
            }
            for index, future in enumerate(as_completed(futures), start=1):
                try:
                    product_counts[future.result()] += 1
                except Exception as exc:  # noqa: BLE001
                    product_counts["rejected"] += 1
                    print(f"[PRODUKT {futures[future]}] {type(exc).__name__}: {exc}")
                if index % 100 == 0:
                    print(f"Postęp: {index}/{len(to_import)} produktów.")
        except KeyboardInterrupt:
            # Bez tego Ctrl+C czekałby na wszystkie zakolejkowane produkty
            executor.shutdown(wait=False, cancel_futures=True)
            raise
        executor.shutdown()

    report_section("KATEGORIE", category_counts)
    report_section("ATRYBUTY", attribute_counts)
    if not dry_run:
        report_section("CECHY (nazwy i wartości)", feature_counts)
    report_section("PRODUKTY", product_counts)

    total_rejected = (
        rejected_records + category_counts["rejected"] + attribute_counts["rejected"]
        + feature_counts["rejected"] + product_counts["rejected"]
    )
    print("\nPODSUMOWANIE")
    print(f"  Pliki produktów:       {len(raw_products)}")
    print(f"  Poprawne rekordy:      {len(normalized)}")
    print(f"  Produkty po grupowaniu:{len(grouped):>6}")
    print(f"  Odrzucone rekordy:     {total_rejected}")
    elapsed = time.perf_counter() - start_time
    minutes, seconds = divmod(int(elapsed), 60)

    print(f"\nCzas wykonania: {minutes} min {seconds} s")
    print("\nPodgląd nie modyfikował sklepu." if dry_run else "\nImport zakończony.")
    return 1 if total_rejected else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nPrzerwano przez użytkownika.", file=sys.stderr)
        raise SystemExit(130)
    except Exception as exc:  # noqa: BLE001
        print(f"BŁĄD KRYTYCZNY: {type(exc).__name__}: {exc}", file=sys.stderr)
        traceback.print_exc()
        raise SystemExit(1)
