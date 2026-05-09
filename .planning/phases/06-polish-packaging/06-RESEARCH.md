# Phase 6: Polish & Packaging - Research

**Researched:** 2026-05-10
**Domain:** PyInstaller packaging, asset resolution, JSON schema versioning, Windows .ico creation
**Confidence:** HIGH

## Summary

Phase 6 covers four polish/packaging tasks: (P6.1) a centralized asset path helper that works in both dev and PyInstaller-bundled modes, (P6.2) schema versioning with a migration registry for all JSON data files, (P6.3) a proper pixel-art .ico for the system tray icon, and (P6.4) PyInstaller spec configuration for --onedir packaging.

The codebase currently has 3 hardcoded asset path patterns (`Path("assets/sounds")` in main.py, `Path(__file__).parent.parent / "data" / "chat_rules.json"` in chat_engine.py, and `QPixmap` generated in-memory in animator.py). The tray icon is a programmatically-drawn 16x16 brown circle. Settings already has `_schema_version: 1` but ScheduleStore and CalendarStore do not. PyInstaller is not currently installed in the environment.

**Primary recommendation:** Use `--onedir` mode (not `--onefile`) for PyInstaller with PySide6 apps. Create a `utils/assets.py` module with a single `get_asset_path()` function. Add `_schema_version` to all JSON stores with a simple migration registry dict.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Asset path resolution | Python utils module | PyInstaller spec | Single function used by all modules |
| Schema versioning | Data layer (store.py) | Individual store modules | Centralized migration logic in store |
| Tray icon | pet/tray.py | assets/ directory | Icon file loaded by tray module |
| Packaging | PyInstaller spec | Entry point (main.py) | Spec controls bundling; main.py needs frozen check |

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DAT-03 | Data schema versioning (embed _schema_version, support migration) | Migration registry pattern documented below |
| PKG-01 | Use PyInstaller to package as standalone .exe | PyInstaller spec file pattern documented |
| PKG-02 | Asset path helper (get_asset_path, compatible with packaged path) | sys._MEIPASS pattern documented |
| PKG-03 | System tray .ico icon | Pillow ICO creation pattern documented |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PySide6 | 6.11.0 (installed) | GUI framework | Already in use [VERIFIED: pip show] |
| PySide6-Addons | 6.11.0 (installed) | Multimedia (QSoundEffect) | Already in use [VERIFIED: pip show] |
| Pillow | 12.2.0 (installed) | .ico file creation | Standard Python imaging library [VERIFIED: pip show] |
| PyInstaller | (not installed) | Executable packaging | Industry standard for Python packaging [ASSUMED] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| filelock | 3.29.0 (installed) | Cross-process JSON locking | Already available [VERIFIED: pip show] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pillow for .ico | QPixmap.save() | QPixmap can save .ico but Pillow gives more control over multi-resolution |
| PyInstaller | Nuitka | Nuitka produces faster/smaller binaries but compile times are 10-60 min; PyInstaller is fine for this project |

**Installation:**
```bash
pip install PyInstaller
```
(Pillow and PySide6 already installed)

**Version verification:** PySide6 6.11.0, Pillow 12.2.0, filelock 3.29.0 all confirmed installed. PyInstaller needs to be installed.

## Architecture Patterns

### System Architecture Diagram

```
                    +-------------------+
                    |    main.py        |
                    | (entry point)     |
                    +--------+----------+
                             |
              +--------------+--------------+
              |              |              |
     +--------v---+  +-------v------+ +----v--------+
     | utils/     |  | data/store.py| | pet/tray.py  |
     | assets.py  |  | (JsonStore)  | | (QSystem     |
     | get_asset_ |  | + migration  | |  TrayIcon)   |
     | path()     |  |   registry   | |              |
     +-----+------+  +------+------+ +------+-------+
           |                |                 |
    +------+------+   +-----+------+   +-----+------+
    | assets/     |   | APPDATA/   |   | assets/    |
    | sounds/     |   | settings   |   | icon.ico   |
    | sprites/    |   | events     |   +------------+
    | icon.ico    |   | calendars  |
    +-------------+   +------------+
```

