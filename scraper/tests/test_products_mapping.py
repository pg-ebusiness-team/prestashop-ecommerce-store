"""save_mapping wołane z wielu wątków, gdy inne wątki dopisują klucze - jak w imporcie równoległym"""
import importlib.util
import json
import threading
from pathlib import Path

# "scraper" w testach to scraper/scraper.py, więc moduł importera ładujemy z pliku
_spec = importlib.util.spec_from_file_location(
    "products_mapping", Path(__file__).parent.parent / "importer" / "products_mapping.py"
)
pm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pm)


def test_save_mapping_concurrent_with_mutations(tmp_path, monkeypatch):
    monkeypatch.setattr(pm, "MAPPING_PATH", tmp_path / "products_mapping.json")
    mapping: dict = {}

    def worker(offset: int) -> None:
        for i in range(300):
            source_id = offset * 1000 + i
            pm.add_product_mapping(mapping, source_id, source_id)
            pm.add_combination_mapping(mapping, source_id, 1, 2)
            mapping[str(source_id)].setdefault("images", {})["7"] = 8
            pm.save_mapping(mapping)

    threads = [threading.Thread(target=worker, args=(n,)) for n in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    pm.save_mapping(mapping)
    saved = json.loads(pm.MAPPING_PATH.read_text(encoding="utf-8"))
    assert len(saved) == 8 * 300
    assert saved == mapping
