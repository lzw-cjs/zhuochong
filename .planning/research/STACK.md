# Desktop Pet Application -- Technology Stack Research

> Research date: 2026-05-09
> Target: Python + PySide6 desktop pet application on Windows

---

## 1. GUI Framework: PySide6 vs PyQt6 vs tkinter

### Recommendation: PySide6

**Confidence: HIGH**

| Criteria | PySide6 | PyQt6 | tkinter |
|---|---|---|---|
| License | LGPL (permissive) | GPL / Commercial | PSF (permissive) |
| Transparent frameless windows | Full support | Full support | Limited, hacky |
| Animation support | Qt Animation Framework | Qt Animation Framework | Canvas-based, primitive |
| Active development | Qt Company (6.8.x / 6.9.x) | Riverbank Computing | stdlib (minimal updates) |
| Python 3.13 support | Yes (6.8.0+) | Yes | Yes (stdlib) |
| Documentation | Excellent (Qt docs) | Excellent | Basic |

### Transparent Frameless Window Implementation

The standard pattern for PySide6 desktop pet windows:

```python
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt

class DesktopPet(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool                    # hides from taskbar
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
```

### Why PySide6 over PyQt6

- **LGPL license** allows proprietary distribution without purchasing a commercial license. PyQt6 requires GPL or a paid license.
- PySide6 is maintained by the Qt Company itself -- aligned with Qt release cadence.
- Identical API surface to PyQt6 (both wrap Qt 6). Migration between them is trivial.

### Why PySide6 over tkinter

- tkinter cannot achieve true per-pixel transparency with frameless windows on Windows without platform-specific hacks (e.g., `-transparentcolor` only supports one color, not alpha).
- tkinter has no hardware-accelerated animation support.
- Qt provides `QPropertyAnimation`, `QTimeLine`, and `QPainter` for smooth, GPU-backed rendering.

### Known Issue: Qt 6.7+ Translucent Window Performance

Qt 6.7 introduced a new RHI (Rendering Hardware Interface) rendering pipeline that can cause flickering or high CPU usage with `WA_TranslucentBackground` on Windows 11.

**Workarounds:**
- Set `Qt.WA_TranslucentBackground` after the window is shown, not in the constructor.
- Combine with `Qt.WA_NoSystemBackground`.
- Set environment variable `QSG_RHI_BACKEND=opengl` to force the OpenGL backend.
- If issues persist, pin to PySide6 6.6.x which uses the older rendering path.

**Recommended version:** `PySide6>=6.8.0,<6.10` -- includes Python 3.13 support and the most mature translucent window handling.

---

## 2. Animation: Sprite Sheet vs GIF vs Lottie

### Recommendation: Sprite Sheet (primary) + GIF (fallback)

**Confidence: HIGH for sprite sheets, MEDIUM for Lottie**

| Approach | Quality | Alpha Support | Dependencies | Control | Performance |
|---|---|---|---|---|---|
| **Sprite Sheet** | Raster, fixed res | Full 8-bit alpha | None (Qt built-in) | Full frame control | Excellent |
| **GIF (QMovie)** | 8-bit color (256) | 1-bit only (on/off) | None (Qt built-in) | Play/pause only | Excellent |
| **Lottie** | Vector, scalable | Full alpha | `pymated` or `rlottie` | Moderate | CPU-intensive |

### Sprite Sheet Approach (Primary)

Use `QPixmap` + `QTimer` + custom `paintEvent()`:

```python
class AnimatedPet(QWidget):
    def __init__(self, sprite_sheet_path, frame_width, frame_height):
        super().__init__()
        self.sprite = QPixmap(sprite_sheet_path)
        self.frame_w = frame_width
        self.frame_h = frame_height
        self.current_frame = 0
        self.total_frames = self.sprite.width() // frame_width

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.advance_frame)
        self.timer.start(100)  # 10 FPS

    def advance_frame(self):
        self.current_frame = (self.current_frame + 1) % self.total_frames
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        x = self.current_frame * self.frame_w
        source = QRect(x, 0, self.frame_w, self.frame_h)
        target = QRect(0, 0, self.frame_w, self.frame_h)
        painter.drawPixmap(target, self.sprite, source)
```

**Why sprite sheets win:**
- Zero additional dependencies.
- Full alpha transparency (crucial for non-rectangular pet shapes).
- Deterministic frame control -- easy to implement state machines (idle, walk, sleep, drag).
- Sprite sheets can include multiple animation states in a single file (grid layout).
- GPU-backed via `QPixmap` -- negligible CPU cost.

### GIF via QMovie (Fallback / Quick Prototyping)

```python
from PySide6.QtGui import QMovie
from PySide6.QtWidgets import QLabel

label = QLabel()
movie = QMovie("pet_idle.gif")
label.setMovie(movie)
movie.start()
```

