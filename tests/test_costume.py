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

        result = renderer.apply_costume(base)
        assert not result.isNull()

    def test_apply_costume_with_active(self, costumes_path):
        from pet.costume import CostumeRenderer

        renderer = CostumeRenderer(costumes_path)
        renderer.set_active_costume("test_costume")

        base = QPixmap(180, 180)
        base.fill(Qt.GlobalColor.red)

        result = renderer.apply_costume(base)
        assert not result.isNull()
        assert result.width() == 180
        assert result.height() == 180

    def test_apply_costume_with_polygon(self, costumes_path):
        from pet.costume import CostumeRenderer

        renderer = CostumeRenderer(costumes_path)
        renderer.set_active_costume("polygon_costume")

        base = QPixmap(180, 180)
        base.fill(Qt.GlobalColor.red)

        result = renderer.apply_costume(base)
        assert not result.isNull()

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
