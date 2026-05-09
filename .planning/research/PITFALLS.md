# Desktop Pet Application -- Common Pitfalls (Python + PySide6 / Windows)

Research compiled for the "zhuochong" desktop pet project.
Last updated: 2026-05-09

---

## 1. Qt Transparent Window Issues

### The Problem

Transparent, frameless windows are the foundation of any desktop pet. On Windows this
is deceptively hard to get right. Qt's `WA_TranslucentBackground` interacts badly with
several Windows subsystems.

### Warning Signs

- Pet appears with a black or white background rectangle instead of being transparent.
- Pet renders correctly on the primary monitor but shows artifacts or a black box on
  secondary monitors with different DPI scaling values.
- After Windows display scaling changes (e.g., connecting to an external projector),
  the pet's hit region and visual position become misaligned.
- The pet's window appears in the Alt-Tab list or steals focus from other applications.
- On Windows 11, rounded corners of the frameless window leak through as a visible
  border.
- The taskbar "peek" thumbnail shows a blank or distorted image of the pet window.

### Prevention Strategy

1. **Set the correct window flags at construction time.** Combine
   `Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool`. The `Qt.Tool` flag
   prevents the window from appearing in the taskbar and Alt-Tab. Do NOT add flags
   after `show()` -- set them before.

2. **DPI awareness must be set before any Qt object is created.** Call
   `QApplication.setHighDpiScaleFactorRoundingPolicy(
   Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)` and set the Windows DPI
   awareness manifest (`<dpiAwareness>PerMonitorV2</dpiAwareness>`) in the
   application manifest or via `ctypes.windll.shcore.SetProcessDpiAwareness(2)` at the
   very top of `main.py`, before `QApplication()` is constructed.

3. **Handle `screenChanged` and `logicalDotsPerInchChanged` signals** on
   `QGuiApplication` to reposition and rescale the pet when the user drags it across
   monitors or changes display scaling in Windows Settings.

4. **Use `setAttribute(Qt.WA_TranslucentBackground)` AND paint the background with
   `QColor(0, 0, 0, 0)`** in the paint event. Just setting the attribute is not always
   sufficient on all Windows versions.

5. **For hit-testing** (clicking through transparent areas), override
   `hitRegion()` or use a `QRegion` mask that only covers opaque pixels. Do not rely
   on `WA_TransparentForMouseEvents` for the main pet window -- it will break drag.

6. **Windows 11 rounded corners:** Set `Qt.FramelessWindowHint` early and avoid
   `Qt.Popup` for the main window. If rounded corners leak through, call
   `DwmSetWindowAttribute` via ctypes to disable `DWMWA_WINDOW_CORNER_PREFERENCE`.

### Phase to Address

**Phase 1 (Foundation / Window Setup).** This must be the first thing that works.
Build a minimal transparent window that renders correctly on multi-monitor setups
before writing any game logic.

---

## 2. Animation Performance

### The Problem

Desktop pets typically cycle through sprite frames. Naive implementations load every
frame as a `QPixmap`, paint them every tick, and quickly consume hundreds of megabytes
of RAM or drop frames on lower-end machines.

### Warning Signs

- Memory usage climbs steadily and never plateaus -- classic `QPixmap` leak.
- Animation stutters or drops below 15 FPS, especially when other windows are being
  dragged over the pet.
- Application freezes for 200-500ms when switching to a new animation state (loading
  sprites from disk synchronously).
- On integrated GPUs (Intel UHD 620 etc.), continuous repaints cause 10-20% CPU usage
  at idle, draining laptop batteries.
- `QPixmap: It is not safe to use pixmaps outside the GUI thread` warnings in
  console.

### Prevention Strategy

1. **Use a sprite atlas (spritesheet) rather than individual files.** One large
   `QPixmap` with all frames laid out in a grid, then use `QPixmap.copy(QRect)` to
   extract frames. This reduces file I/O and avoids creating thousands of small
   `QPixmap` objects.

2. **Lazy-load and cache.** Only load the current animation state's sprites. When
   switching states, load asynchronously in a `QThread` (or `QRunnable` + thread pool)
   and emit a signal when ready. Never call `QPixmap()` constructor from a non-GUI
   thread -- instead, load raw bytes in the background thread and construct the pixmap
   on the main thread.

