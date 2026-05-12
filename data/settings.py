"""应用设置的读写与持久化"""
from dataclasses import dataclass, field, asdict
from data.store import JsonStore, register_migration

SCHEMA_VERSION = 2

DEFAULT_SETTINGS = {
    "_schema_version": SCHEMA_VERSION,
    "pet": {
        "x": 200,
        "y": 200,
        "state": "idle"
    },
    "preferences": {
        "volume": 50,
        "muted": False,
        "auto_start": False,
        "costume_enabled": True
    },
    "llm": {
        "protocol": "",
        "base_url": "",
        "api_key": "",
        "model": "",
        "system_prompt": "",
        "max_history": 50,
    },
    "voice": {
        "enabled": True,
        "auto_play": True,
        "stt_provider": "",
        "xfyun_app_id": "",
        "xfyun_api_key": "",
        "xfyun_api_secret": "",
        "tts_voice": "zh-CN-XiaoxiaoNeural",
        "tts_rate": "+0%",
        "tts_volume": 80,
    },
}


@dataclass
class Settings:
    """应用设置数据模型。

    字段说明：
        pet_x / pet_y: 宠物在屏幕上的像素坐标
        pet_state: 当前动画状态（idle/walk/sleep/happy）
        volume: 音量 0-100
        muted: 是否静音
        auto_start: 是否开机自启
    """
    pet_x: int = 200
    pet_y: int = 200
    pet_state: str = "idle"
    pet_scale: float = 1.0    # 显示缩放倍数 0.5~3.0
    volume: int = 50
    muted: bool = False
    auto_start: bool = False
    costume_enabled: bool = True
    # LLM 配置
    llm_protocol: str = ""      # "", "openai", "anthropic"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_system_prompt: str = ""  # 空 = 使用默认水獭人格
    llm_max_history: int = 50
    # 语音设置
    voice_enabled: bool = True           # 总开关
    voice_auto_play: bool = True         # 回复自动播放
    voice_stt_provider: str = ""         # "", "xfyun"
    voice_xfyun_app_id: str = ""
    voice_xfyun_api_key: str = ""
    voice_xfyun_api_secret: str = ""
    voice_tts_voice: str = "zh-CN-XiaoxiaoNeural"  # edge-tts 音色
    voice_tts_rate: str = "+0%"          # 语速
    voice_tts_volume: int = 80           # 音量 0-100

    def save(self) -> None:
        """将设置保存到 JSON 文件。"""
        store = JsonStore("settings.json")
        data = {
            "_schema_version": SCHEMA_VERSION,
            "pet": {
                "x": self.pet_x,
                "y": self.pet_y,
                "state": self.pet_state,
                "scale": self.pet_scale,
            },
            "preferences": {
                "volume": self.volume,
                "muted": self.muted,
                "auto_start": self.auto_start,
                "costume_enabled": self.costume_enabled,
            },
            "llm": {
                "protocol": self.llm_protocol,
                "base_url": self.llm_base_url,
                "api_key": self.llm_api_key,
                "model": self.llm_model,
                "system_prompt": self.llm_system_prompt,
                "max_history": self.llm_max_history,
            },
            "voice": {
                "enabled": self.voice_enabled,
                "auto_play": self.voice_auto_play,
                "stt_provider": self.voice_stt_provider,
                "xfyun_app_id": self.voice_xfyun_app_id,
                "xfyun_api_key": self.voice_xfyun_api_key,
                "xfyun_api_secret": self.voice_xfyun_api_secret,
                "tts_voice": self.voice_tts_voice,
                "tts_rate": self.voice_tts_rate,
                "tts_volume": self.voice_tts_volume,
            },
        }
        store.save(data)

    @classmethod
    def load(cls) -> "Settings":
        """从 JSON 文件加载设置。文件不存在或格式错误时返回默认值。"""
        store = JsonStore("settings.json")
        data = store.load(default=DEFAULT_SETTINGS)

        try:
            pet = data.get("pet", {})
            prefs = data.get("preferences", {})
            llm = data.get("llm", {})
            voice = data.get("voice", {})
            return cls(
                pet_x=pet.get("x", 200),
                pet_y=pet.get("y", 200),
                pet_state=pet.get("state", "idle"),
                pet_scale=pet.get("scale", 1.0),
                volume=prefs.get("volume", 50),
                muted=prefs.get("muted", False),
                auto_start=prefs.get("auto_start", False),
                costume_enabled=prefs.get("costume_enabled", True),
                llm_protocol=llm.get("protocol", ""),
                llm_base_url=llm.get("base_url", ""),
                llm_api_key=llm.get("api_key", ""),
                llm_model=llm.get("model", ""),
                llm_system_prompt=llm.get("system_prompt", ""),
                llm_max_history=llm.get("max_history", 50),
                voice_enabled=voice.get("enabled", True),
                voice_auto_play=voice.get("auto_play", True),
                voice_stt_provider=voice.get("stt_provider", ""),
                voice_xfyun_app_id=voice.get("xfyun_app_id", ""),
                voice_xfyun_api_key=voice.get("xfyun_api_key", ""),
                voice_xfyun_api_secret=voice.get("xfyun_api_secret", ""),
                voice_tts_voice=voice.get("tts_voice", "zh-CN-XiaoxiaoNeural"),
                voice_tts_rate=voice.get("tts_rate", "+0%"),
                voice_tts_volume=voice.get("tts_volume", 80),
            )
        except (KeyError, TypeError, ValueError):
            return cls()


@register_migration("settings", from_version=1)
def _migrate_v1_to_v2(data: dict) -> dict:
    """v1 → v2: 添加 costume_enabled 字段。"""
    prefs = data.get("preferences", {})
    if "costume_enabled" not in prefs:
        prefs["costume_enabled"] = True
    data["preferences"] = prefs
    return data
