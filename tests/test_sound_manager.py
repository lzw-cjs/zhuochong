"""SoundManager 单元测试"""
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path


class TestSoundManager:
    """SoundManager 的行为测试。"""

    @patch("pet.sound_manager.QSoundEffect")
    def test_play_reminder_not_muted(self, mock_qse_cls):
        """未静音时，play_reminder 应调用 play()。"""
        mock_effect = MagicMock()
        mock_qse_cls.return_value = mock_effect

        from pet.sound_manager import SoundManager
        sm = SoundManager(Path("assets/sounds"))
        sm.play_reminder(muted=False)

        mock_effect.play.assert_called_once()

    @patch("pet.sound_manager.QSoundEffect")
    def test_play_reminder_muted(self, mock_qse_cls):
        """静音时，play_reminder 不应调用 play()。"""
        mock_effect = MagicMock()
        mock_qse_cls.return_value = mock_effect

        from pet.sound_manager import SoundManager
        sm = SoundManager(Path("assets/sounds"))
        sm.play_reminder(muted=True)

        mock_effect.play.assert_not_called()

    @patch("pet.sound_manager.QSoundEffect")
    def test_volume_clamping(self, mock_qse_cls):
        """set_volume 应将音量限制在 0.0 ~ 1.0。"""
        mock_effect = MagicMock()
        mock_qse_cls.return_value = mock_effect

        from pet.sound_manager import SoundManager
        sm = SoundManager(Path("assets/sounds"))

        # 超出上限
        sm.set_volume(1.5)
        mock_effect.setVolume.assert_called_with(1.0)

        # 超出下限
        sm.set_volume(-0.5)
        mock_effect.setVolume.assert_called_with(0.0)

    @patch("pet.sound_manager.QSoundEffect")
    def test_missing_sound_file(self, mock_qse_cls):
        """声音文件不存在时，play_reminder 不应报错。"""
        mock_effect = MagicMock()
        mock_qse_cls.return_value = mock_effect

        from pet.sound_manager import SoundManager
        sm = SoundManager(Path("/nonexistent/path"))
        sm.play_reminder(muted=False)  # 不应抛异常

        mock_effect.play.assert_not_called()
