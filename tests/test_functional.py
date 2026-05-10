"""综合功能测试：覆盖所有主要功能模块"""
import pytest
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def qapp():
    """创建 QApplication 实例（PySide6 GUI 测试需要）"""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


class TestDataLayer:
    """数据层功能测试"""

    def test_settings_load_save(self, tmp_path, monkeypatch):
        """设置加载和保存功能"""
        monkeypatch.setattr("data.store.APPDATA_DIR", tmp_path)
        from data.settings import Settings

        # 测试默认值
        settings = Settings()
        assert settings.pet_x == 200
        assert settings.pet_y == 200
        assert settings.pet_state == "idle"
        assert settings.volume == 50
        assert settings.muted is False

        # 测试保存和加载
        settings.pet_x = 500
        settings.pet_y = 300
        settings.save()

        loaded = Settings.load()
        assert loaded.pet_x == 500
        assert loaded.pet_y == 300

    def test_event_crud(self, tmp_path, monkeypatch):
        """事件 CRUD 操作"""
        monkeypatch.setattr("data.store.APPDATA_DIR", tmp_path)
        from data.event import Event
        from data.schedule_store import ScheduleStore

        store = ScheduleStore()

        # 创建事件
        event = Event(
            title="测试事件",
            datetime_str="2026-05-10T10:00:00",
            description="测试描述",
            category="工作",
            priority="high"
        )
        store.add(event)

        # 读取事件
        events = store.get_all()
        assert len(events) == 1
        assert events[0].title == "测试事件"

        # 更新事件
        event.title = "更新后的事件"
        store.update(event)
        updated = store.get_by_id(event.id)
        assert updated.title == "更新后的事件"

        # 删除事件
        assert store.delete(event.id) is True
        assert len(store.get_all()) == 0

    def test_calendar_crud(self, tmp_path, monkeypatch):
        """日历 CRUD 操作"""
        monkeypatch.setattr("data.store.APPDATA_DIR", tmp_path)
        from data.calendar_store import CalendarStore

        store = CalendarStore()

        # 应该有默认日历
        calendars = store.get_all()
        assert len(calendars) >= 1
        assert calendars[0].name == "默认"

    def test_json_store_migration(self, tmp_path, monkeypatch):
        """JSON 存储迁移功能"""
        monkeypatch.setattr("data.store.APPDATA_DIR", tmp_path)
        from data.store import JsonStore, register_migration, _MIGRATIONS

        # 清空迁移注册表
        _MIGRATIONS.clear()

        # 注册测试迁移
        @register_migration("test", from_version=1)
        def migrate_v1_to_v2(data):
            data["new_field"] = "added"
            return data

        # 创建 v1 数据
        store = JsonStore("test.json", store_name="test")
        store.save({"_schema_version": 1, "old_field": "value"})

        # 加载并自动迁移
        result = store.load(current_version=2)
        assert result["_schema_version"] == 2
        assert result["new_field"] == "added"
        assert result["old_field"] == "value"

        # 清空
        _MIGRATIONS.clear()


