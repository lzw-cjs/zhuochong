<!-- GSD:project-start source:PROJECT.md -->
## Project

**Smart Desktop Pet (智能桌面宠物)**

A pixel-art desktop pet application built with Python + PyQt/PySide. The pet lives on the user's desktop as a small animated creature that they can interact with, manage schedules through, and receive reminders from. Think of it as a modern take on classic desktop pets (like Shimeji or the old Windows BonziBuddy), but with practical utility built in.

**Core Value:** A pixel-art pet that is both charming to interact with AND practically useful for schedule management. If either half fails — ugly animations or broken reminders — the whole thing falls apart.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## 1. GUI Framework: PySide6 vs PyQt6 vs tkinter
### Recommendation: PySide6
| Criteria | PySide6 | PyQt6 | tkinter |
|---|---|---|---|
| License | LGPL (permissive) | GPL / Commercial | PSF (permissive) |
| Transparent frameless windows | Full support | Full support | Limited, hacky |
| Animation support | Qt Animation Framework | Qt Animation Framework | Canvas-based, primitive |
| Active development | Qt Company (6.8.x / 6.9.x) | Riverbank Computing | stdlib (minimal updates) |
| Python 3.13 support | Yes (6.8.0+) | Yes | Yes (stdlib) |
| Documentation | Excellent (Qt docs) | Excellent | Basic |
### Transparent Frameless Window Implementation
### Why PySide6 over PyQt6
- **LGPL license** allows proprietary distribution without purchasing a commercial license. PyQt6 requires GPL or a paid license.
- PySide6 is maintained by the Qt Company itself -- aligned with Qt release cadence.
- Identical API surface to PyQt6 (both wrap Qt 6). Migration between them is trivial.
### Why PySide6 over tkinter
- tkinter cannot achieve true per-pixel transparency with frameless windows on Windows without platform-specific hacks (e.g., `-transparentcolor` only supports one color, not alpha).
- tkinter has no hardware-accelerated animation support.
- Qt provides `QPropertyAnimation`, `QTimeLine`, and `QPainter` for smooth, GPU-backed rendering.
### Known Issue: Qt 6.7+ Translucent Window Performance
- Set `Qt.WA_TranslucentBackground` after the window is shown, not in the constructor.
- Combine with `Qt.WA_NoSystemBackground`.
- Set environment variable `QSG_RHI_BACKEND=opengl` to force the OpenGL backend.
- If issues persist, pin to PySide6 6.6.x which uses the older rendering path.
## 2. Animation: Sprite Sheet vs GIF vs Lottie
### Recommendation: Sprite Sheet (primary) + GIF (fallback)
| Approach | Quality | Alpha Support | Dependencies | Control | Performance |
|---|---|---|---|---|---|
| **Sprite Sheet** | Raster, fixed res | Full 8-bit alpha | None (Qt built-in) | Full frame control | Excellent |
| **GIF (QMovie)** | 8-bit color (256) | 1-bit only (on/off) | None (Qt built-in) | Play/pause only | Excellent |
| **Lottie** | Vector, scalable | Full alpha | `pymated` or `rlottie` | Moderate | CPU-intensive |
### Sprite Sheet Approach (Primary)
- Zero additional dependencies.
- Full alpha transparency (crucial for non-rectangular pet shapes).
- Deterministic frame control -- easy to implement state machines (idle, walk, sleep, drag).
- Sprite sheets can include multiple animation states in a single file (grid layout).
- GPU-backed via `QPixmap` -- negligible CPU cost.
### GIF via QMovie (Fallback / Quick Prototyping)
- GIF only supports 1-bit transparency (fully opaque or fully transparent -- no soft edges).
- 256-color palette causes banding on gradients.
- Cannot pause at specific frames or synchronize with state changes.
### Lottie (Optional, for advanced effects)
- **`pymated`** -- PySide6-native Lottie player using `rlottie` under the hood. Renders Lottie JSON to `QPixmap` frames.
- **`python-rlottie`** -- Python bindings for Samsung's rlottie C library.
## 3. Audio: pygame.mixer vs QSoundEffect
### Recommendation: QSoundEffect
| Criteria | QSoundEffect | pygame.mixer |
|---|---|---|
| Dependencies | None (PySide6 built-in) | `pygame` (~6 MB) |
| Latency | Low (native platform audio) | Moderate (SDL subsystem) |
| Format support | WAV (primary), platform-dependent MP3 | WAV, MP3, OGG, FLAC |
| Initialization | Automatic with QApplication | Requires `pygame.mixer.init()` |
| API complexity | Simple (3 lines) | Moderate |
| Memory footprint | Minimal | ~20-30 MB SDL overhead |
### Implementation
# Usage
### Requirements
- Install: `pip install PySide6-Addons` (provides multimedia backends).
- On Windows: works out of the box.
- Audio files should be **WAV format** (16-bit PCM) for guaranteed compatibility.
- For music/background audio, consider `QMediaPlayer` (also in PySide6-Addons).
### Why QSoundEffect over pygame.mixer
- The application already depends on PySide6. Adding pygame solely for audio introduces ~6 MB of unnecessary binary size and an entire SDL subsystem.
- `QSoundEffect` is purpose-built for short, low-latency sound clips (exactly what notification sounds are).
- Avoids initialization conflicts between Qt's event loop and pygame's mixer thread.
## 4. Calendar / iCal Parsing
### Recommendation: `icalendar` + `recurring-ical-events`
| Library | Purpose | Maintenance | RFC Compliance |
|---|---|---|---|
| **`icalendar`** | Parse/create iCalendar (RFC 5545) | Active (collective/) | Full RFC 5545 |
| **`recurring-ical-events`** | Expand recurring events | Active | Wraps icalendar |
| `icalevents` | Simplified event extraction | Moderate | Partial |
| `vobject` | Alternative parser | Low maintenance | Partial |
### Implementation Pattern
# Usage: get today's events
### Key Best Practices
### Install
## 5. Packaging: Single-File .exe
### Recommendation: PyInstaller (primary) or Nuitka (production)
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
# Basic single-file build
# desktop_pet.spec
- Use `--windowed` to suppress the console window.
- Use `--add-data` to bundle assets (sprite sheets, sounds, .ics templates).
- Use `--icon` for a custom executable icon.
- The `.spec` file is generated on first run and should be version-controlled.
- On Windows, add `--uac-admin` only if needed (triggers UAC prompt).
### Nuitka (Production / Performance)
- True native compilation -- faster startup, lower memory usage.
- Fewer antivirus false positives (native code, not bundled bytecode).
- Smeraller output size with optimization flags.
- Better IP protection (code is compiled to C, not shipped as .pyc).
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
## 6. JSON Storage: Atomic Writes and Migration
### Recommendation: Atomic writes + schema versioning + `filelock`
### Atomic Write Pattern
- `os.replace()` is atomic on all platforms (Windows included) and will overwrite the target if it exists.
- `os.rename()` on Windows raises `FileExistsError` if the target exists.
### File Locking for Concurrent Access
### Schema Versioning and Migration
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
- You need to query across many records (e.g., thousands of calendar events).
- You need transactions and ACID guarantees.
- The data grows beyond what is comfortable to load entirely into memory.
### Recommended Libraries
# orjson is optional but 10-50x faster than stdlib json for large payloads
## Full Dependency Summary
# pyproject.toml [project.dependencies]
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
## Risk Assessment
| Risk | Likelihood | Mitigation |
|---|---|---|
| Qt translucent window rendering issues on Windows 11 | Medium | Pin Qt version; apply RHI workaround |
| PyInstaller antivirus false positives | Medium | Switch to Nuitka for distribution; code-sign the .exe |
| iCal parsing fails on non-standard files | Low-Medium | Wrap all parsing in try/except; validate with known test files |
| JSON corruption from unexpected shutdown | Low | Atomic write pattern (implemented above) |
| PySide6-Addons missing multimedia backend | Low | Test on clean Windows VM; bundle required DLLs |
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
