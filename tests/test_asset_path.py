"""Tests for utils.assets.get_asset_path — dev and frozen modes."""
import sys
from pathlib import Path
from unittest.mock import patch


def test_dev_mode_returns_absolute_path():
    """get_asset_path returns absolute path in dev mode."""
    from utils.assets import get_asset_path
    result = get_asset_path("assets/sounds")
    assert result.is_absolute()
    assert result.parts[-2:] == ("assets", "sounds")


def test_dev_mode_base_is_project_root():
    """In dev mode, base is the project root (parent of utils/)."""
    from utils.assets import get_asset_path
    result = get_asset_path("assets/sounds")
    expected_base = Path(__file__).resolve().parent.parent
    assert str(result).startswith(str(expected_base))


def test_frozen_mode_uses_meipass():
    """When sys.frozen is True, base is sys._MEIPASS."""
    from utils import assets
    fake_meipass = Path("/tmp/fake_bundle")
    with patch.object(sys, 'frozen', True, create=True), \
         patch.object(sys, '_MEIPASS', str(fake_meipass), create=True):
        result = assets.get_asset_path("assets/icon.ico")
    assert str(result) == str(fake_meipass / "assets/icon.ico")


def test_frozen_mode_resolves_data_path():
    """Frozen mode also works for data/ paths."""
    from utils import assets
    fake_meipass = Path("/tmp/fake_bundle")
    with patch.object(sys, 'frozen', True, create=True), \
         patch.object(sys, '_MEIPASS', str(fake_meipass), create=True):
        result = assets.get_asset_path("data/chat_rules.json")
    assert str(result) == str(fake_meipass / "data/chat_rules.json")