**Limitations:**
- GIF only supports 1-bit transparency (fully opaque or fully transparent -- no soft edges).
- 256-color palette causes banding on gradients.
- Cannot pause at specific frames or synchronize with state changes.

### Lottie (Optional, for advanced effects)

Qt 6.7+ has growing Lottie support in Qt Quick/QML. For PySide6 widgets (not QML), the options are:

- **`pymated`** -- PySide6-native Lottie player using `rlottie` under the hood. Renders Lottie JSON to `QPixmap` frames.
- **`python-rlottie`** -- Python bindings for Samsung's rlottie C library.

**Verdict:** Lottie is promising but adds complexity and dependencies. Use sprite sheets for the character animation itself. Reserve Lottie for UI effects (e.g., notification bubbles, sparkle effects) if needed later.

---

## 3. Audio: pygame.mixer vs QSoundEffect

### Recommendation: QSoundEffect

**Confidence: HIGH**

| Criteria | QSoundEffect | pygame.mixer |
|---|---|---|
| Dependencies | None (PySide6 built-in) | `pygame` (~6 MB) |
| Latency | Low (native platform audio) | Moderate (SDL subsystem) |
| Format support | WAV (primary), platform-dependent MP3 | WAV, MP3, OGG, FLAC |
| Initialization | Automatic with QApplication | Requires `pygame.mixer.init()` |
| API complexity | Simple (3 lines) | Moderate |
| Memory footprint | Minimal | ~20-30 MB SDL overhead |

### Implementation

```python
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtCore import QUrl

class SoundManager:
    def __init__(self):
        self.effects = {}

    def load(self, name: str, path: str):
        effect = QSoundEffect()
        effect.setSource(QUrl.fromLocalFile(path))
        effect.setVolume(0.7)
        self.effects[name] = effect

    def play(self, name: str):
        if name in self.effects:
            self.effects[name].play()

# Usage
sounds = SoundManager()
sounds.load("notification", "assets/sounds/notify.wav")
sounds.play("notification")
```

### Requirements

- Install: `pip install PySide6-Addons` (provides multimedia backends).
- On Windows: works out of the box.
- Audio files should be **WAV format** (16-bit PCM) for guaranteed compatibility.
- For music/background audio, consider `QMediaPlayer` (also in PySide6-Addons).

### Why QSoundEffect over pygame.mixer

- The application already depends on PySide6. Adding pygame solely for audio introduces ~6 MB of unnecessary binary size and an entire SDL subsystem.
- `QSoundEffect` is purpose-built for short, low-latency sound clips (exactly what notification sounds are).
- Avoids initialization conflicts between Qt's event loop and pygame's mixer thread.

---

## 4. Calendar / iCal Parsing

### Recommendation: `icalendar` + `recurring-ical-events`

**Confidence: HIGH**

| Library | Purpose | Maintenance | RFC Compliance |
|---|---|---|---|
| **`icalendar`** | Parse/create iCalendar (RFC 5545) | Active (collective/) | Full RFC 5545 |
| **`recurring-ical-events`** | Expand recurring events | Active | Wraps icalendar |
| `icalevents` | Simplified event extraction | Moderate | Partial |
| `vobject` | Alternative parser | Low maintenance | Partial |

### Implementation Pattern

```python
from icalendar import Calendar
from datetime import date, datetime, timedelta
import recurring_ical_events

def load_events(ics_path: str, start: date, end: date) -> list[dict]:
    """Load all events (including recurring) between two dates."""
    with open(ics_path, "rb") as f:
        cal = Calendar.from_ical(f.read())

    events = recurring_ical_events.of(cal).between(start, end)
    result = []
    for event in events:
        dtstart = event.get("dtstart").dt
        result.append({
            "summary": str(event.get("summary", "")),
            "start": dtstart,
            "end": event.get("dtend").dt if event.get("dtend") else None,
            "description": str(event.get("description", "")),
        })
    return result

# Usage: get today's events
today = date.today()
events = load_events("my_calendar.ics", today, today + timedelta(days=1))
```

### Key Best Practices

1. **Always read `.ics` files in binary mode** (`"rb"`) -- `Calendar.from_ical()` expects bytes.
2. **Use `zoneinfo.ZoneInfo`** (Python 3.9+ stdlib) for timezone handling, not `pytz`.
3. **Handle `vDDDTypes`** -- `dtstart.dt` can be either `datetime` or `date` depending on the event. Check with `isinstance()`.
4. **Wrap parsing in try/except** -- real-world `.ics` files from Google Calendar and Outlook often have non-standard quirks.
5. **Cache parsed results** -- parsing large calendars is expensive. Cache with a file mtime check.
6. **EXDATE handling** -- `recurring-ical-events` handles exception dates automatically, which is a major reason to use it over manual `dateutil.rrule` expansion.

