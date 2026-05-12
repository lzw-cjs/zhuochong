"""换装渲染器：根据节日服装配置叠加装饰到宠物精灵上。"""
import json
from pathlib import Path

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QBrush, QFont

# 服装坐标基于 180x180 画布设计
_COSTUME_CANVAS = 180


class CostumeRenderer:
    """加载服装绘制指令，将装饰叠加到宠物 pixmap 上。"""

    def __init__(self, costumes_path: Path | str | None = None):
        self._costumes: dict[str, dict] = {}
        self._active_costume_id: str | None = None

        if costumes_path is None:
            costumes_path = Path(__file__).parent.parent / "data" / "costumes.json"
        self.load_costumes(costumes_path)

    def load_costumes(self, path: Path | str) -> None:
        try:
            with open(path, encoding="utf-8") as f:
                self._costumes = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[CostumeRenderer] 加载服装数据失败: {e}")
            self._costumes = {}

    def set_active_costume(self, costume_id: str) -> None:
        if costume_id in self._costumes:
            self._active_costume_id = costume_id
            print(f"[CostumeRenderer] 激活服装: {costume_id}")

    def clear_costume(self) -> None:
        if self._active_costume_id:
            print(f"[CostumeRenderer] 清除服装: {self._active_costume_id}")
        self._active_costume_id = None

    def has_active_costume(self) -> bool:
        return self._active_costume_id is not None

    def apply_costume(self, base_pixmap: QPixmap) -> QPixmap:
        """在 base_pixmap 上叠加当前激活的服装装饰。"""
        if not self._active_costume_id:
            return base_pixmap

        costume = self._costumes.get(self._active_costume_id)
        if not costume:
            return base_pixmap

        result = QPixmap(base_pixmap.size())
        result.fill(Qt.GlobalColor.transparent)

        p = QPainter(result)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # 先绘制原始精灵
        p.drawPixmap(0, 0, base_pixmap)

        # 按比例缩放：服装坐标基于 180x180 画布，基础帧为 32x32
        w = base_pixmap.width()
        h = base_pixmap.height()
        scale_x = w / _COSTUME_CANVAS
        scale_y = h / _COSTUME_CANVAS
        p.scale(scale_x, scale_y)

        # 绘制服装指令（坐标在 180x180 空间）
        for cmd in costume.get("commands", []):
            self._execute_command(p, cmd)

        p.end()
        return result

    @staticmethod
    def _execute_command(p: QPainter, cmd: dict) -> None:
        shape = cmd.get("shape")
        color = cmd.get("color", [0, 0, 0])
        alpha = cmd.get("alpha", 255)
        qcolor = QColor(color[0], color[1], color[2], alpha)

        if shape == "ellipse":
            p.setBrush(QBrush(qcolor))
            p.setPen(QPen(Qt.PenStyle.NoPen))
            p.drawEllipse(cmd["x"], cmd["y"], cmd["w"], cmd["h"])

        elif shape == "rect":
            p.setBrush(QBrush(qcolor))
            p.setPen(QPen(Qt.PenStyle.NoPen))
            p.drawRect(cmd["x"], cmd["y"], cmd["w"], cmd["h"])

        elif shape == "line":
            p.setPen(QPen(qcolor, cmd.get("width", 2)))
            p.drawLine(cmd["x1"], cmd["y1"], cmd["x2"], cmd["y2"])

        elif shape == "polygon":
            points = [QPoint(x, y) for x, y in cmd["points"]]
            offset_y = cmd.get("offset_y", 0)
            if offset_y:
                points = [QPoint(pt.x(), pt.y() + offset_y) for pt in points]
            p.setBrush(QBrush(qcolor))
            p.setPen(QPen(Qt.PenStyle.NoPen))
            p.drawPolygon(points)

        elif shape == "text":
            p.setPen(QPen(qcolor))
            font = QFont("Segoe UI Emoji", cmd.get("size", 14))
            font.setPixelSize(cmd.get("size", 14))
            p.setFont(font)
            p.drawText(cmd["x"], cmd["y"], cmd.get("text", ""))
