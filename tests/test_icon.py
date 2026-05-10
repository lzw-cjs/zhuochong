"""Tests for icon file validity."""
from pathlib import Path


def test_icon_file_exists():
    """assets/icon.ico exists and is non-empty."""
    icon_path = Path("assets/icon.ico")
    assert icon_path.exists(), "assets/icon.ico does not exist"
    assert icon_path.stat().st_size > 0, "assets/icon.ico is empty"


def test_icon_file_is_valid_ico():
    """assets/icon.ico starts with valid ICO header (0x0000, 0x0100)."""
    icon_path = Path("assets/icon.ico")
    with open(icon_path, "rb") as f:
        header = f.read(6)
    # ICO header: reserved(2) + type(2) + count(2)
    # type == 1 for ICO
    assert header[2:4] == b'\x01\x00', "Not a valid ICO file (type field != 1)"


def test_icon_contains_multiple_sizes():
    """assets/icon.ico contains at least 2 image entries (16x16 and 32x32)."""
    icon_path = Path("assets/icon.ico")
    with open(icon_path, "rb") as f:
        f.seek(4)  # skip reserved + type
        count_bytes = f.read(2)
    count = int.from_bytes(count_bytes, 'little')
    assert count >= 2, f"Expected at least 2 icon sizes, got {count}"
