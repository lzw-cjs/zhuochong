---
description: "Detailed technology stack analysis and implementation patterns for Smart Desktop Pet"
globs: ["**/*.py", "**/*.spec", "**/pyproject.toml"]
---

# Technology Stack — Detailed Reference

## 1. GUI Framework: PySide6

**Decision:** PySide6 (LGPL, maintained by Qt Company, identical API to PyQt6).

### Transparent Frameless Window
- Set `Qt.WA_TranslucentBackground` **after** the window is shown, not in the constructor.
- Combine with `Qt.WA_NoSystemBackground`.
- Set env `QSG_RHI_BACKEND=opengl` to force OpenGL backend.
- If issues persist, pin to PySide6 6.6.x.

### Why not tkinter
- Cannot achieve true per-pixel transparency with frameless windows on Windows.
- No hardware-accelerated animation support.

## 2. Animation: Sprite Sheet (primary) + GIF (fallback)

| Approach | Quality | Alpha | Dependencies | Control | Perf |
|---|---|---|---|---|---|
| **Sprite Sheet** | Raster, fixed res | Full 8-bit alpha | None | Full frame control | Excellent |
| **GIF (QMovie)** | 8-bit color (256) | 1-bit only | None | Play/pause only | Excellent |
| **Lottie** | Vector, scalable | Full alpha | pymated/rlottie | Moderate | CPU-intensive |

### Sprite Sheet
- Zero additional dependencies, full alpha, deterministic frame control.
- GPU-backed via `QPixmap`.
- Grid layout supports multiple animation states in one file.

### GIF via QMovie
- 1-bit transparency (no soft edges), 256-color banding.
- Cannot pause at specific frames or sync with state changes.

### Lottie (optional, advanced effects)
- `pymated` — PySide6-native Lottie player via rlottie.
- `python-rlottie` — Python bindings for Samsung's rlottie.

## 3. Audio: QSoundEffect

| Criteria | QSoundEffect | pygame.mixer |
|---|---|---|
| Dependencies | None (PySide6 built-in) | pygame (~6 MB) |
| Latency | Low | Moderate |
| Format | WAV (primary) | WAV, MP3, OGG, FLAC |
| Init | Automatic | pygame.mixer.init() |

- **Requires:** `pip install PySide6-Addons` (multimedia backends).
- Audio files should be **WAV format** (16-bit PCM).
- For music/background, consider `QMediaPlayer` (also in PySide6-Addons).

## 4. Calendar / iCal Parsing

**Decision:** `icalendar` + `recurring-ical-events`

| Library | Purpose | Maintenance | RFC |
|---|---|---|---|
| icalendar | Parse/create (RFC 5545) | Active | Full |
| recurring-ical-events | Expand recurring events | Active | Wraps icalendar |

### Key Best Practices
- Always wrap parsing in try/except.
- Validate with known test .ics files.

## 5. Packaging

| Criteria | PyInstaller | Nuitka |
|---|---|---|
| Ease | Very easy | Moderate |
| Binary size | 50-200 MB | 30-100 MB |
| Startup | Slow (extract) | Fast (native) |
| Compile time | Seconds | Minutes to hours |
| AV false positives | Frequent | Rare |

### Recommendation
- **Dev/iteration:** No packaging (run directly)
- **Internal testing:** PyInstaller (`--onefile`)
- **Production:** Nuitka (`--standalone --onefile`)

### PyInstaller
```
pyinstaller --onefile --windowed --add-data "assets;assets" main.py
```
- Use `--windowed` to suppress console.
- Use `--add-data` for assets (sprite sheets, sounds, .ics).
- Use `--icon` for custom exe icon.

### Both Packagers: Asset Bundling
- Use `sys._MEIPASS` (PyInstaller) or `os.path.dirname(__file__)` (Nuitka) for runtime asset path.

## 6. JSON Storage

**Decision:** Atomic writes + schema versioning + `filelock`

### Atomic Write Pattern
- `os.replace()` is atomic on all platforms (including Windows).
- `os.rename()` on Windows raises `FileExistsError` if target exists.

### Best Practices
| Practice | Why |
|---|---|
| Write-to-temp + os.replace() | Prevents corruption on crash |
| os.fsync() before rename | Flush to disk, not just OS cache |
| filelock | Cross-process safety |
| _schema_version field | Safe incremental migrations |
| Backup before migration | .bak before overwrite |
| encoding="utf-8" explicitly | Avoid platform defaults |
| ensure_ascii=False | Preserve CJK/emoji |

### When to use SQLite instead
- Thousands of records, need ACID, or data too large for memory.

## 7. Dependencies

```
PySide6>=6.8.0
PySide6-Addons
icalendar>=5.0
recurring-ical-events>=3.0
filelock>=3.13
```

### Version Matrix
| Dependency | Min | Recommended | Notes |
|---|---|---|---|
| Python | 3.11 | 3.12 or 3.13 | Better errors in 3.12+ |
| PySide6 | 6.8.0 | 6.8.x | 6.7.x has RHI issues |
| icalendar | 5.0 | 5.0+ | Active maintenance |
| recurring-ical-events | 3.0 | 3.0+ | RRULE expansion |
| filelock | 3.13 | latest | Cross-platform |
| PyInstaller | 6.0 | 6.x | Dev/test builds |
| Nuitka | 2.0 | 2.x | Production builds |

## 8. Risk Assessment

| Risk | Likelihood | Mitigation |
|---|---|---|
| Qt translucent window on Win11 | Medium | Pin Qt version; RHI workaround |
| PyInstaller AV false positives | Medium | Switch to Nuitka; code-sign |
| iCal parsing on non-standard files | Low-Med | try/except; validate with test files |
| JSON corruption from shutdown | Low | Atomic write pattern |
| PySide6-Addons missing backend | Low | Test on clean VM; bundle DLLs |
