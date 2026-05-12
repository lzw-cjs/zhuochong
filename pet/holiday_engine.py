"""节日检测引擎：自动检测当前日期是否在节日期间，支持农历和公历。"""
import json
from datetime import date, timedelta
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Signal

from lunardate import LunarDate


class HolidayEngine(QObject):
    """检测当前日期是否在某个节日期间，每小时检查一次。"""

    holiday_active = Signal(str, str, str)  # holiday_id, costume_id, emoji
    holiday_ended = Signal()

    CHECK_INTERVAL_MS = 60 * 60 * 1000  # 1 小时

    def __init__(self, holidays_path: Path | str | None = None):
        super().__init__()
        self._holidays: list[dict] = []
        self._active_holiday: dict | None = None

        if holidays_path is None:
            holidays_path = Path(__file__).parent.parent / "data" / "holidays.json"
        self._load_holidays(holidays_path)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check)
        self._timer.start(self.CHECK_INTERVAL_MS)

        # 启动时立即检查一次
        self._check()

    def _load_holidays(self, path: Path | str) -> None:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            self._holidays = data.get("holidays", [])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[HolidayEngine] 加载节日数据失败: {e}")
            self._holidays = []

    def _check(self) -> None:
        today = date.today()
        matched = None

        for h in self._holidays:
            if self._is_in_range(today, h):
                matched = h
                break

        if matched:
            if self._active_holiday is None or self._active_holiday["id"] != matched["id"]:
                self._active_holiday = matched
                self.holiday_active.emit(
                    matched["id"],
                    matched["costume"],
                    matched["emoji"],
                )
                print(f"[HolidayEngine] 节日激活: {matched['name']} ({matched['emoji']})")
        else:
            if self._active_holiday is not None:
                print(f"[HolidayEngine] 节日结束: {self._active_holiday['name']}")
                self._active_holiday = None
                self.holiday_ended.emit()

    def _is_in_range(self, today: date, holiday: dict) -> bool:
        h_type = holiday.get("type", "solar")
        month = holiday.get("month", 1)
        day = holiday.get("day", 1)
        duration = holiday.get("duration_days", 1)

        if h_type == "lunar":
            start = self._lunar_to_solar(today.year, month, day)
            if start is None:
                return False
        else:
            start = date(today.year, month, day)

        end = start + timedelta(days=duration - 1)
        return start <= today <= end

    @staticmethod
    def _lunar_to_solar(year: int, lunar_month: int, lunar_day: int) -> date | None:
        """将农历日期转为公历日期。如果农历月日不存在则返回 None。"""
        try:
            lunar = LunarDate(year, lunar_month, lunar_day)
            return lunar.toSolarDate()
        except (ValueError, IndexError):
            return None

    @property
    def active_holiday(self) -> dict | None:
        return self._active_holiday

    def force_check(self) -> None:
        """手动触发一次检查（用于测试或设置变更后）。"""
        self._check()
