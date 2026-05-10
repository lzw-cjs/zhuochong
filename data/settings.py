"""应用设置的读写与持久化"""
from dataclasses import dataclass, field, asdict
from data.store import JsonStore

SCHEMA_VERSION = 1

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
        "auto_start": False
    }
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
    volume: int = 50
    muted: bool = False
    auto_start: bool = False

    def save(self) -> None:
        """将设置保存到 JSON 文件。"""
        store = JsonStore("settings.json")
        data = {
            "_schema_version": SCHEMA_VERSION,
            "pet": {
                "x": self.pet_x,
                "y": self.pet_y,
                "state": self.pet_state
            },
            "preferences": {
                "volume": self.volume,
                "muted": self.muted,
                "auto_start": self.auto_start
            }
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
            return cls(
                pet_x=pet.get("x", 200),
                pet_y=pet.get("y", 200),
                pet_state=pet.get("state", "idle"),
                volume=prefs.get("volume", 50),
                muted=prefs.get("muted", False),
                auto_start=prefs.get("auto_start", False),
            )
        except (KeyError, TypeError, ValueError):
            return cls()
