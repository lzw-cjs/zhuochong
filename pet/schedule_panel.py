"""日程面板：月历视图 + 事件列表 + 日历管理"""
import uuid
import json
import re
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem,
    QDialog, QLineEdit, QTextEdit, QComboBox,
    QDateTimeEdit, QFileDialog, QSplitter,
    QMessageBox, QApplication, QCheckBox, QMenu,
)
from PySide6.QtCore import Qt, Signal, QDateTime
from PySide6.QtGui import QColor

from data.event import Event
from data.schedule_store import ScheduleStore
from data.calendar_model import Calendar, CALENDAR_COLORS
from data.calendar_store import CalendarStore
from pet.calendar_grid import CalendarGrid


class EventDialog(QDialog):
    """新建/编辑事件对话框。"""

    def __init__(self, event: Event | None, calendars: list[Calendar], parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑事件" if event else "新建事件")
        self.setFixedSize(420, 560)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)

        self._event = event
        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        # 标题
        layout.addWidget(QLabel("标题:"))
        self._title = QLineEdit(event.title if event else "")
        layout.addWidget(self._title)

        # 事件时间
        layout.addWidget(QLabel("事件时间:"))
        self._dt = QDateTimeEdit()
        self._dt.setCalendarPopup(True)
        self._dt.setDisplayFormat("yyyy-MM-dd HH:mm")
        if event and event.datetime_str:
            try:
                dt = datetime.fromisoformat(event.datetime_str)
                self._dt.setDateTime(QDateTime(dt.year, dt.month, dt.day, dt.hour, dt.minute))
            except ValueError:
                self._dt.setDateTime(QDateTime.currentDateTime())
        else:
            self._dt.setDateTime(QDateTime.currentDateTime())
        layout.addWidget(self._dt)

        # 描述
        layout.addWidget(QLabel("描述:"))
        self._desc = QTextEdit()
        self._desc.setPlainText(event.description if event else "")
        self._desc.setMaximumHeight(50)
        layout.addWidget(self._desc)

        # 分类 + 优先级 同行
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("分类:"))
        self._category = QComboBox()
        self._category.addItems(["工作", "学习", "生活", "其他"])
        if event:
            idx = self._category.findText(event.category)
            if idx >= 0:
                self._category.setCurrentIndex(idx)
        row1.addWidget(self._category)
        row1.addWidget(QLabel("优先级:"))
        self._priority = QComboBox()
        self._priority.addItems(["低", "中", "高"])
        priority_map = {"low": 0, "medium": 1, "high": 2}
        self._priority.setCurrentIndex(priority_map.get(event.priority if event else "medium", 1))
        row1.addWidget(self._priority)
        layout.addLayout(row1)

        # 日历
        layout.addWidget(QLabel("日历:"))
        self._calendar = QComboBox()
        self._calendars = calendars
        for cal in calendars:
            self._calendar.addItem(cal.name, cal.id)
        if event:
            for i, cal in enumerate(calendars):
                if cal.id == event.calendar_id:
                    self._calendar.setCurrentIndex(i)
                    break
        layout.addWidget(self._calendar)

        # 提前提醒时间
        layout.addWidget(QLabel("提前提醒:"))
        self._reminder = QComboBox()
        reminder_options = [
            ("5 分钟", 5),
            ("15 分钟", 15),
            ("30 分钟", 30),
            ("1 小时", 60),
        ]
        for label, minutes in reminder_options:
            self._reminder.addItem(label, minutes)
        # Set current selection based on existing event
        if event:
            target = event.reminder_minutes
        else:
            target = 15  # default
        idx = next(
            (i for i, (_, m) in enumerate(reminder_options) if m == target),
            1,  # fallback to 15 min
        )
        self._reminder.setCurrentIndex(idx)
        layout.addWidget(self._reminder)

        # 规定完成时间
        layout.addWidget(QLabel("规定完成时间:"))
        self._has_deadline = QCheckBox("设置截止时间")
        self._has_deadline.setChecked(bool(event and event.deadline_str))
        layout.addWidget(self._has_deadline)

        self._deadline_dt = QDateTimeEdit()
        self._deadline_dt.setCalendarPopup(True)
        self._deadline_dt.setDisplayFormat("yyyy-MM-dd HH:mm")
        self._deadline_dt.setEnabled(bool(event and event.deadline_str))
        if event and event.deadline_str:
            try:
                dt = datetime.fromisoformat(event.deadline_str)
                self._deadline_dt.setDateTime(QDateTime(dt.year, dt.month, dt.day, dt.hour, dt.minute))
            except ValueError:
                self._deadline_dt.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        else:
            self._deadline_dt.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self._has_deadline.toggled.connect(self._deadline_dt.setEnabled)
        layout.addWidget(self._deadline_dt)

        # 按钮
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def get_event(self) -> Event:
        priority_map = {0: "low", 1: "medium", 2: "high"}
        dt = self._dt.dateTime().toPython()
        deadline_str = ""
        if self._has_deadline.isChecked():
            deadline_str = self._deadline_dt.dateTime().toPython().isoformat()
        return Event(
            title=self._title.text(),
            datetime_str=dt.isoformat(),
            description=self._desc.toPlainText(),
            category=self._category.currentText(),
            priority=priority_map[self._priority.currentIndex()],
            calendar_id=self._calendar.currentData(),
            reminder_minutes=self._reminder.currentData(),
            deadline_str=deadline_str,
            id=self._event.id if self._event else uuid.uuid4().hex[:12],
        )


