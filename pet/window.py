"""透明无边框宠物窗口"""
import ctypes
from ctypes import wintypes

from PySide6.QtWidgets import QWidget, QMenu, QApplication
from PySide6.QtCore import Qt, QPoint, QSize, Signal
from PySide6.QtGui import QPainter, QPixmap, QAction


class PetWindow(QWidget):
    """透明无边框、始终置顶的宠物窗口。

    窗口标志组合：
    - FramelessWindowHint: 无标题栏、无边框
    - WindowStaysOnTopHint: 始终置顶
    - Tool: 不在任务栏和 Alt+Tab 中显示

    属性：
    - WA_TranslucentBackground: 真正的 per-pixel alpha 透明
    """

    # 位置变化信号（外部连接到保存逻辑）
    position_changed = Signal(int, int)
    # 点击信号（非拖拽时触发）
    clicked = Signal()
    # 菜单动作信号（Phase 3+ 连接）
    schedule_requested = Signal()
    chat_requested = Signal()
    settings_requested = Signal()

    # 拖拽相关
    _dragging = False
    _drag_start_pos = None
    _window_start_pos = None
    _drag_threshold = 5

    def __init__(self, parent=None):
        super().__init__(parent)

        # 设置窗口标志
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        # 启用透明背景（在 show() 之后设置，避免 Win11 RHI 问题）
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)

        # 窗口尺寸 64x64（32x32 精灵放大 2 倍）
        self.setFixedSize(QSize(64, 64))

        # 当前要渲染的 QPixmap
        self._current_pixmap: QPixmap | None = None

    def showEvent(self, event):
        """在窗口显示后设置透明背景属性，避免 Win11 RHI 渲染问题。"""
        super().showEvent(event)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def moveEvent(self, event):
        """窗口移动时触发位置变化信号。"""
        super().moveEvent(event)
        pos = event.pos()
        self.position_changed.emit(pos.x(), pos.y())

    def set_pixmap(self, pixmap: QPixmap) -> None:
        """设置当前要渲染的精灵帧。"""
        self._current_pixmap = pixmap
        self.update()  # 触发 paintEvent 重绘

    def paintEvent(self, event):
        """绘制当前精灵帧（缩放到窗口大小）。"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)

        if self._current_pixmap and not self._current_pixmap.isNull():
            # 缩放精灵到窗口大小（保持像素风锐利）
            scaled = self._current_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )
            # 居中绘制
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)

        painter.end()

    def move_to(self, x: int, y: int) -> None:
        """移动窗口到指定屏幕坐标。"""
        self.move(QPoint(x, y))

    def get_position(self) -> tuple[int, int]:
        """获取窗口当前屏幕坐标。"""
        pos = self.pos()
        return (pos.x(), pos.y())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_start_pos = event.globalPosition().toPoint()
            self._window_start_pos = self.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging and self._drag_start_pos:
            delta = event.globalPosition().toPoint() - self._drag_start_pos
            new_pos = self._window_start_pos + delta

            # 约束到屏幕边界
            screen = self.screen()
            if screen:
                geo = screen.availableGeometry()
                new_pos.setX(max(geo.left(), min(new_pos.x(), geo.right() - self.width())))
                new_pos.setY(max(geo.top(), min(new_pos.y(), geo.bottom() - self.height())))

            self.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            delta = event.globalPosition().toPoint() - self._drag_start_pos
            moved = (delta.x() ** 2 + delta.y() ** 2) ** 0.5

            if moved < self._drag_threshold:
                self.clicked.emit()

            self._dragging = False
            self._drag_start_pos = None
            self._window_start_pos = None
            event.accept()

    def contextMenuEvent(self, event):
        """右键弹出上下文菜单。"""
        menu = QMenu(self)

        schedule_action = QAction("日程", self)
        schedule_action.triggered.connect(self.schedule_requested.emit)

        chat_action = QAction("聊天", self)
        chat_action.triggered.connect(self.chat_requested.emit)

        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.settings_requested.emit)

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(QApplication.quit)

        menu.addAction(schedule_action)
        menu.addAction(chat_action)
        menu.addAction(settings_action)
        menu.addSeparator()
        menu.addAction(exit_action)

        menu.exec(event.globalPos())

    def _is_fullscreen_active(self) -> bool:
        """检测当前前台窗口是否为全屏应用。

        使用 Win32 API 获取前台窗口尺寸，与所在显示器尺寸比较。
        如果窗口覆盖整个显示器，认为是全屏应用。
        """
        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if hwnd == int(self.winId()):
                return False  # 宠物自身窗口不算全屏

            rect = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            window_width = rect.right - rect.left
            window_height = rect.bottom - rect.top

            # 获取窗口所在显示器
            monitor = user32.MonitorFromWindow(hwnd, 2)  # MONITOR_DEFAULTTONEAREST

            # 获取显示器信息
            class MONITORINFO(ctypes.Structure):
                _fields_ = [
                    ("cbSize", wintypes.DWORD),
                    ("rcMonitor", wintypes.RECT),
                    ("rcWork", wintypes.RECT),
                    ("dwFlags", wintypes.DWORD),
                ]

            mi = MONITORINFO()
            mi.cbSize = ctypes.sizeof(MONITORINFO)
            user32.GetMonitorInfoW(monitor, ctypes.byref(mi))

            monitor_width = mi.rcMonitor.right - mi.rcMonitor.left
            monitor_height = mi.rcMonitor.bottom - mi.rcMonitor.top

            # 允许 2px 容差（部分应用的全屏窗口可能有微小边框）
            return (
                abs(window_width - monitor_width) <= 2
                and abs(window_height - monitor_height) <= 2
            )
        except Exception:
            return False

    def check_smart_topmost(self) -> None:
        """智能置顶：全屏应用运行时隐藏宠物，否则显示。"""
        if self._is_fullscreen_active():
            if self.isVisible():
                self.hide()
        else:
            if not self.isVisible():
                self.show()
