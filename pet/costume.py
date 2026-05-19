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

    def apply_costume(self, base_pixmap: QPixmap) -> tuple[QPixmap, int, int]:
        """在 base_pixmap 上叠加当前激活的服装装饰。

        返回 (result_pixmap, offset_x, offset_y)：
        - result_pixmap: 可能比 base_pixmap 大，以容纳超出边界的服装元素
        - offset_x/y: 原始精灵在 result 中的偏移（用于显示定位）
        """
        if not self._active_costume_id:
            return base_pixmap, 0, 0

        costume = self._costumes.get(self._active_costume_id)
        if not costume:
            return base_pixmap, 0, 0

        commands = costume.get("commands", [])
        if not commands:
            return base_pixmap, 0, 0

        # 计算服装指令的边界框（可能包含负坐标）
        min_x, min_y, max_x, max_y = self._get_commands_bounds(commands)

        # 计算画布需要的扩展量
        expand_left = max(0, -min_x)
        expand_top = max(0, -min_y)
        expand_right = max(0, max_x - _COSTUME_CANVAS)
        expand_bottom = max(0, max_y - _COSTUME_CANVAS)

        # 如果服装没有超出原始画布，使用原始逻辑
        if expand_left == 0 and expand_top == 0 and expand_right == 0 and expand_bottom == 0:
            result = QPixmap(base_pixmap.size())
            result.fill(Qt.GlobalColor.transparent)
            p = QPainter(result)
            p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            p.drawPixmap(0, 0, base_pixmap)
            w, h = base_pixmap.width(), base_pixmap.height()
            p.scale(w / _COSTUME_CANVAS, h / _COSTUME_CANVAS)
            for cmd in commands:
                self._execute_command(p, cmd)
            p.end()
            return result, 0, 0

        # 扩展画布以容纳所有服装元素
        result_w = _COSTUME_CANVAS + expand_left + expand_right
        result_h = _COSTUME_CANVAS + expand_top + expand_bottom
        result = QPixmap(result_w, result_h)
        result.fill(Qt.GlobalColor.transparent)

        p = QPainter(result)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # 在扩展画布上绘制原始精灵（偏移到正确位置）
        p.drawPixmap(expand_left, expand_top, base_pixmap)

        # 平移坐标系以匹配服装指令空间
        p.translate(expand_left, expand_top)

        # 绘制服装指令（坐标在原始 180x180 空间，已通过 translate 偏移）
        for cmd in commands:
            self._execute_command(p, cmd)

        p.end()
        return result, expand_left, expand_top

    @staticmethod
    def _get_commands_bounds(commands: list[dict]) -> tuple[int, int, int, int]:
        """计算服装指令的边界框。"""
        min_x, min_y = 0, 0
        max_x, max_y = _COSTUME_CANVAS, _COSTUME_CANVAS

        for cmd in commands:
            shape = cmd.get("shape")
            if shape == "rect":
                min_x = min(min_x, cmd["x"])
                min_y = min(min_y, cmd["y"])
                max_x = max(max_x, cmd["x"] + cmd["w"])
                max_y = max(max_y, cmd["y"] + cmd["h"])
            elif shape == "ellipse":
                min_x = min(min_x, cmd["x"])
                min_y = min(min_y, cmd["y"])
                max_x = max(max_x, cmd["x"] + cmd["w"])
                max_y = max(max_y, cmd["y"] + cmd["h"])
            elif shape == "line":
                min_x = min(min_x, cmd["x1"], cmd["x2"])
                min_y = min(min_y, cmd["y1"], cmd["y2"])
                max_x = max(max_x, cmd["x1"], cmd["x2"])
                max_y = max(max_y, cmd["y1"], cmd["y2"])
            elif shape == "polygon":
                for px, py in cmd["points"]:
                    offset_y = cmd.get("offset_y", 0)
                    min_x = min(min_x, px)
                    min_y = min(min_y, py + offset_y)
                    max_x = max(max_x, px)
                    max_y = max(max_y, py + offset_y)
            elif shape == "text":
                min_x = min(min_x, cmd["x"])
                min_y = min(min_y, cmd["y"])

        return min_x, min_y, max_x, max_y

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
