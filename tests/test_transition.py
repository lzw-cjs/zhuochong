"""TransitionAnimator 单元测试"""
import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt


class TestTransitionAnimator:
    """状态过渡动画测试"""

    def test_init(self, qtbot):
        from pet.transition import TransitionAnimator

        animator = TransitionAnimator()
        assert animator.is_active is False
        assert animator._from_pixmap is None
        assert animator._to_pixmap is None

    def test_start_transition(self, qtbot):
        from pet.transition import TransitionAnimator

        animator = TransitionAnimator()
        from_pixmap = QPixmap(100, 100)
        from_pixmap.fill(Qt.GlobalColor.red)
        to_pixmap = QPixmap(100, 100)
        to_pixmap.fill(Qt.GlobalColor.blue)

        animator.start_transition(from_pixmap, to_pixmap)
        assert animator.is_active is True

    def test_start_transition_with_none_emits_complete(self, qtbot):
        from pet.transition import TransitionAnimator

        animator = TransitionAnimator()
        to_pixmap = QPixmap(100, 100)

        completed = []
        animator.transition_complete.connect(lambda: completed.append(True))
        animator.start_transition(None, to_pixmap)

        assert len(completed) == 1
        assert animator.is_active is False

    def test_interrupt(self, qtbot):
        from pet.transition import TransitionAnimator

        animator = TransitionAnimator()
        from_pixmap = QPixmap(100, 100)
        to_pixmap = QPixmap(100, 100)

        animator.start_transition(from_pixmap, to_pixmap)
        assert animator.is_active is True

        frames = []
        animator.frame_ready.connect(lambda p: frames.append(p))
        animator.interrupt()

        assert animator.is_active is False
        assert len(frames) == 1  # 应该发射 to_pixmap

    def test_blend_pixmaps_with_valid(self, qtbot):
        from pet.transition import TransitionAnimator

        bottom = QPixmap(100, 100)
        bottom.fill(Qt.GlobalColor.red)
        top = QPixmap(100, 100)
        top.fill(Qt.GlobalColor.blue)

        result = TransitionAnimator._blend_pixmaps(bottom, top, 0.5)
        assert not result.isNull()
        assert result.width() == 100
        assert result.height() == 100

    def test_blend_pixmaps_with_none_bottom(self, qtbot):
        from pet.transition import TransitionAnimator

        top = QPixmap(100, 100)
        result = TransitionAnimator._blend_pixmaps(None, top, 0.5)
        assert not result.isNull()

    def test_blend_pixmaps_with_none_top(self, qtbot):
        from pet.transition import TransitionAnimator

        bottom = QPixmap(100, 100)
        result = TransitionAnimator._blend_pixmaps(bottom, None, 0.5)
        assert not result.isNull()

    def test_blend_pixmaps_with_both_none(self, qtbot):
        from pet.transition import TransitionAnimator

        result = TransitionAnimator._blend_pixmaps(None, None, 0.5)
        assert result.isNull()

    def test_constants(self, qtbot):
        from pet.transition import TransitionAnimator

        assert TransitionAnimator.STEP_MS == 30
        assert TransitionAnimator.TOTAL_STEPS == 10
