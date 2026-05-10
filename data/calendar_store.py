"""日历存储"""
from data.store import JsonStore
from data.calendar_model import Calendar

CALENDAR_SCHEMA_VERSION = 1

DEFAULT_CALENDAR = Calendar(id="default", name="默认", color="#8B5A2B")


class CalendarStore:
    """日历 CRUD 操作。"""

    def __init__(self):
        self._store = JsonStore("calendars.json", store_name="calendars")

    def _load(self) -> list[dict]:
        data = self._store.load(default={"calendars": [DEFAULT_CALENDAR.to_dict()]}, current_version=CALENDAR_SCHEMA_VERSION)
        cals = data.get("calendars", [])
        if not any(c.get("id") == "default" for c in cals):
            cals.insert(0, DEFAULT_CALENDAR.to_dict())
        return cals

    def _save(self, calendars: list[dict]) -> None:
        self._store.save({"_schema_version": CALENDAR_SCHEMA_VERSION, "calendars": calendars})

    def get_all(self) -> list[Calendar]:
        return [Calendar.from_dict(d) for d in self._load()]

    def add(self, cal: Calendar) -> None:
        cals = self._load()
        cals.append(cal.to_dict())
        self._save(cals)

    def delete(self, cal_id: str) -> bool:
        if cal_id == "default":
            return False
        cals = self._load()
        before = len(cals)
        cals = [d for d in cals if d.get("id") != cal_id]
        if len(cals) < before:
            self._save(cals)
            return True
        return False
