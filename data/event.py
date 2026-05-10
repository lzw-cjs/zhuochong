"""日程事件数据模型"""
from dataclasses import dataclass, field, asdict
import uuid


@dataclass
class Event:
    """日程事件。"""
    title: str
    datetime_str: str  # ISO 8601 格式，事件开始时间
    description: str = ""
    category: str = "其他"  # 工作/学习/生活/其他
    priority: str = "medium"  # low/medium/high
    calendar_id: str = "default"
    reminder_minutes: int = 15
    deadline_str: str = ""  # 规定完成时间（ISO 8601），空表示无截止
    completed: bool = False
    completed_at: str = ""  # 实际完成时间（ISO 8601）
    status: str = "pending"  # pending / completed / overdue
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Event":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
