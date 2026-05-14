"""MovementController 单元测试"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from pet.states import PetState


class TestMovementController:
    """移动控制器测试"""

    @patch("pet.movement.QTimer")
    def test_init(self, mock_timer_cls):
        from pet.movement import MovementController

        window = MagicMock()
        animator = MagicMock()
        controller = MovementController(window, animator)

        assert controller._window is window
        assert controller._animator is animator
        assert controller.is_moving is False

    @patch("pet.movement.QTimer")
    def test_state_changed_to_walk(self, mock_timer_cls):
        from pet.movement import MovementController

        mock_timer = MagicMock()
        mock_timer_cls.return_value = mock_timer

        window = MagicMock()
        screen = MagicMock()
        geo = MagicMock()
        geo.left.return_value = 0
        geo.right.return_value = 1920
        geo.top.return_value = 0
        geo.bottom.return_value = 1080
        screen.availableGeometry.return_value = geo
        window.screen.return_value = screen
        window.BASE_CANVAS = 180
        window._scale = 1.0

        animator = MagicMock()
        controller = MovementController(window, animator)
        controller._on_state_changed(PetState.WALK)

        assert controller.is_moving is True
        mock_timer.start.assert_called_with(40)

    @patch("pet.movement.QTimer")
    def test_state_changed_to_idle(self, mock_timer_cls):
        from pet.movement import MovementController

        mock_timer = MagicMock()
        mock_timer_cls.return_value = mock_timer

        window = MagicMock()
        animator = MagicMock()
        controller = MovementController(window, animator)

        controller._moving = True
        controller._on_state_changed(PetState.IDLE)

        assert controller.is_moving is False
        mock_timer.stop.assert_called()

    @patch("pet.movement.QTimer")
    def test_stop(self, mock_timer_cls):
        from pet.movement import MovementController

        mock_timer = MagicMock()
        mock_timer_cls.return_value = mock_timer

        window = MagicMock()
        animator = MagicMock()
        controller = MovementController(window, animator)

        controller._moving = True
        controller.stop()

        assert controller.is_moving is False
        mock_timer.stop.assert_called()

    @patch("pet.movement.QTimer")
    def test_move_step_reaches_target(self, mock_timer_cls):
        from pet.movement import MovementController

        mock_timer = MagicMock()
        mock_timer_cls.return_value = mock_timer

        window = MagicMock()
        window.get_position.return_value = (100, 100)

        screen = MagicMock()
        geo = MagicMock()
        geo.left.return_value = 0
        geo.right.return_value = 1920
        geo.top.return_value = 0
        geo.bottom.return_value = 1080
        screen.availableGeometry.return_value = geo
        window.screen.return_value = screen
        window.BASE_CANVAS = 180
        window._scale = 1.0

        animator = MagicMock()
        controller = MovementController(window, animator)

        # 设置目标很近
        controller._target = (105, 105)
        controller._step_count = 0
        controller._move_step()

        # 应该换新目标
        assert controller._step_count == 1

    @patch("pet.movement.QTimer")
    def test_move_step_moves_toward_target(self, mock_timer_cls):
        from pet.movement import MovementController

        mock_timer = MagicMock()
        mock_timer_cls.return_value = mock_timer

        window = MagicMock()
        window.get_position.return_value = (100, 100)

        animator = MagicMock()
        controller = MovementController(window, animator)

        # 设置目标较远
        controller._target = (500, 500)
        controller._move_step()

        # 应该调用 set_sprite_position
        window.set_sprite_position.assert_called()

    @patch("pet.movement.QTimer")
    def test_move_step_no_target_picks_new(self, mock_timer_cls):
        from pet.movement import MovementController

        mock_timer = MagicMock()
        mock_timer_cls.return_value = mock_timer

        window = MagicMock()
        screen = MagicMock()
        geo = MagicMock()
        geo.left.return_value = 0
        geo.right.return_value = 1920
        geo.top.return_value = 0
        geo.bottom.return_value = 1080
        screen.availableGeometry.return_value = geo
        window.screen.return_value = screen
        window.BASE_CANVAS = 180
        window._scale = 1.0

        animator = MagicMock()
        controller = MovementController(window, animator)

        controller._target = None
        controller._move_step()

        # 应该设置新目标
        assert controller._target is not None
