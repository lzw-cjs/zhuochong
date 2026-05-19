"""CostumeRenderer 单元测试"""
import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtCore import Qt


@pytest.fixture
def costumes_path(tmp_path):
    """创建测试服装数据文件"""
    data = {
        "test_costume": {
            "commands": [
                {"shape": "ellipse", "x": 10, "y": 10, "w": 20, "h": 20, "color": [255, 0, 0]},
                {"shape": "rect", "x": 50, "y": 50, "w": 30, "h": 30, "color": [0, 255, 0]},
                {"shape": "line", "x1": 0, "y1": 0, "x2": 100, "y2": 100, "color": [0, 0, 255], "width": 3},
                {"shape": "text", "x": 80, "y": 80, "text": "测试", "size": 14, "color": [0, 0, 0]},
            ]
        },
        "polygon_costume": {
            "commands": [
                {"shape": "polygon", "points": [[10, 10], [50, 10], [30, 50]], "color": [255, 255, 0]},
            ]
        },
    }
    path = tmp_path / "costumes.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


class TestCostumeRenderer:
    """服装渲染器测试"""

    def test_init_with_path(self, costumes_path):
        from pet.costume import CostumeRenderer

        renderer = CostumeRenderer(costumes_path)
        assert len(renderer._costumes) == 2
        assert "test_costume" in renderer._costumes
        assert "polygon_costume" in renderer._costumes

    def test_init_with_missing_file(self, tmp_path):
        from pet.costume import CostumeRenderer

        renderer = CostumeRenderer(tmp_path / "nonexistent.json")
        assert len(renderer._costumes) == 0

    def test_init_with_invalid_json(self, tmp_path):
        from pet.costume import CostumeRenderer

        path = tmp_path / "invalid.json"
        path.write_text("这不是JSON", encoding="utf-8")

        renderer = CostumeRenderer(path)
        assert len(renderer._costumes) == 0

    def test_set_active_costume(self, costumes_path):
        from pet.costume import CostumeRenderer

        renderer = CostumeRenderer(costumes_path)
        renderer.set_active_costume("test_costume")

        assert renderer._active_costume_id == "test_costume"
        assert renderer.has_active_costume()

    def test_set_active_costume_nonexistent(self, costumes_path):
        from pet.costume import CostumeRenderer

        renderer = CostumeRenderer(costumes_path)
        renderer.set_active_costume("nonexistent")

        assert renderer._active_costume_id is None
        assert not renderer.has_active_costume()

    def test_clear_costume(self, costumes_path):
        from pet.costume import CostumeRenderer

        renderer = CostumeRenderer(costumes_path)
        renderer.set_active_costume("test_costume")
        renderer.clear_costume()

        assert renderer._active_costume_id is None
        assert not renderer.has_active_costume()

    def test_has_active_costume(self, costumes_path):
        from pet.costume import CostumeRenderer

        renderer = CostumeRenderer(costumes_path)
        assert not renderer.has_active_costume()

        renderer.set_active_costume("test_costume")
        assert renderer.has_active_costume()

    def test_apply_costume_no_active(self, costumes_path):
        from pet.costume import CostumeRenderer

        renderer = CostumeRenderer(costumes_path)
        base = QPixmap(180, 180)
        base.fill(Qt.GlobalColor.red)

        result, ox, oy = renderer.apply_costume(base)
        assert not result.isNull()
        assert ox == 0
        assert oy == 0

    def test_apply_costume_with_active(self, costumes_path):
        from pet.costume import CostumeRenderer

        renderer = CostumeRenderer(costumes_path)
        renderer.set_active_costume("test_costume")

        base = QPixmap(180, 180)
        base.fill(Qt.GlobalColor.red)

        result, ox, oy = renderer.apply_costume(base)
        assert not result.isNull()
        assert result.width() == 180
        assert result.height() == 180

    def test_apply_costume_with_polygon(self, costumes_path):
        from pet.costume import CostumeRenderer

        renderer = CostumeRenderer(costumes_path)
        renderer.set_active_costume("polygon_costume")

        base = QPixmap(180, 180)
        base.fill(Qt.GlobalColor.red)

        result, ox, oy = renderer.apply_costume(base)
        assert not result.isNull()

    def test_apply_costume_negative_coords(self, tmp_path):
        """测试负坐标服装元素（如帽子 y=-30）不会被裁剪"""
        from pet.costume import CostumeRenderer

        data = {
            "hat": {
                "commands": [
                    {"shape": "polygon", "points": [[90, -30], [68, 14], [112, 14]], "color": [100, 150, 255]},
                    {"shape": "ellipse", "x": 72, "y": -8, "w": 36, "h": 40, "color": [220, 20, 20]},
                ]
            }
        }
        path = tmp_path / "costumes.json"
        path.write_text(json.dumps(data), encoding="utf-8")

        renderer = CostumeRenderer(path)
        renderer.set_active_costume("hat")

        base = QPixmap(180, 180)
        base.fill(Qt.GlobalColor.red)

        result, ox, oy = renderer.apply_costume(base)
        assert not result.isNull()
        # 画布应该扩展以容纳负坐标元素
        assert oy > 0, "服装偏移量应大于 0 以容纳负坐标元素"
        assert result.height() > 180, "画布高度应大于 180 以容纳超出的服装元素"

    def test_execute_command_ellipse(self, qtbot):
        from pet.costume import CostumeRenderer

        pixmap = QPixmap(180, 180)
        painter = QPainter(pixmap)

        cmd = {"shape": "ellipse", "x": 10, "y": 10, "w": 20, "h": 20, "color": [255, 0, 0]}
        CostumeRenderer._execute_command(painter, cmd)
        painter.end()

    def test_execute_command_rect(self, qtbot):
        from pet.costume import CostumeRenderer

        pixmap = QPixmap(180, 180)
        painter = QPainter(pixmap)

        cmd = {"shape": "rect", "x": 10, "y": 10, "w": 20, "h": 20, "color": [0, 255, 0]}
        CostumeRenderer._execute_command(painter, cmd)
        painter.end()

    def test_execute_command_line(self, qtbot):
        from pet.costume import CostumeRenderer

        pixmap = QPixmap(180, 180)
        painter = QPainter(pixmap)

        cmd = {"shape": "line", "x1": 0, "y1": 0, "x2": 100, "y2": 100, "color": [0, 0, 255]}
        CostumeRenderer._execute_command(painter, cmd)
        painter.end()

    def test_execute_command_polygon(self, qtbot):
        from pet.costume import CostumeRenderer

        pixmap = QPixmap(180, 180)
        painter = QPainter(pixmap)

        cmd = {"shape": "polygon", "points": [[10, 10], [50, 10], [30, 50]], "color": [255, 255, 0]}
        CostumeRenderer._execute_command(painter, cmd)
        painter.end()

    def test_execute_command_text(self, qtbot):
        from pet.costume import CostumeRenderer

        pixmap = QPixmap(180, 180)
        painter = QPainter(pixmap)

        cmd = {"shape": "text", "x": 80, "y": 80, "text": "测试", "size": 14, "color": [0, 0, 0]}
        CostumeRenderer._execute_command(painter, cmd)
        painter.end()