Data flow: All modules call `get_asset_path("relative/path")` to resolve asset locations. In dev mode this resolves relative to project root. In frozen (PyInstaller) mode it resolves to `sys._MEIPASS`. JSON stores read/write to APPDATA with schema version checks on load.

### Recommended Project Structure
```
src/
  utils/
    __init__.py
    assets.py          # get_asset_path() helper
  data/
    store.py           # JsonStore + migration registry
    settings.py        # Settings (already has _schema_version)
    schedule_store.py  # ScheduleStore (needs _schema_version)
    calendar_store.py  # CalendarStore (needs _schema_version)
  pet/
    tray.py            # Updated to load .ico from assets
  assets/
    icon.ico           # Multi-resolution .ico (16x16, 32x32)
    sounds/
      reminder.wav
    sprites/
      (state directories)
  main.py              # Entry point with frozen check
  desktop_pet.spec     # PyInstaller spec file
```

### Pattern 1: Asset Path Helper (P6.1)

**What:** A single function that resolves relative asset paths to absolute paths, working correctly in both development (running from source) and packaged (PyInstaller frozen) modes.

**When to use:** Every time code needs to load a file from the `assets/` directory or bundled data files.

**Example:**
```python
# utils/assets.py
# Source: PyInstaller official documentation pattern
import sys
from pathlib import Path


def get_asset_path(relative_path: str) -> Path:
    """Resolve asset path for both dev and PyInstaller-frozen modes.

    In dev mode: relative to project root (where main.py lives).
    In frozen mode: relative to sys._MEIPASS (PyInstaller extraction dir).
    """
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        base = Path(sys._MEIPASS)
    else:
        # Running in development
        base = Path(__file__).resolve().parent.parent
    return base / relative_path
```

**Usage across codebase:**
```python
# main.py - BEFORE:
sound_manager = SoundManager(Path("assets/sounds"))
# main.py - AFTER:
from utils.assets import get_asset_path
sound_manager = SoundManager(get_asset_path("assets/sounds"))

# pet/chat_engine.py - BEFORE:
rules_path = Path(__file__).parent.parent / "data" / "chat_rules.json"
# pet/chat_engine.py - AFTER:
from utils.assets import get_asset_path
rules_path = get_asset_path("data/chat_rules.json")

# pet/tray.py - loading .ico:
from utils.assets import get_asset_path
icon = QIcon(str(get_asset_path("assets/icon.ico")))
```

**Files with hardcoded paths that need updating:**
| File | Current Pattern | New Pattern |
|------|----------------|-------------|
| `main.py:110` | `Path("assets/sounds")` | `get_asset_path("assets/sounds")` |
| `pet/chat_engine.py:22` | `Path(__file__).parent.parent / "data" / "chat_rules.json"` | `get_asset_path("data/chat_rules.json")` |
| `tests/test_sound_manager.py:17,29,41` | `Path("assets/sounds")` | Keep as-is for tests (tests run from project root) |

### Pattern 2: Schema Versioning with Migration Registry (P6.2)

**What:** Each JSON data file includes a `_schema_version` integer. A central registry maps version numbers to transform functions. On load, if the stored version differs from current, migrations are applied sequentially.

**When to use:** Every `JsonStore` subclass that persists structured data.

