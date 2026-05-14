"""StateIndicator 单元测试"""
import pytest
from pet.states import PetState


class TestStateIndicator:
    """状态指示器测试"""

    def test_init(self, qtbot):
        from pet.indicator import StateIndicator

        indicator = StateIndicator()
        assert indicator._scale == 1.0
        assert indicator._current_state == PetState.IDLE
        assert not indicator.isVisible()

    def test_state_emoji_mapping(self, qtbot):
        from pet.indicator import StateIndicator

        # IDLE 没有 emoji
        assert StateIndicator.STATE_EMOJI[PetState.IDLE] == ""

        # 其他状态有 emoji
        assert StateIndicator.STATE_EMOJI[PetState.WALK] != ""
        assert StateIndicator.STATE_EMOJI[PetState.SLEEP] != ""
        assert StateIndicator.STATE_EMOJI[PetState.HAPPY] != ""
        assert StateIndicator.STATE_EMOJI[PetState.ALERT] != ""

    def test_show_for_state_with_emoji(self, qtbot):
        from pet.indicator import StateIndicator

        indicator = StateIndicator()
        indicator.show_for_state(PetState.WALK, 100, 100)

        assert indicator.isVisible()
        assert indicator._current_state == PetState.WALK

    def test_show_for_state_idle_hides(self, qtbot):
        from pet.indicator import StateIndicator

        indicator = StateIndicator()
        indicator.show_for_state(PetState.WALK, 100, 100)
        assert indicator.isVisible()

        indicator.show_for_state(PetState.IDLE, 100, 100)
        assert not indicator.isVisible()

    def test_set_scale(self, qtbot):
        from pet.indicator import StateIndicator

        indicator = StateIndicator()
        indicator.set_scale(2.0)

        assert indicator._scale == 2.0
        assert indicator._indicator_size == int(48 * 2.0)
        assert indicator._line_length == int(40 * 2.0)

    def test_set_sprite_width(self, qtbot):
        from pet.indicator import StateIndicator

        indicator = StateIndicator()
        indicator.set_sprite_width(300)
        assert indicator._sprite_display_width == 300

    def test_update_position_when_visible(self, qtbot):
        from pet.indicator import StateIndicator

        indicator = StateIndicator()
        indicator.show_for_state(PetState.WALK, 100, 100)
        indicator.update_position(200, 200)

        # 位置应该更新
        assert indicator.isVisible()

    def test_update_position_when_hidden(self, qtbot):
        from pet.indicator import StateIndicator

        indicator = StateIndicator()
        indicator.update_position(200, 200)

        # 隐藏时不更新
        assert not indicator.isVisible()

    def test_float_animation(self, qtbot):
        from pet.indicator import StateIndicator

        indicator = StateIndicator()
        initial_offset = indicator._float_offset

        # 触发动画
        indicator._animate_float()
        assert indicator._float_offset != initial_offset

    def test_constants(self, qtbot):
        from pet.indicator import StateIndicator

        assert StateIndicator.BASE_INDICATOR_SIZE == 48
        assert StateIndicator.BASE_LINE_LENGTH == 40

    def test_window_flags(self, qtbot):
        from pet.indicator import StateIndicator

        indicator = StateIndicator()
        flags = indicator.windowFlags()

        assert flags & 0x00000001  # FramelessWindowHint
        assert flags & 0x00040000  # WindowStaysOnTopHint
        assert flags & 0x00000008  # Tool
