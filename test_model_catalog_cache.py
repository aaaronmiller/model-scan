"""model_catalog.load_cache keeps an unreadable cache aside (version-ledger idea SD-033)."""
import model_catalog


def test_corrupt_cache_is_copied_aside(tmp_path, monkeypatch):
    cache = tmp_path / "model-catalog.json"
    cache.write_text("{not json")
    monkeypatch.setattr(model_catalog, "CACHE_PATH", cache)
    assert model_catalog.load_cache() == {"models": {}, "refreshed_at": None}
    kept = list(tmp_path.glob("model-catalog.json.corrupt.*"))
    assert len(kept) == 1 and kept[0].read_text() == "{not json"
    assert cache.exists()