**Example:**
```python
# data/store.py - MigrationRegistry addition
from typing import Callable

# Registry: version -> transform function
# Each function takes (data: dict) -> dict and upgrades from version N to N+1
_MIGRATIONS: dict[str, dict[int, Callable[[dict], dict]]] = {}


def register_migration(store_name: str, from_version: int):
    """Decorator to register a migration function."""
    def decorator(func: Callable[[dict], dict]):
        if store_name not in _MIGRATIONS:
            _MIGRATIONS[store_name] = {}
        _MIGRATIONS[store_name][from_version] = func
        return func
    return decorator


class JsonStore:
    def __init__(self, filename: str, store_name: str | None = None):
        self.filepath = APPDATA_DIR / filename
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self._store_name = store_name or filename.replace(".json", "")

    def load(self, default: dict | None = None, current_version: int = 1) -> dict:
        if not self.filepath.exists():
            return default if default is not None else {}
        with open(self.filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Auto-migrate if version mismatch
        stored_version = data.get("_schema_version", 0)
        if stored_version < current_version:
            data = self._migrate(data, stored_version, current_version)
            self.save(data)  # persist migrated data
        return data

    def _migrate(self, data: dict, from_ver: int, to_ver: int) -> dict:
        migrations = _MIGRATIONS.get(self._store_name, {})
        for ver in range(from_ver, to_ver):
            if ver in migrations:
                data = migrations[ver](data)
        data["_schema_version"] = to_ver
        return data
```

**Registration pattern:**
```python
# data/schedule_store.py
from data.store import JsonStore, register_migration

SCHEDULE_SCHEMA_VERSION = 2

@register_migration("events", from_version=1)
def migrate_events_v1_to_v2(data: dict) -> dict:
    """Add 'status' field to events missing it."""
    for event in data.get("events", []):
        if "status" not in event:
            event["status"] = "completed" if event.get("completed") else "pending"
    return data


class ScheduleStore:
    def __init__(self):
        self._store = JsonStore("events.json", store_name="events")

    def _load_events(self) -> list[dict]:
        data = self._store.load(
            default={"events": []},
            current_version=SCHEDULE_SCHEMA_VERSION,
        )
        return data.get("events", [])
```

### Pattern 3: .ico Creation with Pillow (P6.3)

**What:** Generate a multi-resolution .ico file programmatically using Pillow, containing 16x16 and 32x32 versions for the system tray and window icon.

**When to use:** Build-time script or one-time asset generation.

**Example:**
```python
# scripts/generate_icon.py (build-time utility)
from PIL import Image, ImageDraw

def create_pet_icon() -> None:
    """Generate a pixel-art sloth icon for the system tray."""
    sizes = [(16, 16), (32, 32)]
    images = []

    for size in sizes:
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        scale = size[0] // 16

        # Body (brown oval)
        draw.ellipse(
            [2*scale, 3*scale, 14*scale, 15*scale],
            fill=(139, 90, 43, 255)
        )
        # Eyes
        draw.ellipse([5*scale, 6*scale, 7*scale, 8*scale], fill=(0, 0, 0, 255))
        draw.ellipse([9*scale, 6*scale, 11*scale, 8*scale], fill=(0, 0, 0, 255))
        # Nose
        draw.ellipse([7*scale, 9*scale, 9*scale, 10*scale], fill=(80, 50, 20, 255))

        images.append(img)

    images[0].save(
        "assets/icon.ico",
        format="ICO",
        sizes=[img.size for img in images],
        append_images=images[1:],
    )

if __name__ == "__main__":
    create_pet_icon()
```

**Key detail:** Pillow's `Image.save(format="ICO", sizes=...)` automatically creates a multi-resolution .ico file. The `sizes` parameter tells Pillow which resolutions to embed. [ASSUMED: Pillow 12.x behavior]

### Pattern 4: PyInstaller Spec for PySide6 (P6.4)

**What:** A `.spec` file configured for `--onedir` mode with PySide6, bundling all assets and excluding unused Qt modules.

**When to use:** Building the distributable executable.

