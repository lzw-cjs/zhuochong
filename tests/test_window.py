"""PetWindow 单元测试"""
import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import Qt, QPoint, QSize, QRect
from PySide6.QtGui import QPixmap, QKeyEvent


class TestPetWindow:
    """宠物窗口测试"""

    def test_init(self, qtbot):
        from pet.window import PetWindow

        window = PetWindow()
        assert window._scale == 1.0
        assert window._sprite_x == 200
        assert window._sprite_y == 200
        assert window._current_pixmap is None
        assert window._dragging is False
        assert window._costume_enabled is True

    def test_init_with_scale(self, qtbot):
        from pet.window import PetWindow

        window = PetWindow(scale=1.5)
        assert window._scale == 1.5

    def test_window_flags(self, qtbot):
        from pet.window import PetWindow

        window = PetWindow()
        flags = window.windowFlags()

        assert flags & Qt.WindowType.FramelessWindowHint
        assert flags & Qt.WindowType.WindowStaysOnTopHint
        assert flags & Qt.WindowType.Tool

    def test_translucent_background(self, qtbot):
        from pet.window import PetWindow

        window = PetWindow()
        assert window.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        assert window.testAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)

    def test_focus_policy(self, qtbot):
        from pet.window import PetWindow

        window = PetWindow()
        assert window.focusPolicy() == Qt.FocusPolicy.StrongFocus

    def test_set_pixmap(self, qtbot):
        from pet.window import PetWindow

        window = PetWindow()
        pixmap = QPixmap(100, 100)
        window.set_pixmap(pixmap)

        assert window._current_pixmap is pixmap

    def test_get_sprite_rect_with_pixmap(self, qtbot):
        from pet.window import PetWindow

        window = PetWindow(scale=1.0)
        pixmap = QPixmap(100, 100)
        window.set_pixmap(pixmap)

        rect = window._get_sprite_rect()
        expected_size = int(180 * 1.4 * 1.0)
        assert rect.width() == expected_size
        assert rect.height() == expected_size

    def test_get_sprite_rect_without_pixmap(self, qtbot):
        from pet.window import PetWindow

        window = PetWindow()
        rect = window._get_sprite_rect()
        assert rect.width() == 0
        assert rect.height() == 0

    def test_is_point_on_sprite(self, qtbot):
        from pet.window import PetWindow

        window = PetWindow(scale=1.0)
        window._sprite_x = 100
        window._sprite_y = 100
        pixmap = QPixmap(100, 100)
        window.set_pixmap(pixmap)

        # 点在精灵范围内
        assert window._is_point_on_sprite(QPoint(150, 150)) is True

        # 点在精灵范围外
        assert window._is_point_on_sprite(QPoint(50, 50)) is False

    def test_set_sprite_position(self, qtbot):
        from pet.window import PetWindow

        window = PetWindow()
        signals = []
        window.position_changed.connect(lambda x, y: signals.append((x, y)))

        window.set_sprite_position(300, 400)

        assert window._sprite_x == 300
        assert window._sprite_y == 400
        assert len(signals) == 1
        assert signals[0] == (300, 400)

    def test_get_position(self, qtbot):
        from pet.window import PetWindow

        window = PetWindow()
        window._sprite_x = 150
        window._sprite_y = 250

        pos = window.get_position()
        assert pos == (150, 250)

    def test_set_scale(self, qtbot):
        from pet.window import PetWindow

        window = PetWindow()
        signals = []
        window.scale_changed.connect(lambda s: signals.append(s))

        window.set_scale(2.0)

        assert window._scale == 2.0
        assert len(signals) == 1
        assert signals[0] == 2.0

    def test_base_canvas_constant(self, qtbot):
        from pet.window import PetWindow

        assert PetWindow.BASE_CANVAS == 180

    def test_drag_threshold(self, qtbot):
        from pet.window import PetWindow

        window = PetWindow()
        assert window._drag_threshold == 5

    def test_signals_exist(self, qtbot):
        from pet.window import PetWindow

        window = PetWindow()

        # 检查信号存在
        assert hasattr(window, 'position_changed')
        assert hasattr(window, 'clicked')
        assert hasattr(window, 'schedule_requested')
        assert hasattr(window, 'chat_requested')
        assert hasattr(window, 'settings_requested')
        assert hasattr(window, 'debug_state_requested')
        assert hasattr(window, 'scale_changed')
        assert hasattr(window, 'costume_toggle')
        assert hasattr(window, 'costume_try')
