"""通知音效管理器"""
from pathlib import Path
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtCore import QUrl


class SoundManager:
    """管理提醒通知音效播放。"""

    def __init__(self, sound_dir: Path):
        self._effect = QSoundEffect()
        self._effect.setVolume(0.5)
        self._sound_dir = sound_dir

    def set_volume(self, volume: float) -> None:
        """设置音量 (0.0 ~ 1.0)。"""
        self._effect.setVolume(max(0.0, min(1.0, volume)))

    def play_reminder(self, muted: bool = False) -> None:
        """播放提醒音效。muted=True 时不播放。"""
        if muted:
            return
        sound_path = self._sound_dir / "reminder.wav"
        if not sound_path.exists():
            return
        self._effect.setSource(QUrl.fromLocalFile(str(sound_path)))
        self._effect.play()