**Example:**
```python
# desktop_pet.spec
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

block_cipher = None

# Collect PySide6 data files (Qt plugins, translations, etc.)
pyside6_datas = collect_data_files('PySide6', include_py_files=False)
pyside6_binaries = collect_dynamic_libs('PySide6')

# Project assets
project_datas = [
    ('assets', 'assets'),
    ('data/chat_rules.json', 'data'),
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=pyside6_binaries,
    datas=pyside6_datas + project_datas,
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtMultimedia',
    ],
    excludes=[
        # Large unused modules (saves 100+ MB)
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineQuick',
        'PySide6.Qt3DCore',
        'PySide6.Qt3DRender',
        'PySide6.Qt3DInput',
        'PySide6.Qt3DLogic',
        'PySide6.Qt3DExtras',
        'PySide6.Qt3DAnimation',
        'PySide6.QtQuick',
        'PySide6.QtQuickWidgets',
        'PySide6.QtQml',
        'PySide6.QtCharts',
        'PySide6.QtDataVisualization',
        'PySide6.QtSvg',
        'PySide6.QtSvgWidgets',
        'PySide6.QtOpenGL',
        'PySide6.QtOpenGLWidgets',
        'PySide6.QtHelp',
        'PySide6.QtTest',
        'PySide6.QtDesigner',
        'PySide6.QtShaderTools',
        'PySide6.QtPdf',
        'PySide6.QtPdfWidgets',
        'PySide6.QtSpatialAudio',
        'PySide6.QtHttpServer',
        'PySide6.QtBluetooth',
        'PySide6.QtNfc',
        'PySide6.QtPositioning',
        'PySide6.QtRemoteObjects',
        'PySide6.QtScxml',
        'PySide6.QtSensors',
        'PySide6.QtSerialBus',
        'PySide6.QtSerialPort',
        'PySide6.QtTextToSpeech',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,  # --onedir mode
    name='SmartDesktopPet',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,           # --windowed: no console window
    icon='assets/icon.ico',  # executable icon
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SmartDesktopPet',
)
```

