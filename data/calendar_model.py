"""日历数据模型"""
from dataclasses import dataclass, field, asdict
import uuid


@dataclass
class Calendar:
    """日历。"""
    name: str
    color: str = "#8B5A2B"
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Calendar":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


CALENDAR_COLORS = {
    "棕色": "#8B5A2B",
    "蓝色": "#4A90D9",
    "绿色": "#5BA55B",
    "红色": "#D94A4A",
    "紫色": "#8B5AD9",
}