3. **Implement a frame budget.** Use `QTimer` with a 33ms interval (30 FPS) or 66ms
   (15 FPS) for idle animations. Do NOT run at 60 FPS for a desktop pet -- it wastes
   CPU for no visual benefit. Only increase frame rate during active interactions.

4. **Paint only what changed.** Call `update(QRect)` with the dirty region instead of
   `update()` (full repaint). Override `paintEvent` to only draw the current sprite
   frame, not the entire background.

5. **Pool `QPixmap` objects.** Keep a small cache (e.g., 10-20 frames) and reuse them.
   When a `QPixmap` is no longer needed, call `.detach()` or let it go out of scope
   explicitly. PySide6's reference counting can keep pixmaps alive longer than
   expected if Python holds a reference cycle.

6. **Profile with `memory_profiler` and `QElapsedTimer`.** Measure actual frame
   times and memory usage early. Do not assume "it runs fine on my machine" -- test on
   a machine with 4GB RAM and integrated graphics.

### Phase to Address

**Phase 2 (Animation Engine).** Build the animation system with performance budgets
from the start. Retrofitting a performant renderer onto a naive implementation is
significantly harder than building it right.

---

## 3. PyInstaller Packaging

### The Problem

PySide6 applications have a large dependency tree that PyInstaller often fails to
fully include. The resulting executable may crash at runtime with `ModuleNotFoundError`,
trigger antivirus warnings, or fail to find bundled data files.

### Warning Signs

- `ModuleNotFoundError: No module named 'PySide6.QtSvg'` or similar -- PySide6
  plugins (platforms, imageformats, styles) are not automatically collected.
- Application works in development but crashes in the bundled `.exe` with
  `FileNotFoundError` when loading sprites, sounds, or config files.
- Windows Defender, 360 Security, or other antivirus software flags the `.exe` as
  suspicious or deletes it silently.
- The bundled folder is 300+ MB even though the application is simple.
- `--onefile` mode takes 30+ seconds to cold-start because it extracts to a temp
  directory every launch.
- Path `sys._MEIPASS` works in onefile mode but not in `--onedir` mode, or vice
  versa.

### Prevention Strategy

1. **Add hidden imports explicitly.** Create a `hook-PySide6.py` or use
   `--hidden-import` for: `PySide6.QtSvg`, `PySide6.QtSvgWidgets`,
   `PySide6.QtOpenGL`, `PySide6.QtMultimedia`, `PySide6.QtSvg`, and the platform
   plugins. Use `--collect-all PySide6` as a starting point, then trim.

2. **Collect Qt plugins with `--collect-data PySide6`** (PyInstaller 5.x+) or
   manually copy `<site-packages>/PySide6/plugins/` to the output. Without this,
   `platforms/qwindows.dll` will be missing and the app will crash with "This
   application failed to start because no Qt platform plugin could be initialized."

3. **Use a resource path helper function:**

   ```python
   import sys, os
   def resource_path(relative_path):
       base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
       return os.path.join(base, relative_path)
   ```

   Always load assets through this function. Test in both `--onefile` and `--onedir`
   modes.

4. **To reduce antivirus false positives:**
   - Code-sign the executable (even a self-signed cert helps with SmartScreen).
   - Do NOT use `--onefile` -- use `--onedir` and zip the folder instead. Single-file
     executables that extract to temp are the #1 false-positive trigger.
   - Submit the `.exe` to Microsoft's malware analysis portal for whitelisting.
   - Avoid `ctypes` calls to `kernel32.dll` or `user32.dll` in code that runs at
     startup (AV heuristics flag this).
   - Use UPX cautiously -- some AV engines flag UPX-packed binaries.

5. **Reduce bundle size:** exclude unused PySide6 modules with
   `--exclude-module PySide6.QtWebEngine`, `--exclude-module PySide6.Qt3D`, etc.
   PySide6's WebEngine alone adds ~150 MB.

6. **Use `--noconsole` (or `--windowed`) for the release build** but keep
   `--console` during development to see Python tracebacks. Wrap the entry point in
   a try/except that writes to a log file so crashes in the no-console build are
   still diagnosable.

### Phase to Address