class TestPetCore:
    """宠物核心功能测试"""

    def test_pet_states(self):
        """宠物状态机测试"""
        from pet.states import PetState, can_transition, FRAME_INTERVALS

        # 测试状态值
        assert PetState.IDLE.value == "idle"
        assert PetState.WALK.value == "walk"
        assert PetState.SLEEP.value == "sleep"
        assert PetState.HAPPY.value == "happy"
        assert PetState.ALERT.value == "alert"

        # 测试状态转换
        assert can_transition(PetState.IDLE, PetState.WALK) is True
        assert can_transition(PetState.IDLE, PetState.SLEEP) is True
        assert can_transition(PetState.IDLE, PetState.HAPPY) is True
        assert can_transition(PetState.IDLE, PetState.ALERT) is True
        assert can_transition(PetState.ALERT, PetState.IDLE) is True
        assert can_transition(PetState.ALERT, PetState.WALK) is False

        # 测试帧间隔
        assert FRAME_INTERVALS[PetState.IDLE] == 500
        assert FRAME_INTERVALS[PetState.WALK] == 300
        assert FRAME_INTERVALS[PetState.SLEEP] == 800
        assert FRAME_INTERVALS[PetState.HAPPY] == 200
        assert FRAME_INTERVALS[PetState.ALERT] == 150

    def test_animator_placeholder_frames(self, qapp):
        """动画器占位帧生成测试"""
        from pet.states import PetState
        from pet.animator import generate_all_placeholder_frames

        frames = generate_all_placeholder_frames()
        assert len(frames) == 5  # 5 个状态
        assert PetState.IDLE in frames
        assert PetState.WALK in frames
        assert PetState.SLEEP in frames
        assert PetState.HAPPY in frames
        assert PetState.ALERT in frames

        # 验证每个状态的帧数
        expected_counts = {
            PetState.IDLE: 4,
            PetState.WALK: 6,
            PetState.SLEEP: 4,
            PetState.HAPPY: 4,
            PetState.ALERT: 4,
        }
        for state, expected in expected_counts.items():
            assert len(frames[state]) == expected, f"{state} should have {expected} frames"

    def test_animator_state_transitions(self):
        """动画器状态转换测试"""
        from pet.states import PetState
        from pet.animator import SpriteAnimator, generate_all_placeholder_frames

        animator = SpriteAnimator()
        animator.load_frames(generate_all_placeholder_frames())

        # 初始状态应该是 IDLE
        assert animator.current_state == PetState.IDLE

        # 测试状态转换
        assert animator.set_state(PetState.WALK) is True
        assert animator.current_state == PetState.WALK

        # 测试无效转换
        assert animator.set_state(PetState.SLEEP) is False  # WALK -> SLEEP 不允许
        assert animator.current_state == PetState.WALK  # 状态不变


class TestInteraction:
    """交互功能测试"""

    def test_chat_engine_replies(self):
        """聊天引擎回复测试"""
        from pet.chat_engine import RuleBasedEngine

        engine = RuleBasedEngine()

        # 测试关键词回复
        reply = engine.get_reply("你好")
        assert reply  # 应该有回复

        reply = engine.get_reply("帮助")
        assert reply  # 应该有回复

        reply = engine.get_reply("日程")
        assert reply  # 应该有回复

        # 测试未知输入
        reply = engine.get_reply("asdfghjkl")
        assert reply  # 应该有默认回复

    def test_asset_path_resolution(self):
        """资源路径解析测试"""
        from utils.assets import get_asset_path

        # 测试开发模式
        path = get_asset_path("assets/sounds")
        assert path.is_absolute()
        assert path.name == "sounds"
        assert path.parent.name == "assets"

        # 测试数据路径
        path = get_asset_path("data/chat_rules.json")
        assert path.is_absolute()
        assert path.name == "chat_rules.json"
        assert path.parent.name == "data"


