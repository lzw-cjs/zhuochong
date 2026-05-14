"""OverdueWidget 单元测试"""
import pytest
from unittest.mock import MagicMock


class TestOverdueWidget:
    """超时通知组件测试"""

    def test_init(self, qtbot):
        from pet.overdue_widget import OverdueWidget

        on_extend = MagicMock()
        on_cancel = MagicMock()

        widget = OverdueWidget("测试事件", on_extend, on_cancel)

        assert widget._event_title == "测试事件"
        assert widget._on_extend is on_extend
        assert widget._on_cancel is on_cancel

    def test_window_flags(self, qtbot):
        from pet.overdue_widget import OverdueWidget
        from PySide6.QtCore import Qt

        widget = OverdueWidget("测试", MagicMock(), MagicMock())
        flags = widget.windowFlags()

        assert flags & Qt.WindowType.FramelessWindowHint
        assert flags & Qt.WindowType.WindowStaysOnTopHint
        assert flags & Qt.WindowType.Tool

    def test_translucent_background(self, qtbot):
        from pet.overdue_widget import OverdueWidget
        from PySide6.QtCore import Qt

        widget = OverdueWidget("测试", MagicMock(), MagicMock())
        assert widget.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def test_fixed_size(self, qtbot):
        from pet.overdue_widget import OverdueWidget

        widget = OverdueWidget("测试", MagicMock(), MagicMock())
        assert widget.width() == 320
        assert widget.height() == 100

    def test_handle_extend(self, qtbot):
        from pet.overdue_widget import OverdueWidget

        on_extend = MagicMock()
        on_cancel = MagicMock()

        widget = OverdueWidget("测试事件", on_extend, on_cancel)
        widget._handle_extend()

        on_extend.assert_called_once_with("测试事件")

    def test_handle_cancel(self, qtbot):
        from pet.overdue_widget import OverdueWidget

        on_extend = MagicMock()
        on_cancel = MagicMock()

        widget = OverdueWidget("测试事件", on_extend, on_cancel)
        widget._handle_cancel()

        on_cancel.assert_called_once_with("测试事件")

    def test_move_direction(self, qtbot):
        from pet.overdue_widget import OverdueWidget

        widget = OverdueWidget("测试", MagicMock(), MagicMock())
        assert widget._direction == 1
        assert widget._speed == 2

    def test_close_stops_timer(self, qtbot):
        from pet.overdue_widget import OverdueWidget

        widget = OverdueWidget("测试", MagicMock(), MagicMock())
        widget.show()
        widget.close()

        # 定时器应该停止
        assert not widget._move_timer.isActive()