**Phase 4 (Packaging / Distribution).** However, the resource path helper should be
introduced in Phase 1 so all asset loading uses it from the start. Do not wait until
packaging to retrofit paths.

---

## 4. JSON Storage

### The Problem

Desktop pets commonly use JSON files for user settings, pet state, and save data.
JSON has no built-in concurrency or corruption protection.

### Warning Signs

- Settings file becomes empty (0 bytes) after a crash or power loss during write.
- `json.JSONDecodeError` when loading settings after the application was force-killed.
- Two instances of the application (or the app + an updater) write to the same JSON
  file simultaneously, producing truncated/corrupt output.
- After adding a new field to the settings schema, old settings files crash the app
  with `KeyError`.
- The settings file grows unboundedly because old data is never cleaned up (e.g., a
  log of every interaction stored in the same JSON).

### Prevention Strategy

1. **Atomic writes.** Write to a temporary file first, then rename over the original.
   On Windows, use `os.replace()` which is atomic on NTFS:

   ```python
   import json, os, tempfile

   def save_json(path, data):
       dir_name = os.path.dirname(path) or "."
       fd, tmp = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
       try:
           with os.fdopen(fd, "w", encoding="utf-8") as f:
               json.dump(data, f, ensure_ascii=False, indent=2)
           os.replace(tmp, path)
       except:
           os.unlink(tmp)
           raise
   ```

2. **Keep a backup.** Before writing, copy the current file to `settings.json.bak`.
   On load, if the primary file is corrupt, fall back to the backup. This two-file
   rotation costs almost nothing and prevents data loss.

3. **Schema versioning.** Include a `"schema_version": N` field in every JSON file.
   On load, check the version and run migrations:

   ```python
   def load_and_migrate(path):
       data = load_json(path)
       ver = data.get("schema_version", 1)
       if ver < 2:
           data = migrate_v1_to_v2(data)
       if ver < 3:
           data = migrate_v2_to_v3(data)
       return data
   ```

4. **Use file locking for multi-process safety.** The `portalocker` library (or
   `msvcrt.locking` on Windows) can prevent concurrent writes. However, for a desktop
   pet, the simpler approach is to use a lockfile (`settings.json.lock`) and check for
   stale locks on startup.

5. **Validate on load.** Use `pydantic` or a simple schema check to ensure required
   fields exist and have correct types. Never assume the JSON is well-formed.

6. **Separate concerns.** Use different files for different data:
   - `config.json` -- user settings (small, rarely written)
   - `state.json` -- pet state (written frequently)
   - `history.json` -- interaction log (append-only, can grow)

### Phase to Address

**Phase 1 (Foundation).** Implement the atomic write + backup + versioning pattern
before any feature writes to disk. Retrofitting this after data loss incidents is
painful.

---

## 5. Reminder / Timer Issues

### The Problem

Desktop pets often include reminder or timer features ("stand up and stretch",
"drink water"). System sleep, timezone changes, and clock adjustments break naive
timekeeping.

### Warning Signs

- After the laptop wakes from sleep, a 30-minute reminder fires instantly because
  the elapsed time was measured by wall-clock difference.
- The reminder fires at the wrong local time after a timezone change (e.g., user
  travels or Windows adjusts for DST).
- Timers accumulate when the application runs for days without restart, causing
  multiple firings of the same reminder.
- `QTimer` with a 1-minute interval drifts over hours -- Qt timers are not
  guaranteed to be precise over long periods.
- The reminder sound plays even when the system is in "Focus Assist" / "Do Not
  Disturb" mode.

### Prevention Strategy

1. **Use absolute timestamps, not relative intervals.** Store the next reminder time
   as a Unix timestamp or ISO-8601 string. On each tick (e.g., every 30 seconds),
   compare `now` against the stored next-fire time. This handles sleep/wake correctly
   because the comparison catches up automatically.

   ```python
   from datetime import datetime, timezone

   def check_reminder(stored_next_fire_iso: str) -> bool:
       next_fire = datetime.fromisoformat(stored_next_fire_iso)
       return datetime.now(next_fire.tzinfo) >= next_fire
   ```

2. **Always work in UTC internally.** Store all times in UTC. Convert to local time
   only for display. This eliminates timezone and DST bugs.