class PasteImportDialog(QDialog):
    """粘贴导入对话框。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("粘贴导入")
        self.setMinimumSize(420, 320)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)

        layout = QVBoxLayout(self)

        label = QLabel("请粘贴日程内容（支持 JSON、纯文本、Markdown 格式）:")
        layout.addWidget(label)

        self._text_edit = QTextEdit()
        self._text_edit.setPlaceholderText("在此粘贴内容...")
        layout.addWidget(self._text_edit)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定导入")
        cancel_btn = QPushButton("取消")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def get_text(self) -> str:
        return self._text_edit.toPlainText()


class SchedulePanel(QWidget):
    """日程面板窗口。"""

    mark_completed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("日程管理")
        self.setFixedSize(660, 540)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)

        self._store = ScheduleStore()
        self._cal_store = CalendarStore()
        self._selected_date: str = ""

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # === 左侧：月历 + 日历列表 ===
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        self._cal_grid = CalendarGrid()
        self._cal_grid.date_clicked.connect(self._on_date_clicked)
        left_layout.addWidget(self._cal_grid)

        # 日历列表 + 添加/删除按钮
        left_layout.addWidget(QLabel("日历"))
        self._cal_list = QListWidget()
        self._cal_list.setMaximumHeight(100)
        left_layout.addWidget(self._cal_list)

        cal_btn_row = QHBoxLayout()
        add_cal_btn = QPushButton("+ 添加")
        add_cal_btn.setFixedWidth(60)
        add_cal_btn.clicked.connect(self._add_calendar)
        del_cal_btn = QPushButton("- 删除")
        del_cal_btn.setFixedWidth(60)
        del_cal_btn.clicked.connect(self._delete_calendar)
        cal_btn_row.addWidget(add_cal_btn)
        cal_btn_row.addWidget(del_cal_btn)
        cal_btn_row.addStretch()
        left_layout.addLayout(cal_btn_row)

        splitter.addWidget(left)

        # === 右侧：事件列表 + 按钮 ===
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)

        self._date_label = QLabel("所有事件")
        self._date_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        right_layout.addWidget(self._date_label)

        self._event_list = QListWidget()
        self._event_list.itemDoubleClicked.connect(self._on_event_double_click)
        self._event_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._event_list.customContextMenuRequested.connect(self._on_event_context_menu)
        right_layout.addWidget(self._event_list, 1)

        # 操作按钮行
        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        add_btn = QPushButton("新建事件")
        add_btn.clicked.connect(self._add_event)
        complete_btn = QPushButton("标记完成")
        complete_btn.clicked.connect(self._complete_event)
        del_btn = QPushButton("删除事件")
        del_btn.clicked.connect(self._delete_event)
        action_row.addWidget(add_btn)
        action_row.addWidget(complete_btn)
        action_row.addWidget(del_btn)
        right_layout.addLayout(action_row)

        # 导入导出按钮行
        io_row = QHBoxLayout()
        io_row.setSpacing(8)
        export_btn = QPushButton("导出 Markdown")
        export_btn.clicked.connect(self._export_markdown)
        import_btn = QPushButton("导入文件")
        import_btn.clicked.connect(self._import)
        paste_btn = QPushButton("粘贴导入")
        paste_btn.clicked.connect(self._import_from_clipboard)
        io_row.addStretch()
        io_row.addWidget(export_btn)
        io_row.addWidget(import_btn)
        io_row.addWidget(paste_btn)
        right_layout.addLayout(io_row)

        splitter.addWidget(right)
        layout.addWidget(splitter)

        self._refresh()

    def _refresh(self):
        self._cal_list.clear()
        for cal in self._cal_store.get_all():
            item = QListWidgetItem(cal.name)
            item.setData(Qt.ItemDataRole.UserRole, cal.id)
            item.setCheckState(Qt.CheckState.Checked)
            item.setForeground(QColor(cal.color))
            self._cal_list.addItem(item)

        all_events = self._store.get_all()
        event_dates = {e.datetime_str[:10] for e in all_events if e.datetime_str}
        self._cal_grid.set_event_dates(event_dates)
        self._refresh_events()

    def _refresh_events(self):
        self._event_list.clear()
        events = self._store.get_all()

        if self._selected_date:
            events = [e for e in events if e.datetime_str and e.datetime_str[:10] == self._selected_date]
            self._date_label.setText(f"📅 {self._selected_date}")
        else:
            self._date_label.setText("所有事件")

        events.sort(key=lambda e: e.datetime_str)
        for ev in events:
            dt_str = ev.datetime_str[:16].replace("T", " ")
            p_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(ev.priority, "⚪")
            s_icon = {"completed": "✅", "overdue": "⏰"}.get(ev.status, "")
            dl = ""
            if ev.deadline_str and ev.status == "pending":
                dl = f" [截止: {ev.deadline_str[:16].replace('T', ' ')}]"
            text = f"{s_icon}{p_icon} [{ev.category}] {ev.title}  ({dt_str}){dl}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, ev.id)
            if ev.status == "completed":
                item.setForeground(QColor("#999"))
            elif ev.status == "overdue":
                item.setForeground(QColor("#D94A4A"))
            self._event_list.addItem(item)

    def _on_date_clicked(self, date_str: str):
        self._selected_date = "" if self._selected_date == date_str else date_str
        self._refresh_events()

    def _on_event_double_click(self, item: QListWidgetItem):
        self._edit_event(item)

    def _on_event_context_menu(self, pos):
        """右键菜单。"""
        item = self._event_list.itemAt(pos)
        if not item:
            return

        menu = QMenu(self)
        edit_action = menu.addAction("编辑本事件")
        complete_action = menu.addAction("标记完成")
        uncomplete_action = menu.addAction("取消标记完成")
        delete_action = menu.addAction("删除事件")

        action = menu.exec_(self._event_list.mapToGlobal(pos))

        if action == edit_action:
            self._edit_event(item)
        elif action == complete_action:
            self._complete_event()
        elif action == uncomplete_action:
            self._uncomplete_event()
        elif action == delete_action:
            self._delete_event()

    def _edit_event(self, item: QListWidgetItem):
        """编辑事件。"""
        event_id = item.data(Qt.ItemDataRole.UserRole)
        ev = self._store.get_by_id(event_id)
        if not ev:
            return
        calendars = self._cal_store.get_all()
        dlg = EventDialog(ev, calendars, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._store.update(dlg.get_event())
            self._refresh()

    def _add_event(self):
        calendars = self._cal_store.get_all()
        dlg = EventDialog(None, calendars, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._store.add(dlg.get_event())
            self._refresh()

    def _delete_event(self):
        item = self._event_list.currentItem()
        if not item:
            return
        event_id = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self, "确认删除", "确定要删除这个事件吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._store.delete(event_id)
            self._refresh()

    def _complete_event(self):
        item = self._event_list.currentItem()
        if not item:
            return
        event_id = item.data(Qt.ItemDataRole.UserRole)
        self.mark_completed.emit(event_id)
        self._refresh()

    def _uncomplete_event(self):
        """取消标记完成。"""
        item = self._event_list.currentItem()
        if not item:
            return
        event_id = item.data(Qt.ItemDataRole.UserRole)
        ev = self._store.get_by_id(event_id)
        if not ev:
            return
        ev.status = "pending"
        ev.completed = False
        ev.completed_at = ""
        self._store.update(ev)
        self._refresh()

    def _add_calendar(self):
        colors = list(CALENDAR_COLORS.values())
        idx = len(self._cal_store.get_all()) % len(colors)
        cal = Calendar(name="新日历", color=colors[idx])
        self._cal_store.add(cal)
        self._refresh()

    def _delete_calendar(self):
        item = self._cal_list.currentItem()
        if not item:
            return
        cal_id = item.data(Qt.ItemDataRole.UserRole)
        if cal_id == "default":
            QMessageBox.warning(self, "提示", "默认日历不能删除")
            return
        reply = QMessageBox.question(
            self, "确认删除", f"确定要删除日历「{item.text()}」吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._cal_store.delete(cal_id)
            self._refresh()

    def _export_markdown(self):
        """导出为 Markdown 格式。"""
        path, _ = QFileDialog.getSaveFileName(self, "导出日程", "schedule.md", "Markdown (*.md)")
        if not path:
            return
        events = self._store.get_all()
        events.sort(key=lambda e: e.datetime_str)

        lines = ["# 日程导出\n"]
        for ev in events:
            dt_str = ev.datetime_str[:16].replace("T", " ")
            status = "✅" if ev.status == "completed" else "⏰" if ev.status == "overdue" else "⬜"
            priority = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(ev.priority, "⚪")
            line = f"- {status}{priority} **{ev.title}** ({dt_str})"
            if ev.deadline_str:
                line += f" [截止: {ev.deadline_str[:16].replace('T', ' ')}]"
            if ev.description:
                line += f"\n  {ev.description}"
            lines.append(line)

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        QMessageBox.information(self, "导出成功", f"已导出到 {path}")

    def _import(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "导入日程", "",
            "Markdown (*.md);;所有支持格式 (*.json *.txt *.md);;JSON (*.json);;文本 (*.txt)"
        )
        if not path:
            return
        if path.endswith(".json"):
            count = self._store.import_json(path)
        else:
            count = self._import_text_file(path)
        self._refresh()
        QMessageBox.information(self, "导入成功", f"导入了 {count} 条新事件")

    def _import_text_file(self, path: str) -> int:
        """从纯文本/Markdown 文件提取事件。"""
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        events = self._extract_events_from_text(text)
        if not events:
            return 0
        existing = self._store._load_events()
        existing_ids = {e.get("id") for e in existing}
        new_events = [e for e in events if e.get("id") not in existing_ids]
        existing.extend(new_events)
        self._store._save_events(existing)
        return len(new_events)

    def _extract_events_from_text(self, text: str) -> list[dict]:
        """从文本中自动提取事件。

        支持格式：
        - "YYYY-MM-DD HH:MM 标题"
        - "YYYY/MM/DD HH:MM 标题"
        - "MM月DD日 标题"
        - "- [ ] 标题 (日期)" (Markdown todo)
        """
        events = []
        now = datetime.now()
        year = now.year

        # 模式1: 2026-05-10 14:00 开会
        for m in re.finditer(r'(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{2})\s+(.+)', text):
            y, mo, d, h, mi, title = m.groups()
            title = title.strip().split('\n')[0]
            dt_str = f"{y}-{int(mo):02d}-{int(d):02d}T{int(h):02d}:{mi}:00"
            events.append(self._make_event_dict(title, dt_str))

        # 模式2: 2026/5/10 14:00 开会
        for m in re.finditer(r'(\d{4})/(\d{1,2})/(\d{1,2})\s+(\d{1,2}):(\d{2})\s+(.+)', text):
            y, mo, d, h, mi, title = m.groups()
            title = title.strip().split('\n')[0]
            dt_str = f"{y}-{int(mo):02d}-{int(d):02d}T{int(h):02d}:{mi}:00"
            events.append(self._make_event_dict(title, dt_str))

        # 模式3: 5月10日 开会 / 5月10号 开会
        for m in re.finditer(r'(\d{1,2})月(\d{1,2})[日号]\s*(.+)', text):
            mo, d, title = m.groups()
            title = title.strip().split('\n')[0]
            if len(title) > 50:
                title = title[:50]
            dt_str = f"{year}-{int(mo):02d}-{int(d):02d}T09:00:00"
            events.append(self._make_event_dict(title, dt_str))

        # 模式4: - [ ] 待办事项 (2026-05-10)
        for m in re.finditer(r'-\s*\[[ x]\]\s+(.+?)(?:\((\d{4}-\d{2}-\d{2})\))?$', text, re.MULTILINE):
            title, date_str = m.groups()
            title = title.strip()
            if date_str:
                dt_str = f"{date_str}T09:00:00"
            else:
                dt_str = now.isoformat()
            events.append(self._make_event_dict(title, dt_str))

        return events

    def _make_event_dict(self, title: str, dt_str: str) -> dict:
        return {
            "title": title,
            "datetime_str": dt_str,
            "description": "",
            "category": "其他",
            "priority": "medium",
            "calendar_id": "default",
            "reminder_minutes": 15,
            "deadline_str": "",
            "completed": False,
            "completed_at": "",
            "status": "pending",
            "id": uuid.uuid4().hex[:12],
        }

    def _import_from_clipboard(self):
        dlg = PasteImportDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        text = dlg.get_text().strip()
        if not text:
            QMessageBox.warning(self, "粘贴导入", "内容为空")
            return

        # 先尝试 JSON
        try:
            data = json.loads(text)
            if isinstance(data, list):
                events_data = data
            elif isinstance(data, dict) and "events" in data:
                events_data = data["events"]
            else:
                events_data = None
            if events_data:
                existing = self._store._load_events()
                existing_ids = {e.get("id") for e in existing}
                new_events = [e for e in events_data if e.get("id") not in existing_ids]
                if new_events:
                    existing.extend(new_events)
                    self._store._save_events(existing)
                    self._refresh()
                    QMessageBox.information(self, "粘贴导入", f"导入了 {len(new_events)} 条新事件")
                else:
                    QMessageBox.information(self, "粘贴导入", "没有新事件可导入")
                return
        except json.JSONDecodeError:
            pass

        # 非 JSON，尝试从文本提取事件
        events = self._extract_events_from_text(text)
        if not events:
            QMessageBox.warning(self, "粘贴导入", "未能从文本中提取到事件")
            return
        existing = self._store._load_events()
        existing.extend(events)
        self._store._save_events(existing)
        self._refresh()
        QMessageBox.information(self, "粘贴导入", f"从文本中提取了 {len(events)} 条事件")

    def closeEvent(self, event):
        event.ignore()
        self.hide()
