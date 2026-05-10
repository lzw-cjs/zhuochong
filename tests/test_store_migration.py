import json
import pytest
from pathlib import Path
from data.store import JsonStore, register_migration, _MIGRATIONS, APPDATA_DIR


@pytest.fixture(autouse=True)
def clean_migrations():
    """Clear migration registry before each test."""
    _MIGRATIONS.clear()
    yield
    _MIGRATIONS.clear()


@pytest.fixture
def tmp_store(tmp_path, monkeypatch):
    """Redirect APPDATA_DIR to tmp_path for isolated tests."""
    monkeypatch.setattr("data.store.APPDATA_DIR", tmp_path)
    return tmp_path


def test_register_migration_adds_to_registry():
    """register_migration() stores the function in _MIGRATIONS."""
    @register_migration("test_store", from_version=1)
    def migrate_v1(data):
        return data
    assert "test_store" in _MIGRATIONS
    assert 1 in _MIGRATIONS["test_store"]
    assert _MIGRATIONS["test_store"][1] is migrate_v1


def test_load_runs_migration_on_version_mismatch(tmp_store):
    """JsonStore.load(current_version=2) runs migration when stored version is 1."""
    store = JsonStore("test.json")
    store.save({"_schema_version": 1, "items": ["a"]})

    @register_migration("test", from_version=1)
    def add_count(data):
        data["count"] = len(data.get("items", []))
        return data

    result = store.load(current_version=2)
    assert result["_schema_version"] == 2
    assert result["count"] == 1
    assert result["items"] == ["a"]


def test_load_skips_migration_when_versions_match(tmp_store):
    """No migration runs when stored version equals current version."""
    store = JsonStore("test.json")
    store.save({"_schema_version": 2, "items": ["a"]})

    call_count = [0]
    @register_migration("test", from_version=1)
    def should_not_run(data):
        call_count[0] += 1
        return data

    store.load(current_version=2)
    assert call_count[0] == 0


def test_load_returns_default_when_file_missing(tmp_store):
    """When file doesn't exist, default is returned without migration."""
    store = JsonStore("nonexistent.json")
    result = store.load(default={"items": []}, current_version=3)
    assert result == {"items": []}


def test_migration_chains_sequentially(tmp_store):
    """Multiple migrations run in order: v1->v2->v3."""
    store = JsonStore("test.json")
    store.save({"_schema_version": 1, "value": 10})

    @register_migration("test", from_version=1)
    def v1_to_v2(data):
        data["value"] = data["value"] * 2
        return data

    @register_migration("test", from_version=2)
    def v2_to_v3(data):
        data["value"] = data["value"] + 1
        return data

    result = store.load(current_version=3)
    assert result["_schema_version"] == 3
    assert result["value"] == 21  # 10 * 2 + 1


def test_migration_preserves_existing_data(tmp_store):
    """Migration preserves all existing fields."""
    store = JsonStore("test.json")
    original = {"_schema_version": 1, "name": "test", "items": [1, 2, 3], "nested": {"a": 1}}
    store.save(original)

    @register_migration("test", from_version=1)
    def add_field(data):
        data["new_field"] = "added"
        return data

    result = store.load(current_version=2)
    assert result["name"] == "test"
    assert result["items"] == [1, 2, 3]
    assert result["nested"] == {"a": 1}
    assert result["new_field"] == "added"
    assert result["_schema_version"] == 2


def test_migration_persists_result(tmp_store):
    """After migration, the migrated data is saved to disk."""
    store = JsonStore("test.json")
    store.save({"_schema_version": 1, "value": 0})

    @register_migration("test", from_version=1)
    def bump(data):
        data["value"] = 99
        return data

    store.load(current_version=2)

    # Re-read from disk to confirm persistence
    with open(store.filepath, "r", encoding="utf-8") as f:
        on_disk = json.load(f)
    assert on_disk["_schema_version"] == 2
    assert on_disk["value"] == 99
