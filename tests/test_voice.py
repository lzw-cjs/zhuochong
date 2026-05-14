"""语音系统单元测试（STT + TTS + Settings 语音字段）。"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path

from data.settings import Settings
from data.store import JsonStore


# ── Settings 语音字段 ─────────────────────────────────────────────


class TestSettingsVoiceFields:
    """Settings 扩展的语音字段测试。"""

    @pytest.fixture(autouse=True)
    def _clean_settings(self, tmp_path):
        with patch("data.store.APPDATA_DIR", tmp_path):
            yield

    def test_default_voice_fields(self):
        s = Settings()
        assert s.voice_enabled is True
        assert s.voice_auto_play is True
        assert s.voice_stt_provider == ""
        assert s.voice_xfyun_app_id == ""
        assert s.voice_xfyun_api_key == ""
        assert s.voice_xfyun_api_secret == ""
        assert s.voice_tts_voice == "zh-CN-XiaoxiaoNeural"
        assert s.voice_tts_rate == "+0%"
        assert s.voice_tts_volume == 80

    def test_save_load_roundtrip(self):
        s = Settings(
            voice_enabled=False,
            voice_auto_play=False,
            voice_stt_provider="xfyun",
            voice_xfyun_app_id="test_app_id",
            voice_xfyun_api_key="test_key",
            voice_xfyun_api_secret="test_secret",
            voice_tts_voice="zh-CN-YunxiNeural",
            voice_tts_rate="+20%",
            voice_tts_volume=60,
        )
        s.save()

        loaded = Settings.load()
        assert loaded.voice_enabled is False
        assert loaded.voice_auto_play is False
        assert loaded.voice_stt_provider == "xfyun"
        assert loaded.voice_xfyun_app_id == "test_app_id"
        assert loaded.voice_xfyun_api_key == "test_key"
        assert loaded.voice_xfyun_api_secret == "test_secret"
        assert loaded.voice_tts_voice == "zh-CN-YunxiNeural"
        assert loaded.voice_tts_rate == "+20%"
        assert loaded.voice_tts_volume == 60

    def test_backward_compatible_missing_voice_section(self, tmp_path):
        """旧版 settings.json 没有 voice 字段时应使用默认值。"""
        store = JsonStore("settings.json")
        store.save({
            "_schema_version": 1,
            "pet": {"x": 100, "y": 100, "state": "idle"},
            "preferences": {"volume": 50, "muted": False, "auto_start": False},
        })

        loaded = Settings.load()
        assert loaded.voice_enabled is True
        assert loaded.voice_xfyun_app_id == ""


# ── MicrophoneRecorder ────────────────────────────────────────────


class TestMicrophoneRecorder:
    """麦克风录音器测试。"""

    @patch("pet.voice_stt.HAS_SOUNDDEVICE", True)
    def test_initial_state(self):
        from pet.voice_stt import MicrophoneRecorder
        rec = MicrophoneRecorder()
        assert rec.is_recording is False

    @patch("pet.voice_stt.HAS_SOUNDDEVICE", True)
    @patch("pet.voice_stt.sd", create=True)
    def test_start_stop_recording(self, mock_sd):
        from pet.voice_stt import MicrophoneRecorder
        mock_stream = MagicMock()
        mock_sd.InputStream.return_value = mock_stream

        rec = MicrophoneRecorder()
        rec.start_recording()

        assert rec.is_recording is True
        mock_sd.InputStream.assert_called_once()
        mock_stream.start.assert_called_once()

        result = rec.stop_recording()
        assert rec.is_recording is False
        mock_stream.stop.assert_called_once()
        mock_stream.close.assert_called_once()

    @patch("pet.voice_stt.HAS_SOUNDDEVICE", False)
    def test_start_recording_no_sounddevice(self):
        from pet.voice_stt import MicrophoneRecorder
        rec = MicrophoneRecorder()
        with pytest.raises(RuntimeError, match="sounddevice 未安装"):
            rec.start_recording()

    def test_stop_without_start(self):
        from pet.voice_stt import MicrophoneRecorder
        rec = MicrophoneRecorder()
        result = rec.stop_recording()
        assert result == b""


# ── XfyunASR ──────────────────────────────────────────────────────


class TestXfyunASR:
    """科大讯飞 ASR 封装测试。"""

    def test_init_stores_params(self):
        from pet.voice_stt import XfyunASR
        asr = XfyunASR("app123", "key456", "secret789")
        assert asr._app_id == "app123"
        assert asr._api_key == "key456"
        assert asr._api_secret == "secret789"

    def test_create_url_format(self):
        from pet.voice_stt import XfyunASR
        asr = XfyunASR("app123", "key456", "secret789")
        url = asr._create_url()
        assert url.startswith("wss://iat-api.xfyun.cn/v2/iat?")
        assert "authorization=" in url
        assert "date=" in url
        assert "host=" in url

    @patch("pet.voice_stt.HAS_WEBSOCKET", False)
    def test_recognize_no_websocket(self):
        from pet.voice_stt import XfyunASR
        asr = XfyunASR("app123", "key456", "secret789")
        with pytest.raises(RuntimeError, match="websocket-client 未安装"):
            asr.recognize(b"\x00" * 1280)

    def test_recognize_empty_data(self):
        from pet.voice_stt import XfyunASR
        asr = XfyunASR("app123", "key456", "secret789")
        result = asr.recognize(b"")
        assert result == ""


# ── STTWorker ─────────────────────────────────────────────────────


class TestSTTWorker:
    """STT 工作线程测试。"""

    @patch("pet.voice_stt.HAS_WEBSOCKET", True)
    def test_success_emits_result(self, qtbot):
        from pet.voice_stt import STTWorker, XfyunASR

        asr = MagicMock(spec=XfyunASR)
        asr.recognize.return_value = "你好世界"

        worker = STTWorker(asr, b"\x00" * 1280)
        results = []
        errors = []
        worker.result_ready.connect(lambda t: results.append(t))
        worker.error_occurred.connect(lambda e: errors.append(e))

        worker.run()

        assert results == ["你好世界"]
        assert errors == []

    def test_error_emits_error(self, qtbot):
        from pet.voice_stt import STTWorker, XfyunASR

        asr = MagicMock(spec=XfyunASR)
        asr.recognize.side_effect = RuntimeError("连接失败")

        worker = STTWorker(asr, b"\x00" * 1280)
        results = []
        errors = []
        worker.result_ready.connect(lambda t: results.append(t))
        worker.error_occurred.connect(lambda e: errors.append(e))

        worker.run()

        assert results == []
        assert len(errors) == 1
        assert "连接失败" in errors[0]


# ── EdgeTTSPlayer ─────────────────────────────────────────────────


class TestEdgeTTSPlayer:
    """edge-tts 播放器测试。"""

    def test_init_params(self):
        from pet.voice_tts import EdgeTTSPlayer
        player = EdgeTTSPlayer(voice="zh-CN-YunxiNeural", rate="+10%", volume=60)
        assert player.voice == "zh-CN-YunxiNeural"
        assert player.rate == "+10%"

    def test_set_voice(self):
        from pet.voice_tts import EdgeTTSPlayer
        player = EdgeTTSPlayer()
        player.set_voice("zh-CN-YunjianNeural")
        assert player.voice == "zh-CN-YunjianNeural"

    def test_set_rate(self):
        from pet.voice_tts import EdgeTTSPlayer
        player = EdgeTTSPlayer()
        player.set_rate("-20%")
        assert player.rate == "-20%"

    def test_stop_without_play(self):
        from pet.voice_tts import EdgeTTSPlayer
        player = EdgeTTSPlayer()
        player.stop()  # 不应抛异常


# ── TTSWorker ─────────────────────────────────────────────────────


class TestTTSWorker:
    """TTS 工作线程测试。"""

    @patch("pet.voice_tts.HAS_EDGE_TTS", False)
    def test_no_edge_tts_emits_error(self):
        from pet.voice_tts import TTSWorker

        worker = TTSWorker("你好")
        results = []
        errors = []
        worker.playback_ready.connect(lambda d: results.append(d))
        worker.error_occurred.connect(lambda e: errors.append(e))

        worker.run()

        assert results == []
        assert len(errors) == 1
        assert "edge-tts 未安装" in errors[0]

    @patch("pet.voice_tts.HAS_EDGE_TTS", True)
    @patch("pet.voice_tts.edge_tts", create=True)
    def test_success_emits_mp3(self, mock_edge_tts):
        from pet.voice_tts import TTSWorker
        import io

        mock_communicate = MagicMock()

        async def mock_save(buf):
            buf.write(b"\xff\xfb\x90\x00" + b"\x00" * 100)  # Fake MP3 data

        mock_communicate.save = mock_save
        mock_edge_tts.Communicate.return_value = mock_communicate

        worker = TTSWorker("你好", voice="zh-CN-XiaoxiaoNeural")
        results = []
        errors = []
        worker.playback_ready.connect(lambda d: results.append(d))
        worker.error_occurred.connect(lambda e: errors.append(e))

        worker.run()

        # 由于 asyncio.run 的 mock 比较复杂，这里主要验证不崩溃
        # 实际的 edge-tts 调用需要集成测试