class TestReminderSystem:
    """提醒系统测试"""

    def test_reminder_engine_basic(self, tmp_path, monkeypatch):
        """提醒引擎基本功能测试"""
        monkeypatch.setattr("data.store.APPDATA_DIR", tmp_path)
        from data.event import Event
        from data.schedule_store import ScheduleStore
        from pet.reminder_engine import ReminderEngine

        store = ScheduleStore()
        engine = ReminderEngine(store)

        # 测试抑制功能
        engine.suppress(True)
        engine.suppress(False)

        # 测试清除功能
        engine.clear_fired()
        engine.clear_fired("test_id")

        # 测试停止功能
        engine.stop()

    def test_sound_manager(self, tmp_path):
        """音效管理器测试"""
        from pet.sound_manager import SoundManager

        # 创建测试音效目录
        sound_dir = tmp_path / "sounds"
        sound_dir.mkdir()

        manager = SoundManager(sound_dir)

        # 测试音量设置
        manager.set_volume(0.5)
        manager.set_volume(1.5)  # 应该被限制为 1.0
        manager.set_volume(-0.5)  # 应该被限制为 0.0

        # 测试静音播放
        manager.play_reminder(muted=True)  # 应该不播放

    def test_overdue_detector(self, tmp_path, monkeypatch):
        """超时检测器测试"""
        monkeypatch.setattr("data.store.APPDATA_DIR", tmp_path)
        from data.schedule_store import ScheduleStore
        from pet.overdue_detector import ReminderEngine

        store = ScheduleStore()
        detector = ReminderEngine(store)

        # 测试基本功能
        assert hasattr(detector, 'overdue')
        assert hasattr(detector, 'completed_early')
        assert hasattr(detector, 'mark_completed')
        assert hasattr(detector, 'extend_deadline')
        assert hasattr(detector, 'cancel_event')


class TestScheduleSystem:
    """日程系统测试"""

    def test_event_dialog_creation(self):
        """事件对话框创建测试"""
        from data.event import Event
        from data.calendar_model import Calendar
        from pet.schedule_panel import EventDialog

        # 创建测试事件
        event = Event(
            title="测试事件",
            datetime_str="2026-05-10T10:00:00",
            description="测试描述",
            category="工作",
            priority="high",
            reminder_minutes=30
        )

        # 创建测试日历
        calendars = [Calendar(id="default", name="默认日历", color="#4CAF50")]

        # 测试对话框创建
        dlg = EventDialog(event, calendars)
        assert dlg._title.text() == "测试事件"
        assert dlg._reminder.currentData() == 30

    def test_event_dialog_new_event(self):
        """新事件对话框测试"""
        from data.calendar_model import Calendar
        from pet.schedule_panel import EventDialog

        calendars = [Calendar(id="default", name="默认日历", color="#4CAF50")]

        # 测试新事件对话框
        dlg = EventDialog(None, calendars)
        assert dlg._title.text() == ""
        assert dlg._reminder.currentData() == 15  # 默认 15 分钟


class TestIntegration:
    """集成功能测试"""

    def test_main_imports(self):
        """主模块导入测试"""
        # 测试所有主要模块可以导入
        modules = [
            'data.store',
            'data.settings',
            'data.event',
            'data.schedule_store',
            'data.calendar_store',
            'data.calendar_model',
            'pet.states',
            'pet.animator',
            'pet.behavior',
            'pet.bubble',
            'pet.window',
            'pet.tray',
            'pet.chat_engine',
            'pet.chat_panel',
            'pet.schedule_panel',
            'pet.calendar_grid',
            'pet.overdue_widget',
            'pet.overdue_detector',
            'pet.reminder_engine',
            'pet.sound_manager',
            'utils.assets',
        ]

        for mod in modules:
            try:
                __import__(mod)
            except Exception as e:
                pytest.fail(f"Failed to import {mod}: {e}")

    def test_file_syntax(self):
        """文件语法检查"""
        import py_compile

        files_to_check = [
            'main.py',
            'pet/animator.py',
            'pet/behavior.py',
            'pet/bubble.py',
            'pet/calendar_grid.py',
            'pet/chat_engine.py',
            'pet/chat_panel.py',
            'pet/overdue_detector.py',
            'pet/overdue_widget.py',
            'pet/reminder_engine.py',
            'pet/schedule_panel.py',
            'pet/sound_manager.py',
            'pet/states.py',
            'pet/tray.py',
            'pet/window.py',
            'data/calendar_model.py',
            'data/calendar_store.py',
            'data/event.py',
            'data/schedule_store.py',
            'data/settings.py',
            'data/store.py',
        ]

        for file in files_to_check:
            try:
                py_compile.compile(file, doraise=True)
            except py_compile.PyCompileError as e:
                pytest.fail(f"Syntax error in {file}: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
