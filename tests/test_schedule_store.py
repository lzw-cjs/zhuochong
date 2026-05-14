"""ScheduleStore 单元测试"""
import pytest
from unittest.mock import patch
from datetime import datetime
from data.schedule_store import ScheduleStore
from data.event import Event


@pytest.fixture
def store(tmp_path):
    with patch("data.store.APPDATA_DIR", tmp_path):
        yield ScheduleStore()


def make_event(**kwargs):
    defaults = {
        "id": "test-1",
        "title": "测试事件",
        "datetime_str": datetime.now().isoformat(),
        "status": "pending",
    }
    defaults.update(kwargs)
    return Event(**defaults)


class TestScheduleStoreCRUD:
    """增删改查测试"""

    def test_add_event(self, store):
        event = make_event()
        store.add(event)
        events = store.get_all()
        assert len(events) == 1
        assert events[0].id == "test-1"

    def test_get_all_empty(self, store):
        events = store.get_all()
        assert events == []

    def test_get_by_id(self, store):
        store.add(make_event(id="evt-1"))
        store.add(make_event(id="evt-2"))
        result = store.get_by_id("evt-2")
        assert result is not None
        assert result.id == "evt-2"

    def test_get_by_id_not_found(self, store):
        result = store.get_by_id("nonexistent")
        assert result is None

    def test_update_event(self, store):
        event = make_event(id="evt-1", title="原标题")
        store.add(event)

        event.title = "新标题"
        result = store.update(event)
        assert result is True

        loaded = store.get_by_id("evt-1")
        assert loaded.title == "新标题"

    def test_update_nonexistent_event(self, store):
        event = make_event(id="nonexistent")
        result = store.update(event)
        assert result is False

    def test_delete_event(self, store):
        store.add(make_event(id="evt-1"))
        result = store.delete("evt-1")
        assert result is True
        assert store.get_by_id("evt-1") is None

    def test_delete_nonexistent_event(self, store):
        result = store.delete("nonexistent")
        assert result is False

    def test_multiple_events(self, store):
        for i in range(5):
            store.add(make_event(id=f"evt-{i}"))
        events = store.get_all()
        assert len(events) == 5


class TestScheduleStoreExportImport:
    """导入导出测试"""

    def test_export_json(self, store, tmp_path):
        store.add(make_event(id="evt-1"))
        store.add(make_event(id="evt-2"))

        export_path = tmp_path / "export.json"
        store.export_json(str(export_path))

        assert export_path.exists()

    def test_import_json(self, store, tmp_path):
        # 先添加一个事件
        store.add(make_event(id="existing"))

        # 创建导入文件
        import json
        import_data = {
            "events": [
                make_event(id="imported-1").to_dict(),
                make_event(id="imported-2").to_dict(),
            ]
        }
        import_path = tmp_path / "import.json"
        import_path.write_text(json.dumps(import_data), encoding="utf-8")

        count = store.import_json(str(import_path))
        assert count == 2

        events = store.get_all()
        assert len(events) == 3  # existing + 2 imported

    def test_import_json_deduplication(self, store, tmp_path):
        """导入时已存在的事件不会重复"""
        store.add(make_event(id="same-id"))

        import json
        import_data = {"events": [make_event(id="same-id").to_dict()]}
        import_path = tmp_path / "import.json"
        import_path.write_text(json.dumps(import_data), encoding="utf-8")

        count = store.import_json(str(import_path))
        assert count == 0

        events = store.get_all()
        assert len(events) == 1


class TestScheduleStorePersistence:
    """持久化测试"""

    def test_save_and_load(self, store):
        store.add(make_event(id="persist-1", title="持久化事件"))

        store2 = ScheduleStore()
        events = store2.get_all()
        assert len(events) == 1
        assert events[0].title == "持久化事件"
