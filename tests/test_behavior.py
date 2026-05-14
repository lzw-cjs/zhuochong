"""BehaviorScheduler 单元测试"""
import pytest
from unittest.mock import MagicMock, patch, call
from pet.states import PetState


class TestBehaviorScheduler:
    """行为调度器测试"""

    @patch("pet.behavior.QTimer")
    def test_init(self, mock_timer_cls):
        from pet.behavior import BehaviorScheduler

        animator = MagicMock()
        scheduler = BehaviorScheduler(animator)

        assert scheduler._animator is animator
        assert scheduler.IDLE_TIMEOUT == 5 * 60 * 1000
        assert scheduler.RETURN_TIMEOUT == 10 * 1000
        assert scheduler.RANDOM_MIN == 30 * 1000
        assert scheduler.RANDOM_MAX == 90 * 1000

    @patch("pet.behavior.QTimer")
    def test_start_sets_idle(self, mock_timer_cls):
        from pet.behavior import BehaviorScheduler

        animator = MagicMock()
        scheduler = BehaviorScheduler(animator)
        scheduler.start()

        animator.set_state.assert_called_with(PetState.IDLE)

    @patch("pet.behavior.QTimer")
    def test_stop_stops_all_timers(self, mock_timer_cls):
        from pet.behavior import BehaviorScheduler

        mock_timers = [MagicMock(), MagicMock(), MagicMock()]
        mock_timer_cls.side_effect = mock_timers

        animator = MagicMock()
        scheduler = BehaviorScheduler(animator)
        scheduler.stop()

        for timer in mock_timers:
            timer.stop.assert_called()

    @patch("pet.behavior.QTimer")
    def test_user_interaction_sets_happy(self, mock_timer_cls):
        from pet.behavior import BehaviorScheduler

        mock_timers = [MagicMock(), MagicMock(), MagicMock()]
        mock_timer_cls.side_effect = mock_timers

        animator = MagicMock()
        scheduler = BehaviorScheduler(animator)
        scheduler.on_user_interaction()

        animator.set_state.assert_called_with(PetState.HAPPY)

    @patch("pet.behavior.QTimer")
    def test_idle_timeout_sets_sleep(self, mock_timer_cls):
        from pet.behavior import BehaviorScheduler

        mock_timers = [MagicMock(), MagicMock(), MagicMock()]
        mock_timer_cls.side_effect = mock_timers

        animator = MagicMock()
        scheduler = BehaviorScheduler(animator)
        scheduler._on_idle_timeout()

        animator.set_state.assert_called_with(PetState.SLEEP)

    @patch("pet.behavior.QTimer")
    def test_return_timeout_sets_idle(self, mock_timer_cls):
        from pet.behavior import BehaviorScheduler

        mock_timers = [MagicMock(), MagicMock(), MagicMock()]
        mock_timer_cls.side_effect = mock_timers

        animator = MagicMock()
        scheduler = BehaviorScheduler(animator)
        scheduler._on_return_timeout()

        animator.set_state.assert_called_with(PetState.IDLE)

    @patch("pet.behavior.QTimer")
    def test_random_switch_sets_walk_when_idle(self, mock_timer_cls):
        from pet.behavior import BehaviorScheduler

        mock_timers = [MagicMock(), MagicMock(), MagicMock()]
        mock_timer_cls.side_effect = mock_timers

        animator = MagicMock()
        animator.current_state = PetState.IDLE
        scheduler = BehaviorScheduler(animator)
        scheduler._on_random_switch()

        animator.set_state.assert_called_with(PetState.WALK)

    @patch("pet.behavior.QTimer")
    def test_random_switch_no_effect_when_not_idle(self, mock_timer_cls):
        from pet.behavior import BehaviorScheduler

        mock_timers = [MagicMock(), MagicMock(), MagicMock()]
        mock_timer_cls.side_effect = mock_timers

        animator = MagicMock()
        animator.current_state = PetState.SLEEP
        scheduler = BehaviorScheduler(animator)
        scheduler._on_random_switch()

        animator.set_state.assert_not_called()

    @patch("pet.behavior.QTimer")
    def test_walk_done_returns_to_idle(self, mock_timer_cls):
        from pet.behavior import BehaviorScheduler

        mock_timers = [MagicMock(), MagicMock(), MagicMock()]
        mock_timer_cls.side_effect = mock_timers

        animator = MagicMock()
        animator.current_state = PetState.WALK
        scheduler = BehaviorScheduler(animator)
        scheduler._on_walk_done()

        animator.set_state.assert_called_with(PetState.IDLE)

    @patch("pet.behavior.QTimer")
    def test_walk_done_no_effect_when_not_walk(self, mock_timer_cls):
        from pet.behavior import BehaviorScheduler

        mock_timers = [MagicMock(), MagicMock(), MagicMock()]
        mock_timer_cls.side_effect = mock_timers

        animator = MagicMock()
        animator.current_state = PetState.IDLE
        scheduler = BehaviorScheduler(animator)
        scheduler._on_walk_done()

        animator.set_state.assert_not_called()
