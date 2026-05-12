"""语音合成模块：edge-tts 合成 + PySide6 QMediaPlayer 播放"""
import asyncio
import io

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False

from PySide6.QtCore import QThread, Signal, QBuffer, QIODevice, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput


TTS_VOICES = {
    "zh-CN-XiaoxiaoNeural": "晓晓（女声·温柔）",
    "zh-CN-YunxiNeural": "云希（男声·阳光）",
    "zh-CN-XiaoyiNeural": "晓伊（女声·活泼）",
    "zh-CN-YunjianNeural": "云健（男声·沉稳）",
}


class EdgeTTSPlayer:
    """edge-tts 语音合成 + QMediaPlayer 播放。

    edge-tts 输出 MP3 格式，必须使用 QMediaPlayer 播放
    （QSoundEffect 只支持 WAV）。
    """

    def __init__(
        self,
        voice: str = "zh-CN-XiaoxiaoNeural",
        rate: str = "+0%",
        volume: int = 80,
    ):
        self._voice = voice
        self._rate = rate
        self._volume = volume

        # 播放器
        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)
        self._buffer: QBuffer | None = None
        self._temp_file: str | None = None

    def set_voice(self, voice: str) -> None:
        self._voice = voice

    def set_rate(self, rate: str) -> None:
        self._rate = rate

    def set_volume(self, volume: int) -> None:
        self._volume = max(0, min(100, volume))
        self._audio_output.setVolume(self._volume / 100.0)

    def play(self, mp3_data: bytes) -> None:
        """播放 MP3 音频数据。"""
        if not mp3_data:
            return
        self.stop()

        self._buffer = QBuffer()
        self._buffer.setData(mp3_data)
        self._buffer.open(QIODevice.OpenModeFlag.ReadOnly)
        self._player.setSourceDevice(
            self._buffer, QUrl("file://dummy.mp3")
        )
        self._audio_output.setVolume(self._volume / 100.0)
        self._player.play()

    def stop(self) -> None:
        """停止当前播放。"""
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.stop()

    def is_playing(self) -> bool:
        return (
            self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
        )

    @property
    def voice(self) -> str:
        return self._voice

    @property
    def rate(self) -> str:
        return self._rate


class TTSWorker(QThread):
    """在工作线程中执行 edge-tts 语音合成。"""

    playback_ready = Signal(bytes)
    error_occurred = Signal(str)

    def __init__(
        self,
        text: str,
        voice: str = "zh-CN-XiaoxiaoNeural",
        rate: str = "+0%",
        parent=None,
    ):
        super().__init__(parent)
        self._text = text
        self._voice = voice
        self._rate = rate

    def run(self):
        if not HAS_EDGE_TTS:
            self.error_occurred.emit("edge-tts 未安装")
            return
        try:
            buf = asyncio.run(self._synthesize())
            if buf:
                self.playback_ready.emit(buf)
            else:
                self.error_occurred.emit("合成结果为空")
        except Exception as e:
            self.error_occurred.emit(str(e))

    async def _synthesize(self) -> bytes | None:
        communicate = edge_tts.Communicate(
            self._text, self._voice, rate=self._rate
        )
        buf = io.BytesIO()
        await communicate.save(buf)
        data = buf.getvalue()
        return data if data else None
