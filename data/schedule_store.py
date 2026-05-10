"""日程事件存储"""
import json
import os
import tempfile
from data.store import JsonStore
from data.event import Event

SCHEDULE_SCHEMA_VERSION = 1


class ScheduleStore:
    """事件 CRUD 操作。"""

    def __init__(self):
        self._store = JsonStore("events.json", store_name="events")

    def _load_events(self) -> list[dict]:
        data = self._store.load(default={"events": []}, current_version=SCHEDULE_SCHEMA_VERSION)
        return data.get("events", [])

    def _save_events(self, events: list[dict]) -> None:
        self._store.save({"_schema_version": SCHEDULE_SCHEMA_VERSION, "events": events})

    def add(self, event: Event) -> None:
        events = self._load_events()
        events.append(event.to_dict())
        self._save_events(events)

    def get_all(self) -> list[Event]:
        return [Event.from_dict(d) for d in self._load_events()]

    def get_by_id(self, event_id: str) -> Event | None:
        for e in self.get_all():
            if e.id == event_id:
                return e
        return None

    def update(self, event: Event) -> bool:
        events = self._load_events()
        for i, d in enumerate(events):
            if d.get("id") == event.id:
                events[i] = event.to_dict()
                self._save_events(events)
                return True
        return False

    def delete(self, event_id: str) -> bool:
        events = self._load_events()
        before = len(events)
        events = [d for d in events if d.get("id") != event_id]
        if len(events) < before:
            self._save_events(events)
            return True
        return False

    def export_json(self, filepath: str) -> None:
        """导出所有事件到 JSON 文件。"""
        data = {"events": self._load_events()}
        fd, tmp = tempfile.mkstemp(suffix=".json")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, filepath)
        except Exception:
            os.unlink(tmp)
            raise

    def import_json(self, filepath: str) -> int:
        """从 JSON 文件导入事件，返回导入数量。"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        imported = data.get("events", [])
        existing = self._load_events()
        existing_ids = {e.get("id") for e in existing}
        new_events = [e for e in imported if e.get("id") not in existing_ids]
        existing.extend(new_events)
        self._save_events(existing)
        return len(new_events)
