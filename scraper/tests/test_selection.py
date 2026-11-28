"""Odrzucanie produktów bez opisu w selektorze importu"""
import importlib.util
from pathlib import Path

# "scraper" w testach to scraper/scraper.py, więc moduł importera ładujemy z pliku
_spec = importlib.util.spec_from_file_location(
    "selection", Path(__file__).parent.parent / "importer" / "selection.py"
)
selection = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(selection)


def test_filter_products_with_description():
    products = {
        1: [{"description": "<p>Wino czerwone</p>"}],
        2: [{"description": "<p> &nbsp;</p>\n"}],
        3: [{"description": None}, {"description": "Opis wariantu"}],
        4: [{}],
    }
    assert set(selection.filter_products_with_description(products)) == {1, 3}


def test_select_products_without_target_takes_all(monkeypatch):
    # Selektor sprawdza zdjęcia na dysku - tu udajemy, że wszystkie istnieją
    monkeypatch.setattr(Path, "is_file", lambda self: True)
    valid = {i: [{"images": [{"id_image": 1}, {"id_image": 2}]}] for i in range(60)}
    categories = {("a", "b"): set(valid)}

    # Test dotyczy tylko target=None - reguły promocji i stanu 0 wyłączone
    selected, _ = selection.select_products(
        valid, categories, target=None,
        minimum_promoted_products=0, minimum_zero_stock_ratio=0,
    )

    assert len(selected) == 60
