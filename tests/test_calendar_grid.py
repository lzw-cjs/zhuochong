"""CalendarGrid 单元测试"""
import pytest
from datetime import date
from unittest.mock import patch


class TestCalendarGrid:
    """月历网格测试"""

    def test_init(self, qtbot):
        from pet.calendar_grid import CalendarGrid

        grid = CalendarGrid()
        assert grid._year == date.today().year
        assert grid._month == date.today().month

    def test_set_event_dates(self, qtbot):
        from pet.calendar_grid import CalendarGrid

        grid = CalendarGrid()
        dates = {"2026-05-01", "2026-05-15"}
        grid.set_event_dates(dates)

        assert grid._event_dates == dates

    def test_prev_month(self, qtbot):
        from pet.calendar_grid import CalendarGrid

        grid = CalendarGrid()
        original_month = grid._month
        original_year = grid._year

        grid._prev_month()

        if original_month == 1:
            assert grid._month == 12
            assert grid._year == original_year - 1
        else:
            assert grid._month == original_month - 1
            assert grid._year == original_year

    def test_next_month(self, qtbot):
        from pet.calendar_grid import CalendarGrid

        grid = CalendarGrid()
        original_month = grid._month
        original_year = grid._year

        grid._next_month()

        if original_month == 12:
            assert grid._month == 1
            assert grid._year == original_year + 1
        else:
            assert grid._month == original_month + 1
            assert grid._year == original_year

    def test_prev_month_january(self, qtbot):
        from pet.calendar_grid import CalendarGrid

        grid = CalendarGrid()
        grid._month = 1
        grid._year = 2026

        grid._prev_month()

        assert grid._month == 12
        assert grid._year == 2025

    def test_next_month_december(self, qtbot):
        from pet.calendar_grid import CalendarGrid

        grid = CalendarGrid()
        grid._month = 12
        grid._year = 2026

        grid._next_month()

        assert grid._month == 1
        assert grid._year == 2027

    def test_go_to_today(self, qtbot):
        from pet.calendar_grid import CalendarGrid

        grid = CalendarGrid()
        grid._month = 1
        grid._year = 2020

        grid.go_to_today()

        assert grid._year == date.today().year
        assert grid._month == date.today().month

    def test_date_clicked_signal(self, qtbot):
        from pet.calendar_grid import CalendarGrid

        grid = CalendarGrid()
        clicked_dates = []
        grid.date_clicked.connect(lambda d: clicked_dates.append(d))

        # 模拟点击
        grid.date_clicked.emit("2026-05-14")

        assert clicked_dates == ["2026-05-14"]

    def test_month_label_text(self, qtbot):
        from pet.calendar_grid import CalendarGrid

        grid = CalendarGrid()
        grid._year = 2026
        grid._month = 5
        grid._refresh()

        assert grid._month_label.text() == "2026年5月"

    def test_refresh_creates_widgets(self, qtbot):
        from pet.calendar_grid import CalendarGrid

        grid = CalendarGrid()
        grid._refresh()

        # 应该有日期标签
        assert grid._grid.count() > 0

    def test_multiple_refresh(self, qtbot):
        from pet.calendar_grid import CalendarGrid

        grid = CalendarGrid()
        grid._refresh()
        count1 = grid._grid.count()

        grid._month = 6
        grid._refresh()
        count2 = grid._grid.count()

        # 不同月份可能有不同的日期数
        assert count1 > 0
        assert count2 > 0
