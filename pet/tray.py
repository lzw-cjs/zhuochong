"""系统托盘图标与菜单"""
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction
from PySide6.QtCore import Qt, Signal


def create_placeholder_icon() -> QIcon:
    """生成 16x16 占位托盘图标（棕色圆形 + 黑色眼睛）。"""
    pixmap = QPixmap(16, 16)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 身体
    painter.setBrush(QColor(139, 90, 43))
    painter.setPen(QColor(139, 90, 43))
    painter.drawEllipse(2, 3, 12, 12)

    # 眼睛
    painter.setBrush(QColor(0, 0, 0))
    painter.drawEllipse(5, 6, 2, 2)
    painter.drawEllipse(9, 6, 2, 2)

    painter.end()
    return QIcon(pixmap)


class PetTrayIcon(QSystemTrayIcon):
    """系统托盘图标。

    功能：
    - 显示占位图标
    - 右键菜单：Show/Hide Pet, Exit
    - 双击切换宠物可见性
    """

    toggle_visibility = Signal()
    reminder_suppress = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        # 设置图标
        self.setIcon(create_placeholder_icon())
        self.setToolTip("智能桌面宠物")

        # 右键菜单
        self._menu = QMenu()

        self._toggle_action = QAction("隐藏宠物", self)
        self._toggle_action.triggered.connect(self.toggle_visibility.emit)

        self._reminder_action = QAction("关闭提醒", self)
        self._reminder_action.setCheckable(True)
        self._reminder_action.setChecked(False)
        self._reminder_action.triggered.connect(self._on_reminder_toggle)

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(QApplication.quit)

        self._menu.addAction(self._toggle_action)
        self._menu.addAction(self._reminder_action)
        self._menu.addSeparator()
        self._menu.addAction(exit_action)

        self.setContextMenu(self._menu)

        # 双击切换可见性
        self.activated.connect(self._on_activated)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.toggle_visibility.emit()

    def update_visibility_state(self, is_visible: bool) -> None:
        if is_visible:
            self._toggle_action.setText("隐藏宠物")
        else:
            self._toggle_action.setText("显示宠物")

    def _on_reminder_toggle(self, checked: bool) -> None:
        """切换提醒开关。checked=True 表示关闭提醒。"""
        if checked:
            self._reminder_action.setText("开启提醒")
            self.reminder_suppress.emit(True)
        else:
            self._reminder_action.setText("关闭提醒")
            self.reminder_suppress.emit(False)

    def update_reminder_suppressed(self, suppressed: bool) -> None:
        """更新提醒抑制状态（供外部调用同步状态）。"""
        self._reminder_action.setChecked(suppressed)
        self._reminder_action.setText("开启提醒" if suppressed else "关闭提醒")
