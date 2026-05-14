"""PetTrayIcon 单元测试"""
import pytest
from unittest.mock import MagicMock, patch


class TestPetTrayIcon:
    """系统托盘图标测试"""

    @patch("pet.tray.get_asset_path")
    def test_init_with_icon(self, mock_get_asset, qtbot):
        from pet.tray import PetTrayIcon
        from pathlib import Path

        # 使用真实的图标路径
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.__str__ = lambda self: "assets/icon.ico"
        mock_get_asset.return_value = mock_path

        # 直接测试 tooltip 设置
        tray = PetTrayIcon()
        assert tray.toolTip() == "智能桌面宠物"

    @patch("pet.tray.get_asset_path")
    def test_init_without_icon(self, mock_get_asset, qtbot):
        from pet.tray import PetTrayIcon

        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_get_asset.return_value = mock_path

        tray = PetTrayIcon()
        assert tray.toolTip() == "智能桌面宠物"

    @patch("pet.tray.get_asset_path")
    def test_update_visibility_state_visible(self, mock_get_asset, qtbot):
        from pet.tray import PetTrayIcon

        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_get_asset.return_value = mock_path

        tray = PetTrayIcon()
        tray.update_visibility_state(True)

        assert tray._toggle_action.text() == "隐藏宠物"

    @patch("pet.tray.get_asset_path")
    def test_update_visibility_state_hidden(self, mock_get_asset, qtbot):
        from pet.tray import PetTrayIcon

        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_get_asset.return_value = mock_path

        tray = PetTrayIcon()
        tray.update_visibility_state(False)

        assert tray._toggle_action.text() == "显示宠物"

    @patch("pet.tray.get_asset_path")
    def test_reminder_suppress_signal(self, mock_get_asset, qtbot):
        from pet.tray import PetTrayIcon

        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_get_asset.return_value = mock_path

        tray = PetTrayIcon()
        signals = []
        tray.reminder_suppress.connect(lambda v: signals.append(v))

        tray._on_reminder_toggle(True)
        assert signals == [True]

        tray._on_reminder_toggle(False)
        assert signals == [True, False]

    @patch("pet.tray.get_asset_path")
    def test_reminder_action_text(self, mock_get_asset, qtbot):
        from pet.tray import PetTrayIcon

        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_get_asset.return_value = mock_path

        tray = PetTrayIcon()
        tray._on_reminder_toggle(True)
        assert tray._reminder_action.text() == "开启提醒"

        tray._on_reminder_toggle(False)
        assert tray._reminder_action.text() == "关闭提醒"

    @patch("pet.tray.get_asset_path")
    def test_update_reminder_suppressed(self, mock_get_asset, qtbot):
        from pet.tray import PetTrayIcon

        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_get_asset.return_value = mock_path

        tray = PetTrayIcon()
        tray.update_reminder_suppressed(True)

        assert tray._reminder_action.isChecked()
        assert tray._reminder_action.text() == "开启提醒"

        tray.update_reminder_suppressed(False)

        assert not tray._reminder_action.isChecked()
        assert tray._reminder_action.text() == "关闭提醒"


class TestCreatePlaceholderIcon:
    """占位图标测试"""

    def test_create_placeholder_icon(self, qtbot):
        from pet.tray import create_placeholder_icon

        icon = create_placeholder_icon()
        assert icon is not None
        assert not icon.isNull()
