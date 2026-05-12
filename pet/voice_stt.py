"""语音识别模块：麦克风录音 + 科大讯飞 IAT 语音听写"""
import base64
import datetime
import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import numpy as np

try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False

try:
    import websocket
    HAS_WEBSOCKET = True
except ImportError:
    HAS_WEBSOCKET = False

from PySide6.QtCore import QThread, Signal


class MicrophoneRecorder:
    """麦克风录音器，输出 16kHz/16bit/mono PCM 数据。"""

    def __init__(self, samplerate: int = 16000, channels: int = 1):
        self._samplerate = samplerate
        self._channels = channels
        self._stream = None
        self._frames: list[np.ndarray] = []
        self._recording = False

    @property
    def is_recording(self) -> bool:
        return self._recording

    def start_recording(self) -> None:
        """开始录音。"""
        if not HAS_SOUNDDEVICE:
            raise RuntimeError("sounddevice 未安装，无法录音")
        if self._recording:
            return
        self._frames = []
        self._recording = True

        def callback(indata, frames, time_info, status):
            if self._recording:
                self._frames.append(indata.copy())

        self._stream = sd.InputStream(
            samplerate=self._samplerate,
            channels=self._channels,
            dtype="int16",
            blocksize=640,  # 对齐讯飞 1280 bytes/帧 (640 samples * 2 bytes)
            callback=callback,
        )
        self._stream.start()

    def stop_recording(self) -> bytes:
        """停止录音，返回 PCM bytes (16kHz/16bit/mono)。"""
        if not self._recording:
            return b""
        self._recording = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        if not self._frames:
            return b""
        audio = np.concatenate(self._frames, axis=0)
        return audio.tobytes()


class XfyunASR:
    """科大讯飞语音听写 (IAT) 封装。

    需要在 xfyun.cn 注册并创建语音听写应用获取凭据。
    """

    HOST = "iat-api.xfyun.cn"
    PATH = "/v2/iat"

    def __init__(self, app_id: str, api_key: str, api_secret: str):
        self._app_id = app_id
        self._api_key = api_key
        self._api_secret = api_secret

    def _create_url(self) -> str:
        """生成带 HMAC-SHA256 签名的 WebSocket URL。"""
        now = datetime.datetime.now(datetime.timezone.utc)
        date = now.strftime("%a, %d %b %Y %H:%M:%S GMT")

        signature_origin = (
            f"host: {self.HOST}\n"
            f"date: {date}\n"
            f"GET {self.PATH} HTTP/1.1"
        )
        signature_sha = hmac.new(
            self._api_secret.encode("utf-8"),
            signature_origin.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        signature = base64.b64encode(signature_sha).decode("utf-8")

        authorization_origin = (
            f'api_key="{self._api_key}", '
            f'algorithm="hmac-sha256", '
            f'headers="host date request-line", '
            f'signature="{signature}"'
        )
        authorization = base64.b64encode(
            authorization_origin.encode("utf-8")
        ).decode("utf-8")

        params = {
            "authorization": authorization,
            "date": date,
            "host": self.HOST,
        }
        return f"wss://{self.HOST}{self.PATH}?{urlencode(params)}"

    def recognize(self, pcm_data: bytes) -> str:
        """同步识别 PCM 音频数据，返回识别文本。

        Args:
            pcm_data: 16kHz/16bit/mono PCM 原始数据
        """
        if not HAS_WEBSOCKET:
            raise RuntimeError("websocket-client 未安装")
        if not pcm_data:
            return ""

        url = self._create_url()
        ws = websocket.create_connection(url, timeout=15)
        result_parts = []

        try:
            # 第一帧：参数 + 业务配置
            first_frame = {
                "common": {"app_id": self._app_id},
                "business": {
                    "language": "zh_cn",
                    "domain": "iat",
                    "accent": "mandarin",
                    "vad_eos": 3000,
                    "dwa": "wpgs",
                },
                "data": {
                    "status": 0,
                    "format": "audio/L16;rate=16000",
                    "encoding": "raw",
                    "audio": "",
                },
            }
            ws.send(json.dumps(first_frame))

            # 中间帧：音频数据，每帧 1280 bytes
            chunk_size = 1280
            for i in range(0, len(pcm_data), chunk_size):
                chunk = pcm_data[i : i + chunk_size]
                frame = {
                    "data": {
                        "status": 1,
                        "format": "audio/L16;rate=16000",
                        "encoding": "raw",
                        "audio": base64.b64encode(chunk).decode(),
                    }
                }
                ws.send(json.dumps(frame))
                time.sleep(0.04)

            # 最后一帧：结束
            ws.send(json.dumps({"data": {"status": 2, "audio": ""}}))

            # 接收识别结果
            while True:
                res = json.loads(ws.recv())
                code = res.get("code")
                if code != 0:
                    raise RuntimeError(
                        f"讯飞 API 错误: code={code}, message={res.get('message', '')}"
                    )
                data = res.get("data", {}).get("result", {})
                for ws_item in data.get("ws", []):
                    for cw in ws_item.get("cw", []):
                        result_parts.append(cw.get("w", ""))
                if res.get("data", {}).get("status") == 2:
                    break
        finally:
            ws.close()

        return "".join(result_parts)


class STTWorker(QThread):
    """在工作线程中执行语音识别。"""

    result_ready = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, asr: XfyunASR, pcm_data: bytes, parent=None):
        super().__init__(parent)
        self._asr = asr
        self._pcm_data = pcm_data

    def run(self):
        try:
            text = self._asr.recognize(self._pcm_data)
            self.result_ready.emit(text)
        except Exception as e:
            self.error_occurred.emit(str(e))
