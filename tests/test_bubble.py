"""ChatBubble 单元测试"""
import pytest
from unittest.mock import MagicMock
from PySide6.QtCore import Qt


class TestChatBubble:
    """对话气泡测试"""

    def test_init(self, qtbot):
        from pet.bubble import ChatBubble

        bubble = ChatBubble()
        assert bubble.windowFlags() & Qt.WindowType.FramelessWindowHint
        assert bubble.windowFlags() & Qt.WindowType.WindowStaysOnTopHint
        assert bubble.windowFlags() & Qt.WindowType.Tool

    def test_show_message(self, qtbot):
        from pet.bubble import ChatBubble

        bubble = ChatBubble()
        bubble.show_message("你好世界", 500, 300)

        assert bubble.isVisible()
        assert bubble._label.text() == "你好世界"

    def test_show_message_with_custom_duration(self, qtbot):
        from pet.bubble import ChatBubble

        bubble = ChatBubble()
        bubble.show_message("测试", 100, 100, duration_ms=5000)

        assert bubble.isVisible()

    def test_auto_dismiss(self, qtbot):
        from pet.bubble import ChatBubble

        bubble = ChatBubble()
        bubble.show_message("自动消失", 100, 100, duration_ms=100)

        # 等待定时器触发
        qtbot.wait(150)
        assert not bubble.isVisible()

    def test_label_word_wrap(self, qtbot):
        from pet.bubble import ChatBubble

        bubble = ChatBubble()
        assert bubble._label.wordWrap() is True
        assert bubble._label.maximumWidth() == 180

    def test_label_alignment(self, qtbot):
        from pet.bubble import ChatBubble

        bubble = ChatBubble()
        assert bubble._label.alignment() == Qt.AlignmentFlag.AlignCenter

    def test_translucent_background(self, qtbot):
        from pet.bubble import ChatBubble

        bubble = ChatBubble()
        assert bubble.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        assert bubble.testAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