### Install

```bash
pip install icalendar recurring-ical-events
```

---

## 5. Packaging: Single-File .exe

### Recommendation: PyInstaller (primary) or Nuitka (production)

**Confidence: HIGH**

| Criteria | PyInstaller | Nuitka | cx_Freeze |
|---|---|---|---|
| Ease of use | Very easy (`--onefile`) | Moderate (long compile) | Moderate (setup.py) |
| Binary size | 50-200 MB | 30-100 MB | 50-150 MB |
| Startup time | Slow (extract + interpret) | Fast (native code) | Slow (similar to PyInstaller) |
| Runtime speed | Same as Python | 5-300% faster | Same as Python |
| Compile time | Seconds | Minutes to hours | Seconds |
| Antivirus false positives | Frequent | Rare | Occasional |
| Windows support | Excellent | Excellent | Good |
| Python 3.13 support | Yes | Yes (2.x) | Yes |

### PyInstaller (Quick and Simple)

```bash
# Basic single-file build
pyinstaller --onefile --windowed \
    --name "DesktopPet" \
    --icon assets/icon.ico \
    --add-data "assets;assets" \
    main.py
```

**Spec file for reproducible builds:**

```python
# desktop_pet.spec
a = Analysis(
    ['main.py'],
    datas=[('assets/**/*', 'assets')],
    hiddenimports=['PySide6.QtMultimedia'],
    ...
)
```

**Tips:**
- Use `--windowed` to suppress the console window.
- Use `--add-data` to bundle assets (sprite sheets, sounds, .ics templates).
- Use `--icon` for a custom executable icon.
- The `.spec` file is generated on first run and should be version-controlled.
- On Windows, add `--uac-admin` only if needed (triggers UAC prompt).

### Nuitka (Production / Performance)

```bash
nuitka --standalone --onefile \
    --enable-plugin=pyside6 \
    --include-data-dir=assets=assets \
    --windows-icon-from-ico=assets/icon.ico \
    --windows-console-mode=disable \
    main.py
```

**Why consider Nuitka:**
- True native compilation -- faster startup, lower memory usage.
- Fewer antivirus false positives (native code, not bundled bytecode).
- Smeraller output size with optimization flags.
- Better IP protection (code is compiled to C, not shipped as .pyc).

**Why it might not be worth it for a desktop pet:**
- Compile times of 10-60 minutes for each build.
- Debugging compiled code is harder.
- PySide6 plugin support in Nuitka has improved but can still have edge cases.

### Recommendation

| Phase | Packager |
|---|---|
| Development / iteration | No packaging (run directly) |
| Internal testing / sharing | PyInstaller (`--onefile`) |
| Production release | Nuitka (`--standalone --onefile`) |

### Both Packagers: Asset Bundling

A critical pattern for both tools -- resolve asset paths at runtime:

```python
import sys
from pathlib import Path

def get_asset_path(relative: str) -> Path:
    """Resolve asset path for both dev and packaged modes."""
    if getattr(sys, 'frozen', False):
        # Running as packaged executable
        base = Path(sys._MEIPASS)  # PyInstaller temp dir
    else:
        # Running in development
        base = Path(__file__).parent
    return base / relative
```

---

## 6. JSON Storage: Atomic Writes and Migration

### Recommendation: Atomic writes + schema versioning + `filelock`

**Confidence: HIGH**

### Atomic Write Pattern

The write-to-temp-then-rename pattern prevents data corruption on crash or power loss:

```python
import json
import os
import tempfile
from pathlib import Path

def atomic_write_json(filepath: Path, data: dict) -> None:
    """Write JSON atomically using temp file + os.replace()."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w",
        dir=filepath.parent,
        suffix=".tmp",
        delete=False,
        encoding="utf-8",
    ) as tmp:
        json.dump(data, tmp, indent=2, ensure_ascii=False)
        tmp.flush()
        os.fsync(tmp.fileno())  # ensure data hits disk
        tmp_name = tmp.name

    os.replace(tmp_name, filepath)  # atomic on same filesystem
```

**Why `os.replace()` and not `os.rename()`:**
- `os.replace()` is atomic on all platforms (Windows included) and will overwrite the target if it exists.
- `os.rename()` on Windows raises `FileExistsError` if the target exists.

### File Locking for Concurrent Access

If multiple processes might access the config (e.g., main app + settings dialog):

```python
import filelock
import json

def safe_write_json(filepath: Path, data: dict) -> None:
    lock = filelock.FileLock(str(filepath) + ".lock", timeout=10)
    with lock:
        atomic_write_json(filepath, data)

def safe_read_json(filepath: Path) -> dict:
    lock = filelock.FileLock(str(filepath) + ".lock", timeout=10)
    with lock:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
```