**Build command:**
```bash
pyinstaller desktop_pet.spec
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Asset path resolution | Custom sys.path manipulation | `sys._MEIPASS` + `getattr(sys, 'frozen')` check | PyInstaller's documented pattern; handles all edge cases |
| .ico file creation | Manual byte manipulation | `Pillow.Image.save(format="ICO")` | Correct ICO format with multi-resolution support |
| JSON atomic writes | Manual temp file + rename | Already implemented in `JsonStore` | Existing implementation is correct |
| Qt plugin bundling | Manual copy of DLLs | `collect_data_files('PySide6')` in spec | PyInstaller hooks handle plugin discovery |

## Common Pitfalls

### Pitfall 1: Missing Qt Platform Plugin
**What goes wrong:** Application fails to start with "This application failed to start because no Qt platform plugin could be initialized."
**Why it happens:** PyInstaller doesn't always copy `platforms/qwindows.dll` automatically.
**How to avoid:** Use `collect_data_files('PySide6')` in the spec file, or add `--collect-all PySide6` to the build command. Verify `platforms/qwindows.dll` exists in the output `_internal/PySide6/` directory.
**Warning signs:** Error message about Qt platform plugin on first test run.

### Pitfall 2: sys._MEIPASS Not Set in Dev Mode
**What goes wrong:** `AttributeError: module 'sys' has no attribute '_MEIPASS'`
**Why it happens:** `sys._MEIPASS` only exists when running from a PyInstaller bundle.
**How to avoid:** Always use `getattr(sys, '_MEIPASS', None)` or `getattr(sys, 'frozen', False)` as the check, never access `sys._MEIPASS` directly.
**Warning signs:** Crash on startup when running from source.

### Pitfall 3: --onefile Slow Startup with PySide6
**What goes wrong:** Application takes 5-10 seconds to start because it extracts all files to a temp directory on every launch.
**Why it happens:** `--onefile` mode extracts the entire bundle (including PySide6's ~50MB of DLLs) to a temp folder on each startup.
**How to avoid:** Use `--onedir` mode instead. If single-file distribution is needed, use an installer maker (Inno Setup, NSIS) to wrap the `--onedir` output.
**Warning signs:** User reports slow startup.

### Pitfall 4: Hardcoded Relative Paths Break After Packaging
**What goes wrong:** `FileNotFoundError` when loading sounds, chat rules, or sprites from packaged app.
**Why it happens:** `Path("assets/sounds")` resolves relative to the current working directory, which is different when running from a packaged .exe.
**How to avoid:** Replace ALL hardcoded paths with `get_asset_path()` calls. Grep for `Path("` and `QPixmap("` to find all instances.
**Warning signs:** Asset loading errors in packaged builds only.

### Pitfall 5: Schema Migration Overwriting User Data
**What goes wrong:** Migration function has a bug that corrupts user data.
**Why it happens:** No backup before migration; no rollback mechanism.
**How to avoid:** Always create a `.bak` copy of the JSON file before running migrations. Test migration functions with sample data from each schema version.
**Warning signs:** Data loss reported after app update.

## Code Examples

### Complete Asset Path Helper
```python
# utils/assets.py
import sys
from pathlib import Path


def get_asset_path(relative_path: str) -> Path:
    """Resolve asset path for dev and PyInstaller-frozen modes.

    Args:
        relative_path: Path relative to project root, e.g. "assets/sounds/reminder.wav"

    Returns:
        Absolute Path to the asset.
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base = Path(sys._MEIPASS)
    else:
        # __file__ is utils/assets.py -> parent.parent is project root
        base = Path(__file__).resolve().parent.parent
    return base / relative_path
```

### Migration Registry Usage
```python
# data/store.py - in JsonStore.load()
def load(self, default=None, current_version=1):
    if not self.filepath.exists():
        return default if default is not None else {}
    with open(self.filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    stored = data.get("_schema_version", 0)
    if stored < current_version:
        data = self._migrate(data, stored, current_version)
        self.save(data)
    return data
```

### .ico Generation with Pillow
```python
from PIL import Image, ImageDraw

def generate_icon(output_path: str = "assets/icon.ico"):
    sizes = [(16, 16), (32, 32)]
    images = []
    for size in sizes:
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        s = size[0] // 16
        # Brown body
        draw.ellipse([2*s, 3*s, 14*s, 15*s], fill=(139, 90, 43))
        # Black eyes
        draw.ellipse([5*s, 6*s, 7*s, 8*s], fill=(0, 0, 0))
        draw.ellipse([9*s, 6*s, 11*s, 8*s], fill=(0, 0, 0))
        images.append(img)
    images[0].save(output_path, format="ICO",
                   sizes=[i.size for i in images],
                   append_images=images[1:])
```

### PyInstaller Frozen Check in main.py
```python
# At top of main.py, before any PySide6 imports:
import os
import sys

if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle
    os.environ['QT_PLUGIN_PATH'] = os.path.join(sys._MEIPASS, 'PySide6', 'Qt', 'plugins')
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| PyInstaller --onefile | PyInstaller --onedir | PyInstaller 6.x (2024) | --onedir is now recommended for Qt apps; --onefile has more issues |
| Manual Qt plugin copy | `collect_data_files('PySide6')` | PyInstaller hooks improved | Automatic plugin discovery |
| `sys._MEIPASS` direct access | `getattr(sys, 'frozen', False)` check | Best practice evolution | More robust; works when not frozen |

**Deprecated/outdated:**
- `--onefile` for Qt apps: Not deprecated but strongly discouraged due to startup time and plugin issues
- Manual `qt.conf` editing: Usually unnecessary with modern PyInstaller + `collect_data_files`

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | PyInstaller is the correct packaging tool for this project (vs Nuitka) | Standard Stack | Could switch to Nuitka with minimal code changes; spec file format differs |
| A2 | `Pillow.Image.save(format="ICO", sizes=...)` works correctly for multi-resolution .ico | Pattern 3 | Would need to use a different library or manual ICO construction |
| A3 | `collect_data_files('PySide6')` properly includes Qt platform plugins | Pattern 4 | May need manual plugin directory specification |
| A4 | The project does not use QML, only QWidget-based UI | Pattern 4 excludes | If QML is used, `QtQml` and `QtQuick` should NOT be excluded |
| A5 | `os.replace()` is atomic on Windows for the migration save-back | Pattern 2 | Verified in CLAUDE.md as correct |

## Open Questions

1. **Should chat_rules.json be bundled as an asset or remain in data/?**
   - What we know: Currently at `data/chat_rules.json`, loaded via `Path(__file__).parent.parent / "data"`
   - What's unclear: Whether it should be a bundled asset (read-only) or remain editable
   - Recommendation: Bundle it as an asset (read-only). If user customization is needed later, copy to APPDATA on first run.

2. **PyInstaller version to install?**
   - What we know: PyInstaller 6.x is current; not installed in environment
   - What's unclear: Exact version to pin
   - Recommendation: Install latest PyInstaller 6.x (`pip install PyInstaller`)

3. **Should the .ico be generated at build time or committed as a binary asset?**
   - What we know: No .ico exists yet; Pillow is available
   - What's unclear: Whether to generate on each build or commit once
   - Recommendation: Generate once with a script, commit the .ico to version control. Avoid build-time dependencies on Pillow for icon generation.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | All | YES | (not detected via python3, but pip works) | - |
| PySide6 | GUI framework | YES | 6.11.0 | - |
| PySide6-Addons | QSoundEffect | YES | 6.11.0 | - |
| Pillow | .ico creation | YES | 12.2.0 | - |
| filelock | JSON locking | YES | 3.29.0 | - |
| PyInstaller | Packaging | NO | - | Must install: `pip install PyInstaller` |

**Missing dependencies with no fallback:**
- PyInstaller must be installed before P6.4 can execute

**Missing dependencies with fallback:**
- None

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (detected via tests/ directory) |
| Config file | none detected |
| Quick run command | `pytest tests/ -x` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PKG-02 | get_asset_path() resolves correctly in dev mode | unit | `pytest tests/test_assets.py -x` | NO - Wave 0 |
| PKG-02 | get_asset_path() uses sys._MEIPASS when frozen | unit (mock) | `pytest tests/test_assets.py::test_frozen -x` | NO - Wave 0 |
| DAT-03 | Schema migration runs on version mismatch | unit | `pytest tests/test_store_migration.py -x` | NO - Wave 0 |
| DAT-03 | Migration preserves existing data | unit | `pytest tests/test_store_migration.py::test_preserves_data -x` | NO - Wave 0 |
| PKG-03 | .ico file is valid and contains 16x16 + 32x32 | unit | `pytest tests/test_icon.py -x` | NO - Wave 0 |
| PKG-01 | PyInstaller build succeeds | integration | `pyinstaller desktop_pet.spec` | NO - Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green + manual test of packaged .exe

### Wave 0 Gaps
- [ ] `tests/test_assets.py` — covers PKG-02 (asset path resolution)
- [ ] `tests/test_store_migration.py` — covers DAT-03 (schema migration)
- [ ] `tests/test_icon.py` — covers PKG-03 (ico validation)
- [ ] `utils/__init__.py` — new package for assets module
- [ ] `utils/assets.py` — the asset path helper itself
- [ ] `desktop_pet.spec` — PyInstaller spec file
- [ ] `assets/icon.ico` — generated icon file
- [ ] PyInstaller install: `pip install PyInstaller`

## Sources

### Primary (HIGH confidence)
- PyInstaller documentation: https://pyinstaller.org/en/stable/ — sys._MEIPASS pattern, spec file format, --onedir mode
- Pillow documentation: https://pillow.readthedthedocs.io/ — ICO format support, multi-resolution save
- Codebase inspection — verified all hardcoded paths, current schema versions, installed packages

### Secondary (MEDIUM confidence)
- WebSearch: PyInstaller + PySide6 best practices — --onedir recommended over --onefile, collect_data_files pattern
- WebSearch: PyInstaller exclude PySide6 modules — list of safe-to-exclude modules
- WebSearch: Pillow ICO multi-resolution — sizes parameter behavior

### Tertiary (LOW confidence)
- A4 (no QML usage): Based on codebase inspection showing QWidget-only code; LOW risk of being wrong

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified installed (except PyInstaller which needs install)
- Architecture: HIGH — patterns are standard PyInstaller + Qt patterns
- Pitfalls: HIGH — common issues well-documented in PyInstaller community

**Research date:** 2026-05-10
**Valid until:** 2026-06-10 (stable — PyInstaller and PySide6 patterns don't change frequently)
