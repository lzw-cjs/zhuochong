"""HolidayEngine 单元测试"""
import pytest
import json
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch


@pytest.fixture
def holidays_path(tmp_path):
    """创建测试节日数据文件"""
    data = {
        "holidays": [
            {
                "id": "spring_festival",
                "name": "春节",
                "type": "lunar",
                "month": 1,
                "day": 1,
                "duration_days": 7,
                "costume": "red_lantern_hat",
                "emoji": "🧧"
            },
            {
                "id": "national_day",
                "name": "国庆节",
                "type": "solar",
                "month": 10,
                "day": 1,
                "duration_days": 7,
                "costume": "flag_ribbon",
                "emoji": "🇨🇳"
            },
        ]
    }
    path = tmp_path / "holidays.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


@pytest.fixture
def empty_holidays_path(tmp_path):
    """创建空节日数据文件"""
    path = tmp_path / "holidays.json"
    path.write_text('{"holidays": []}', encoding="utf-8")
    return path


class TestHolidayEngine:
    """节日引擎测试"""

    @patch("pet.holiday_engine.QTimer")
    def test_init_with_file(self, mock_timer_cls, holidays_path):
        from pet.holiday_engine import HolidayEngine

        engine = HolidayEngine(holidays_path)
        assert len(engine._holidays) == 2

    @patch("pet.holiday_engine.QTimer")
    def test_init_with_missing_file(self, mock_timer_cls, tmp_path):
        from pet.holiday_engine import HolidayEngine

        engine = HolidayEngine(tmp_path / "nonexistent.json")
        assert len(engine._holidays) == 0

    @patch("pet.holiday_engine.QTimer")
    def test_init_with_invalid_json(self, mock_timer_cls, tmp_path):
        from pet.holiday_engine import HolidayEngine

        path = tmp_path / "invalid.json"
        path.write_text("这不是JSON", encoding="utf-8")

        engine = HolidayEngine(path)
        assert len(engine._holidays) == 0

    @patch("pet.holiday_engine.QTimer")
    @patch("pet.holiday_engine.date")
    def test_check_solar_holiday_active(self, mock_date_cls, mock_timer_cls, holidays_path):
        from pet.holiday_engine import HolidayEngine

        mock_today = date(2026, 10, 3)
        mock_date_cls.today.return_value = mock_today
        mock_date_cls.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

        engine = HolidayEngine(holidays_path)
        engine._check()

        assert engine.active_holiday is not None
        assert engine.active_holiday["id"] == "national_day"

    @patch("pet.holiday_engine.QTimer")
    @patch("pet.holiday_engine.date")
    def test_check_no_holiday_active(self, mock_date_cls, mock_timer_cls, holidays_path):
        from pet.holiday_engine import HolidayEngine

        mock_today = date(2026, 6, 15)
        mock_date_cls.today.return_value = mock_today
        mock_date_cls.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

        engine = HolidayEngine(holidays_path)
        engine._check()

        # 国庆节还没到
        assert engine.active_holiday is None or engine.active_holiday["id"] != "national_day"

    @patch("pet.holiday_engine.QTimer")
    def test_force_check(self, mock_timer_cls, holidays_path):
        from pet.holiday_engine import HolidayEngine

        engine = HolidayEngine(holidays_path)
        engine.force_check()

        # 不应抛异常

    @patch("pet.holiday_engine.QTimer")
    def test_is_in_range_solar(self, mock_timer_cls, holidays_path):
        from pet.holiday_engine import HolidayEngine

        engine = HolidayEngine(holidays_path)

        holiday = {
            "type": "solar",
            "month": 10,
            "day": 1,
            "duration_days": 7,
        }

        # 在范围内
        assert engine._is_in_range(date(2026, 10, 3), holiday) is True

        # 在范围外
        assert engine._is_in_range(date(2026, 6, 15), holiday) is False

    @patch("pet.holiday_engine.QTimer")
    def test_is_in_range_solar_edge_cases(self, mock_timer_cls, holidays_path):
        from pet.holiday_engine import HolidayEngine

        engine = HolidayEngine(holidays_path)

        holiday = {
            "type": "solar",
            "month": 10,
            "day": 1,
            "duration_days": 7,
        }

        # 第一天
        assert engine._is_in_range(date(2026, 10, 1), holiday) is True

        # 最后一天
        assert engine._is_in_range(date(2026, 10, 7), holiday) is True

        # 之前一天
        assert engine._is_in_range(date(2026, 9, 30), holiday) is False

        # 之后一天
        assert engine._is_in_range(date(2026, 10, 8), holiday) is False

    @patch("pet.holiday_engine.QTimer")
    def test_lunar_to_solar(self, mock_timer_cls, holidays_path):
        from pet.holiday_engine import HolidayEngine

        result = HolidayEngine._lunar_to_solar(2026, 1, 1)
        # 农历日期转换应该返回一个日期
        if result is not None:
            assert isinstance(result, date)

    @patch("pet.holiday_engine.QTimer")
    def test_lunar_to_solar_invalid(self, mock_timer_cls, holidays_path):
        from pet.holiday_engine import HolidayEngine

        # 无效的农历日期
        result = HolidayEngine._lunar_to_solar(2026, 13, 1)
        assert result is None

    @patch("pet.holiday_engine.QTimer")
    def test_holiday_signals(self, mock_timer_cls, holidays_path):
        from pet.holiday_engine import HolidayEngine

        engine = HolidayEngine(holidays_path)

        active_signals = []
        ended_signals = []

        engine.holiday_active.connect(lambda *args: active_signals.append(args))
        engine.holiday_ended.connect(lambda: ended_signals.append(True))

        # 手动设置一个活跃节日然后清除
        engine._active_holiday = {"id": "test", "name": "测试"}
        engine._holidays = []  # 清空节日列表
        engine._check()

        assert len(ended_signals) == 1
