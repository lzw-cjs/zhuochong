"""SchedulePanel 逻辑测试（非 UI 部分）"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime


class TestExtractEventsFromText:
    """从文本提取事件测试"""

    @patch("pet.schedule_panel.ScheduleStore")
    @patch("pet.schedule_panel.CalendarStore")
    def test_extract_date_time_format(self, mock_cal_store, mock_store, qtbot):
        from pet.schedule_panel import SchedulePanel

        panel = SchedulePanel()

        text = "2026-05-10 14:00 开会讨论项目"
        events = panel._extract_events_from_text(text)

        assert len(events) == 1
        assert events[0]["title"] == "开会讨论项目"
        assert "2026-05-10" in events[0]["datetime_str"]

    @patch("pet.schedule_panel.ScheduleStore")
    @patch("pet.schedule_panel.CalendarStore")
    def test_extract_slash_date_format(self, mock_cal_store, mock_store, qtbot):
        from pet.schedule_panel import SchedulePanel

        panel = SchedulePanel()

        text = "2026/5/10 14:00 团队会议"
        events = panel._extract_events_from_text(text)

        assert len(events) == 1
        assert events[0]["title"] == "团队会议"

    @patch("pet.schedule_panel.ScheduleStore")
    @patch("pet.schedule_panel.CalendarStore")
    def test_extract_chinese_date_format(self, mock_cal_store, mock_store, qtbot):
        from pet.schedule_panel import SchedulePanel

        panel = SchedulePanel()

        text = "5月10日 项目评审"
        events = panel._extract_events_from_text(text)

        assert len(events) == 1
        assert events[0]["title"] == "项目评审"

    @patch("pet.schedule_panel.ScheduleStore")
    @patch("pet.schedule_panel.CalendarStore")
    def test_extract_markdown_todo_format(self, mock_cal_store, mock_store, qtbot):
        from pet.schedule_panel import SchedulePanel

        panel = SchedulePanel()

        text = "- [ ] 完成报告 (2026-05-10)"
        events = panel._extract_events_from_text(text)

        assert len(events) == 1
        assert events[0]["title"] == "完成报告"

    @patch("pet.schedule_panel.ScheduleStore")
    @patch("pet.schedule_panel.CalendarStore")
    def test_extract_multiple_events(self, mock_cal_store, mock_store, qtbot):
        from pet.schedule_panel import SchedulePanel

        panel = SchedulePanel()

        text = """2026-05-10 09:00 晨会
2026-05-10 14:00 项目评审
2026-05-11 10:00 客户拜访"""
        events = panel._extract_events_from_text(text)

        assert len(events) == 3

    @patch("pet.schedule_panel.ScheduleStore")
    @patch("pet.schedule_panel.CalendarStore")
    def test_extract_no_events(self, mock_cal_store, mock_store, qtbot):
        from pet.schedule_panel import SchedulePanel

        panel = SchedulePanel()

        text = "这是一段普通文本，没有日期信息"
        events = panel._extract_events_from_text(text)

        assert len(events) == 0

    @patch("pet.schedule_panel.ScheduleStore")
    @patch("pet.schedule_panel.CalendarStore")
    def test_make_event_dict(self, mock_cal_store, mock_store, qtbot):
        from pet.schedule_panel import SchedulePanel

        panel = SchedulePanel()

        event_dict = panel._make_event_dict("测试事件", "2026-05-10T14:00:00")

        assert event_dict["title"] == "测试事件"
        assert event_dict["datetime_str"] == "2026-05-10T14:00:00"
        assert event_dict["category"] == "其他"
        assert event_dict["priority"] == "medium"
        assert event_dict["calendar_id"] == "default"
        assert event_dict["reminder_minutes"] == 15
        assert event_dict["status"] == "pending"
        assert event_dict["completed"] is False
        assert len(event_dict["id"]) == 12


class TestEventDialogLogic:
    """EventDialog 逻辑测试"""

    @patch("pet.schedule_panel.ScheduleStore")
    @patch("pet.schedule_panel.CalendarStore")
    def test_event_dialog_get_event_new(self, mock_cal_store, mock_store, qtbot):
        from pet.schedule_panel import EventDialog
        from data.calendar_model import Calendar

        calendars = [Calendar(id="default", name="默认", color="#8B5A2B")]
        dlg = EventDialog(None, calendars)

        event = dlg.get_event()

        assert event.title == ""
        assert len(event.id) == 12
        assert event.status == "pending"

    @patch("pet.schedule_panel.ScheduleStore")
    @patch("pet.schedule_panel.CalendarStore")
    def test_event_dialog_get_event_edit(self, mock_cal_store, mock_store, qtbot):
        from pet.schedule_panel import EventDialog
        from data.calendar_model import Calendar
        from data.event import Event

        calendars = [Calendar(id="default", name="默认", color="#8B5A2B")]
        existing = Event(
            id="existing-id",
            title="已有事件",
            datetime_str="2026-05-10T14:00:00",
            status="pending",
        )

        dlg = EventDialog(existing, calendars)
        event = dlg.get_event()

        assert event.id == "existing-id"


class TestPasteImportDialogLogic:
    """PasteImportDialog 逻辑测试"""

    @patch("pet.schedule_panel.ScheduleStore")
    @patch("pet.schedule_panel.CalendarStore")
    def test_get_text(self, mock_cal_store, mock_store, qtbot):
        from pet.schedule_panel import PasteImportDialog

        dlg = PasteImportDialog()
        dlg._text_edit.setPlainText("测试文本")

        assert dlg.get_text() == "测试文本"
