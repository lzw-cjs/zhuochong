"""Asset path resolution for dev and PyInstaller-frozen modes."""
import sys
from pathlib import Path


def get_asset_path(relative_path: str) -> Path:
    """Resolve asset path for both development and packaged modes.

    Args:
        relative_path: Path relative to project root, e.g. "assets/sounds/reminder.wav"

    Returns:
        Absolute Path to the asset.
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parent.parent
    return base / relative_path
