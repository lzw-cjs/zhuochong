"""月历网格组件：显示月视图，标记有事件的日期"""
import calendar
from datetime import date, datetime
from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QPushButton, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QColor, QFont


class CalendarGrid(QWidget):
    """月历网格。

    功能：
    - 显示一个月的日历，周一到周日
    - 前后月份导航
    - 有事件的日期高亮标记
    - 点击日期触发信号
    """

    date_clicked = Signal(str)  # 发射 ISO 格式日期字符串

    def __init__(self, parent=None):
        super().__init__(parent)
        self._today = date.today()
        self._year = self._today.year
        self._month = self._today.month
        self._event_dates: set[str] = set()  # "YYYY-MM-DD" 格式

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # 月份导航
        nav = QHBoxLayout()
        self._prev_btn = QPushButton("<")
        self._prev_btn.setFixedWidth(28)
        self._prev_btn.clicked.connect(self._prev_month)
        self._month_label = QLabel()
        self._month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._next_btn = QPushButton(">")
        self._next_btn.setFixedWidth(28)
        self._next_btn.clicked.connect(self._next_month)
        nav.addWidget(self._prev_btn)
        nav.addWidget(self._month_label, 1)
        nav.addWidget(self._next_btn)
        layout.addLayout(nav)

        # 星期头
        weekdays = ["一", "二", "三", "四", "五", "六", "日"]
        header = QHBoxLayout()
        header.setSpacing(0)
        for wd in weekdays:
            lbl = QLabel(wd)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("font-size: 11px; color: #888; padding: 2px;")
            header.addWidget(lbl)
        layout.addLayout(header)

        # 日期网格容器
        self._grid_widget = QWidget()
        self._grid = QGridLayout(self._grid_widget)
        self._grid.setSpacing(1)
        self._grid.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._grid_widget)

        self._refresh()

    def set_event_dates(self, dates: set[str]) -> None:
        """设置有事件的日期集合（"YYYY-MM-DD" 格式）。"""
        self._event_dates = dates
        self._refresh()

    def _refresh(self):
        """重绘日历网格。"""
        # 清空旧内容
        while self._grid.count():
            item = self._grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        self._month_label.setText(f"{self._year}年{self._month}月")

        cal = calendar.monthcalendar(self._year, self._month)
        for row, week in enumerate(cal):
            for col, day in enumerate(week):
                if day == 0:
                    lbl = QLabel("")
                    self._grid.addWidget(lbl, row, col)
                    continue

                date_str = f"{self._year}-{self._month:02d}-{day:02d}"
                is_today = (date_str == self._today.isoformat())
                has_event = date_str in self._event_dates

                lbl = QLabel(str(day))
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl.setFixedSize(32, 24)
                lbl.setCursor(Qt.CursorShape.PointingHandCursor)

                style_parts = ["font-size: 12px; padding: 2px; border-radius: 4px;"]

                if is_today:
                    style_parts.append("background-color: #8B5A2B; color: white; font-weight: bold;")
                elif has_event:
                    style_parts.append("background-color: #D4A574; color: #333; font-weight: bold;")
                else:
                    style_parts.append("color: #555;")

                lbl.setStyleSheet("".join(style_parts))

                # 用 lambda 捕获 date_str
                lbl.mousePressEvent=lambda e, d=date_str: self.date_clicked.emit(d)

                self._grid.addWidget(lbl, row, col)

    def _prev_month(self):
        self._month -= 1
        if self._month < 1:
            self._month = 12
            self._year -= 1
        self._refresh()

    def _next_month(self):
        self._month += 1
        if self._month > 12:
            self._month = 1
            self._year += 1
        self._refresh()

    def go_to_today(self):
        """跳转到今天的月份。"""
        self._today = date.today()
        self._year = self._today.year
        self._month = self._today.month
        self._refresh()