3. **Detect sleep/wake.** Listen for Windows power notifications via
   `QAbstractNativeEventFilter` or `ctypes.windll.kernel32` power broadcast messages.
   After wake, recalculate all timers based on the current time rather than trusting
   accumulated elapsed time.

4. **Respect Windows Focus Assist.** Query the registry key
   `HKCU\Software\Microsoft\Windows\CurrentVersion\CloudStore\...` or use the
   `QuietHours` API (Windows 10 1809+) to detect Focus Assist state. Suppress
   notification sounds when active.

5. **Deduplicate reminders.** Before firing, check if the reminder was already shown
   (store a `last_fired` timestamp). This prevents double-firing after rapid
   sleep/wake cycles.

6. **Use `QTimer.singleShot()` for one-shot reminders** instead of interval-based
   timers that need to be manually stopped and restarted.

### Phase to Address

**Phase 3 (Features / Reminders).** But store all timestamps in UTC from Phase 1
onward -- retrofitting UTC-only storage is a large, error-prone migration.

---

## 6. Desktop Integration

### The Problem

A desktop pet must coexist with every other window on the user's system. Always-on-top
behavior, fullscreen applications, multi-desktop (virtual desktops), and system tray
interactions all create edge cases.

### Warning Signs

- Pet stays on top of fullscreen games or video players, blocking user interaction.
- Pet disappears when the user switches virtual desktops (Win+Tab on Windows 10/11).
- System tray icon does not appear, or appears as a blank/generic icon.
- Right-clicking the tray icon causes the context menu to appear behind the pet
  window.
