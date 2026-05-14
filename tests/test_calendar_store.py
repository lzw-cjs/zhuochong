"""CalendarStore 单元测试"""
import pytest
from unittest.mock import patch
from data.calendar_store import CalendarStore, DEFAULT_CALENDAR
from data.calendar_model import Calendar


@pytest.fixture
def store(tmp_path):
    with patch("data.store.APPDATA_DIR", tmp_path):
        yield CalendarStore()


class TestCalendarStoreInit:
    """初始化测试"""

    def test_default_calendar_exists(self, store):
        cals = store.get_all()
        assert len(cals) >= 1
        assert any(c.id == "default" for c in cals)

    def test_default_calendar_properties(self, store):
        cals = store.get_all()
        default = next(c for c in cals if c.id == "default")
        assert default.name == "默认"
        assert default.color == "#8B5A2B"


class TestCalendarStoreCRUD:
    """增删改查测试"""

    def test_add_calendar(self, store):
        cal = Calendar(id="work", name="工作", color="#FF0000")
        store.add(cal)
        cals = store.get_all()
        assert len(cals) >= 2
        assert any(c.id == "work" for c in cals)

    def test_delete_calendar(self, store):
        cal = Calendar(id="temp", name="临时", color="#00FF00")
        store.add(cal)
        result = store.delete("temp")
        assert result is True
        cals = store.get_all()
        assert not any(c.id == "temp" for c in cals)

    def test_delete_default_calendar_fails(self, store):
        result = store.delete("default")
        assert result is False

    def test_delete_nonexistent_calendar(self, store):
        result = store.delete("nonexistent")
        assert result is False

    def test_multiple_calendars(self, store):
        store.add(Calendar(id="cal1", name="日历1", color="#FF0000"))
        store.add(Calendar(id="cal2", name="日历2", color="#00FF00"))
        store.add(Calendar(id="cal3", name="日历3", color="#0000FF"))
        cals = store.get_all()
        assert len(cals) >= 4  # default + 3


class TestCalendarStorePersistence:
    """持久化测试"""

    def test_save_and_load(self, store):
        cal = Calendar(id="persist", name="持久化测试", color="#123456")
        store.add(cal)

        # 创建新 store 实例加载
        store2 = CalendarStore()
        cals = store2.get_all()
        assert any(c.id == "persist" for c in cals)

    def test_default_always_present(self, store):
        """即使数据中没有 default，也会自动添加"""
        store._save([Calendar(id="custom", name="自定义", color="#ABC").to_dict()])
        cals = store.get_all()
        assert any(c.id == "default" for c in cals)