### Schema Versioning and Migration

Embed a `_schema_version` field in every stored JSON file:

```python
from pathlib import Path
from typing import Callable
import json
import shutil

class JsonStore:
    SCHEMA_VERSION_KEY = "_schema_version"
    CURRENT_VERSION = 3

    MIGRATIONS: dict[int, Callable[[dict], dict]] = {
        0: _migrate_v0_to_v1,
        1: _migrate_v1_to_v2,
        2: _migrate_v2_to_v3,
    }

    def __init__(self, filepath: Path, defaults: dict | None = None):
        self.filepath = Path(filepath)
        self.defaults = defaults or {}
        self._data = self._load()

    def _load(self) -> dict:
        if not self.filepath.exists():
            data = {**self.defaults, self.SCHEMA_VERSION_KEY: self.CURRENT_VERSION}
            atomic_write_json(self.filepath, data)
            return data

        with open(self.filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        version = data.get(self.SCHEMA_VERSION_KEY, 0)

        if version < self.CURRENT_VERSION:
            # Backup before migration
            backup = self.filepath.with_suffix(f".v{version}.bak.json")
            shutil.copy2(self.filepath, backup)

            while version < self.CURRENT_VERSION:
                migration_fn = self.MIGRATIONS.get(version)
                if migration_fn:
                    data = migration_fn(data)
                version += 1

            data[self.SCHEMA_VERSION_KEY] = self.CURRENT_VERSION
            atomic_write_json(self.filepath, data)

        return data

    def save(self) -> None:
        atomic_write_json(self.filepath, self._data)

    def __getitem__(self, key: str):
        return self._data[key]

    def __setitem__(self, key: str, value):
        self._data[key] = value
```

### Best Practices Summary

| Practice | Why |
|---|---|
| Write-to-temp + `os.replace()` | Prevents corruption on crash/power loss |
| `os.fsync()` before rename | Ensures data is flushed to disk, not just OS cache |
| `filelock` for cross-process safety | Prevents concurrent write corruption |
| `_schema_version` field | Enables safe incremental schema migrations |
| Backup before migration | Keep `.bak` file before overwriting in case migration has bugs |
| `encoding="utf-8"` explicitly | Avoids platform-default encoding issues |
| `ensure_ascii=False` | Preserves Unicode characters (important for CJK text, emoji) |

### When to Consider SQLite Instead

JSON files work well for small configuration and state (<1 MB). Consider migrating to SQLite if:
- You need to query across many records (e.g., thousands of calendar events).
- You need transactions and ACID guarantees.
- The data grows beyond what is comfortable to load entirely into memory.

For a desktop pet application, JSON is the right choice for settings and small state files.

### Recommended Libraries

```bash
pip install filelock    # cross-platform file locking
# orjson is optional but 10-50x faster than stdlib json for large payloads
pip install orjson      # drop-in replacement: orjson.dumps() / orjson.loads()
```

---

## Full Dependency Summary

```toml
# pyproject.toml [project.dependencies]
[project]
name = "desktop-pet"
requires-python = ">=3.11"
dependencies = [
    "PySide6>=6.8.0,<6.10",
    "PySide6-Addons>=6.8.0,<6.10",   # multimedia backends
    "icalendar>=5.0",
    "recurring-ical-events>=3.0",
    "filelock>=3.13",
]

[project.optional-dependencies]
dev = [
    "pyinstaller>=6.0",
    "nuitka>=2.0",
]
perf = [
    "orjson>=3.9",
]
```

### Version Matrix (tested/recommended)

| Dependency | Minimum Version | Recommended Version | Notes |
|---|---|---|---|
| Python | 3.11 | 3.12 or 3.13 | 3.12+ for better error messages |
| PySide6 | 6.8.0 | 6.8.x (stable) | 6.7.x has RHI rendering issues |
| icalendar | 5.0 | 5.0+ | Active maintenance |
| recurring-ical-events | 3.0 | 3.0+ | Required for RRULE expansion |
| filelock | 3.13 | latest | Cross-platform locking |
| PyInstaller | 6.0 | 6.x | For dev/test builds |
| Nuitka | 2.0 | 2.x | For production builds |

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|---|---|---|
| Qt translucent window rendering issues on Windows 11 | Medium | Pin Qt version; apply RHI workaround |
| PyInstaller antivirus false positives | Medium | Switch to Nuitka for distribution; code-sign the .exe |
| iCal parsing fails on non-standard files | Low-Medium | Wrap all parsing in try/except; validate with known test files |
| JSON corruption from unexpected shutdown | Low | Atomic write pattern (implemented above) |
| PySide6-Addons missing multimedia backend | Low | Test on clean Windows VM; bundle required DLLs |