- Pet interferes with screen-sharing in Teams/Zoom/Discord (captures attention or
  appears in shared screen when user doesn't want it to).
- `WindowStaysOnTopHint` conflicts with other always-on-top windows (e.g., Task
  Manager, Sticky Notes).

### Prevention Strategy

1. **Detect fullscreen applications.** Periodically (every 2-5 seconds) check if the
   foreground window is fullscreen. On Windows, use
   `ctypes.windll.user32.GetForegroundWindow()` and compare the window rect to the
   screen rect. If fullscreen is detected, hide or minimize the pet. Restore it when
   fullscreen ends.

   ```python
   import ctypes

   def is_foreground_fullscreen():
       user32 = ctypes.windll.user32
       hwnd = user32.GetForegroundWindow()
       rect = ctypes.wintypes.RECT()
       user32.GetWindowRect(hwnd, ctypes.byref(rect))
       screen_w = user32.GetSystemMetrics(0)
       screen_h = user32.GetSystemMetrics(1)
       return (rect.left <= 0 and rect.top <= 0 and
               rect.right >= screen_w and rect.bottom >= screen_h)
   ```

2. **Use `Qt.Tool` flag** to prevent the pet from appearing in Alt-Tab. Combine with
   `Qt.WindowDoesNotAcceptFocus` if the pet should never steal focus.

3. **System tray implementation:**
   - Use `QSystemTrayIcon` with an explicit `.ico` file (not a `.png`).
   - Call `tray_icon.show()` after `QApplication` is fully initialized.
   - Create the context menu with `QMenu` and set it via `setContextMenu()`. Do NOT
     use `activated` signal for right-click -- use `setContextMenu()`.
   - Handle `QSystemTrayIcon.Context` in the `activated` signal only if you need
     custom behavior beyond the default context menu.

4. **Virtual desktop awareness.** There is no clean Qt API for this. Monitor
   `IVirtualDesktopManager` COM interface (Windows 10+) or accept that the pet may
   be hidden on non-active virtual desktops and handle `showEvent`/`hideEvent` to
   pause/resume animation.

5. **Screen-sharing etiquette.** Provide a "hide" toggle accessible from the tray
   icon so users can quickly hide the pet before sharing their screen.

6. **Z-order management.** Instead of a permanent `WindowStaysOnTopHint`, consider
   periodically calling `raise()` and `activateWindow()` with a cooldown. This is
   less intrusive and avoids conflicts with Task Manager (which explicitly sets
   itself topmost).

### Phase to Address

**Phase 2 (Window Behavior / Integration).** Fullscreen detection and tray icon
should be part of the core window management module, not bolted on later.

---

## 7. Python Desktop App Mistakes

### The Problem

Python developers moving from web/CLI to desktop GUI frequently make mistakes that
cause hangs, crashes, or unresponsive UIs.

### Warning Signs

- Application window shows "Not Responding" in the title bar and turns white.
- Network requests, file I/O, or heavy computation freeze the UI for seconds.
- Random crashes with `RuntimeError: wrapped C/C++ object of type X has been deleted`
  when interacting with the pet rapidly.
- Signals are received multiple times or not at all after reconnecting slots.
- High CPU usage at idle (busy-waiting in a loop instead of using event-driven
  mechanisms).
- `QPixmap: It is not safe to use pixmaps outside the GUI thread` warnings.

### Prevention Strategy

1. **Never block the main thread.** The Qt event loop (`app.exec()`) MUST remain
   free to process paint events, mouse events, and timer callbacks. Any operation
   that takes more than 16ms must be offloaded:

   - **I/O operations:** Use `QThread` or `QRunnable` with signals to communicate
     results back to the main thread.
   - **Network requests:** Use `QNetworkAccessManager` (async) or
     `requests` in a `QThread`.
   - **Heavy computation:** Use `QThreadPool.globalInstance().start()` with a
     `QRunnable`.

2. **Thread safety rules:**
   - NEVER create or modify `QWidget`, `QPixmap`, `QPainter`, or any GUI object
     from a non-GUI thread.
   - Use `QMetaObject.invokeMethod()` or signals/slots to communicate between
     threads.
   - Use `threading.Lock` only for pure Python data structures shared between
     threads, never for Qt objects.

3. **Prevent object lifecycle crashes:**
   - Store references to child widgets explicitly. If a Python variable goes out of
     scope but the C++ object is still alive (or vice versa), PySide6 will crash.
   - Connect signals with `Qt.ConnectionType.QueuedConnection` when the sender and
     receiver live in different threads.
   - Disconnect signals in `closeEvent` or `__del__` to prevent callbacks to deleted
     objects.

4. **Avoid busy-waiting.** Never write `while True: do_something(); time.sleep(0.1)`.
   Use `QTimer` instead:

   ```python
   timer = QTimer()
   timer.timeout.connect(do_something)
   timer.start(100)  # milliseconds
   ```

5. **Exception handling in slots.** Unhandled exceptions in Qt slots silently
   terminate the slot execution and may leave the application in an inconsistent
   state. Wrap all slot implementations in try/except and log errors:

   ```python
   @Slot()
   def on_timer_tick(self):
       try:
           self.do_logic()
       except Exception:
           traceback.print_exc()  # or write to log file
   ```

6. **Resource cleanup.** Use `QApplication.aboutToQuit` signal to save state and
   release resources. Do NOT rely on Python's `__del__` for critical cleanup -- the
   order of destruction during interpreter shutdown is undefined.

7. **Logging.** Replace `print()` with Python's `logging` module configured to write
   to a file. In `--noconsole` mode, `print()` output goes nowhere and you lose all
   diagnostic information.

### Phase to Address

**Phase 1 (Foundation).** Establish the threading pattern, logging setup, and error
handling conventions in the first phase. Every subsequent feature depends on these
conventions.

---

## Summary Table

| Pitfall Area | Severity | When to Address | Key Mitigation |
|---|---|---|---|
| Transparent windows / DPI | High | Phase 1 | `PerMonitorV2` DPI + `Qt.Tool` flag |
| Animation performance | Medium | Phase 2 | Sprite atlas + 15-30 FPS cap + lazy loading |
| PyInstaller packaging | High | Phase 1 + 4 | Resource path helper (Ph1), bundling config (Ph4) |
| JSON storage | High | Phase 1 | Atomic writes + backup rotation + schema version |
| Reminder / timer | Medium | Phase 1 + 3 | UTC timestamps (Ph1), sleep detection (Ph3) |
| Desktop integration | Medium | Phase 2 | Fullscreen detection + tray icon + hide toggle |
| Python desktop mistakes | High | Phase 1 | No blocking main thread + logging + error handling |

**Legend:**
- **Phase 1:** Foundation / Core architecture
- **Phase 2:** Window behavior / Animation / Integration
- **Phase 3:** Features (reminders, interactions, etc.)
- **Phase 4:** Packaging / Distribution / Polish
