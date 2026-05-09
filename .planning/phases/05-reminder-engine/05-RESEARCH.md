# Phase 5: Reminder Engine - Research

**Researched:** 2026-05-10
**Domain:** Qt timer-based reminder system, audio playback, animation state machine extension
**Confidence:** HIGH

## Summary

Phase 5 implements proactive event reminders: the pet shows a speech bubble and plays a sound when an event is approaching (default 15 minutes before). The existing codebase provides strong foundations -- the `Event` model already has a `reminder_minutes` field (default 15), `ChatBubble` exists for popup display, `Settings` has a `muted` flag, and `ScheduleStore` provides full CRUD. The main work is: (1) building a new `ReminderEngine` that fires BEFORE events (the current one only detects overdue events AFTER deadlines), (2) adding `ALERT` to the `PetState` enum and transition table, (3) integrating `QSoundEffect` for WAV playback, and (4) wiring everything into `main.py`.

**Primary recommendation:** Extend the existing codebase incrementally. Reuse `ChatBubble` for popups, add `ALERT` state to the animation state machine, build a new `ReminderEngine` class alongside the existing overdue detector, and use `QSoundEffect` from `PySide6.QtMultimedia` for sound.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Reminder timing logic | Backend (Python) | -- | QTimer-based polling, datetime comparison |
| Speech bubble popup | Browser/Client (Qt widget) | -- | ChatBubble is a QWidget overlay |
| Sound playback | Backend (PySide6 QtMultimedia) | -- | QSoundEffect is a Qt audio class |
| Animation state transition | Backend (Python) | -- | PetState enum + SpriteAnimator |
| User settings (mute, timing) | Backend (Python) | -- | Settings dataclass + JsonStore |
| Event data access | Backend (Python) | -- | ScheduleStore + Event model |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PySide6 | 6.11.0 (installed) | Qt bindings, QSoundEffect, QTimer | Already project dependency |
| PySide6.QtMultimedia | 6.11.0 (installed) | QSoundEffect for WAV playback | Bundled with PySide6-Addons |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| PySide6-Addons | 6.11.0 (installed) | Multimedia backends | Required for QSoundEffect on Windows |

**Installation:** No additional packages needed. PySide6 and PySide6-Addons are already installed. [VERIFIED: pip show output]

**Version verification:**
- PySide6 6.11.0 [VERIFIED: pip show]
- PySide6-Addons 6.11.0 [VERIFIED: pip show]
- QtMultimedia.pyd exists at `site-packages/PySide6/QtMultimedia.pyd` [VERIFIED: file system]

## Architecture Patterns

### System Architecture: Reminder Flow

```
Event.datetime_str + Event.reminder_minutes
            |
            v
    ReminderEngine (QTimer, 60s poll)
            |
            v
    Compare: now >= (event_time - reminder_minutes)?
            |
       YES  |  NO --> skip
            v
    Deduplicate: event.id in _fired_set?
            |
       NO   |  YES --> skip
            v
    +--> ChatBubble.show_message(title, ...)
    +--> AnimationController --> ALERT state
    +--> QSoundEffect.play() (if !muted)
    +--> Add event.id to _fired_set
```

### Recommended Project Structure

```
pet/
├── reminder_engine.py    # NEW: ReminderEngine (pre-event reminders)
├── overdue_detector.py   # RENAME from current reminder_engine.py (post-deadline detection)
├── bubble.py             # EXISTING: ChatBubble (reuse for reminders)
├── states.py             # MODIFY: add ALERT to PetState + transitions
├── animator.py           # MODIFY: add ALERT placeholder frames
├── window.py             # EXISTING: no changes needed
└── tray.py               # MODIFY: add "Show/Hide" reminder suppression
data/
├── event.py              # EXISTING: already has reminder_minutes field
├── settings.py           # EXISTING: already has muted field
└── schedule_store.py     # EXISTING: no changes needed
assets/
└── sounds/
    └── reminder.wav      # NEW: notification sound file
```

### Pattern 1: QTimer Polling Loop

**What:** Use QTimer with 60-second interval to check upcoming events
**When to use:** For periodic background checks that don't need sub-second precision
**Example:**
```python
# Source: Existing pattern in pet/reminder_engine.py (adapted)
class ReminderEngine(QObject):
    reminder_fired = Signal(Event)  # fires when event is approaching

    def __init__(self, store: ScheduleStore, parent=None):
        super().__init__(parent)
        self._store = store
        self._fired: set[str] = set()  # deduplication
        self._timer = QTimer()
        self._timer.timeout.connect(self._check)
        self._timer.start(60000)  # 60 seconds

    def _check(self):
        now = datetime.now()
        for ev in self._store.get_all():
            if ev.status != "pending" or not ev.datetime_str:
                continue
            if ev.id in self._fired:
                continue
            try:
                event_time = datetime.fromisoformat(ev.datetime_str)
            except ValueError:
                continue
            reminder_time = event_time - timedelta(minutes=ev.reminder_minutes)
            if now >= reminder_time:
                self._fired.add(ev.id)
                self.reminder_fired.emit(ev)
```

### Pattern 2: QSoundEffect for Notification Sound

**What:** Use QSoundEffect for low-latency WAV playback
**When to use:** For short sound clips (notification sounds)
**Example:**
```python
# Source: PySide6.QtMultimedia documentation
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtCore import QUrl

class SoundManager:
    def __init__(self):
        self._effect = QSoundEffect()
        self._effect.setVolume(0.5)  # 0.0 to 1.0

    def play_reminder(self, sound_path: str, muted: bool = False):
        if muted:
            return
        self._effect.setSource(QUrl.fromLocalFile(sound_path))
        self._effect.play()
```

### Pattern 3: ALERT Animation State

**What:** Add ALERT to PetState enum with appropriate transitions
**When to use:** When the pet needs to visually indicate an alert/notification
**Example:**
```python
# Source: Existing pattern in pet/states.py (extended)
class PetState(Enum):
    IDLE = "idle"
    WALK = "walk"
    SLEEP = "sleep"
    HAPPY = "happy"
    ALERT = "alert"  # NEW

TRANSITIONS = {
    PetState.IDLE:  [PetState.WALK, PetState.SLEEP, PetState.HAPPY, PetState.ALERT],
    PetState.WALK:  [PetState.IDLE, PetState.HAPPY, PetState.ALERT],
    PetState.SLEEP: [PetState.IDLE, PetState.HAPPY, PetState.ALERT],
    PetState.HAPPY: [PetState.IDLE, PetState.ALERT],
    PetState.ALERT: [PetState.IDLE],  # ALERT only returns to IDLE
}
```

### Anti-Patterns to Avoid

- **Blocking the event loop:** Never use `time.sleep()` or blocking I/O in the reminder check. Use QTimer for all periodic operations. [ASSUMED]
- **Comparing naive vs aware datetimes:** The Event model uses ISO 8601 strings without timezone info. All comparisons should use `datetime.fromisoformat()` consistently (naive datetimes). Mixing aware and naive datetimes raises `TypeError`. [ASSUMED]
- **Playing sound on every poll tick:** The deduplication set (`_fired`) must be checked BEFORE emitting signals or playing sounds. [ASSUMED]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Sound playback | pygame.mixer or winsound | QSoundEffect | Already have PySide6-Addons; no extra dependency |
| Timer scheduling | Manual sleep loops | QTimer | Qt event loop integration, non-blocking |
| Deduplication | Complex state tracking | Simple set of event IDs | In-memory set is sufficient for MVP |

## Common Pitfalls

### Pitfall 1: QSoundEffect Requires Valid WAV File
**What goes wrong:** QSoundEffect silently fails if the WAV file doesn't exist or has unsupported format
**Why it happens:** QSoundEffect only supports PCM WAV (16-bit, mono/stereo). No MP3, no OGG.
**How to avoid:** Use a valid 16-bit PCM WAV file. Check `QSoundEffect.status()` after setting source.
**Warning signs:** No sound plays, no error message

### Pitfall 2: Sleep/Wake Drift
**What goes wrong:** If the computer sleeps for 30 minutes, the QTimer may fire multiple times rapidly to "catch up", or miss events entirely
**Why it happens:** QTimer uses system clock; sleep pauses the event loop
**How to avoid:** Compare absolute timestamps (wall clock) in `_check()`, not relative timer intervals. The `now >= reminder_time` comparison handles drift naturally. [ASSUMED]
**Warning signs:** Multiple reminders for the same event after wake, or missed reminders

### Pitfall 3: Existing ReminderEngine Name Collision
**What goes wrong:** The current `reminder_engine.py` contains an overdue detector, not a pre-event reminder engine
**Why it happens:** Phase 4 created it for deadline detection
**How to avoid:** Rename current file to `overdue_detector.py`, update imports in `main.py`, then create new `reminder_engine.py`
**Warning signs:** Import errors, confused signal names

### Pitfall 4: ChatBubble Reuse Without Anchoring
**What goes wrong:** Reminder bubble appears at wrong position or overlaps with click-triggered bubble
**Why it happens:** ChatBubble positions itself relative to anchor coordinates passed by caller
**How to avoid:** Always pass `window.get_position()` coordinates when showing reminder bubbles. Consider dismissing any existing bubble before showing a new one. [ASSUMED]
**Warning signs:** Bubble appears off-screen or at (0,0)

### Pitfall 5: ALERT State Transition Back to Previous State
**What goes wrong:** After alert animation, pet returns to IDLE instead of its previous state (e.g., SLEEP)
**Why it happens:** Simple state machine doesn't track previous state
**How to avoid:** Store `_previous_state` before ALERT transition, restore it after alert timeout. Or always return to IDLE (simpler, acceptable for MVP). [ASSUMED]
**Warning signs:** Pet wakes up from sleep to show alert, then stays awake instead of going back to sleep

## Code Examples

### Complete ReminderEngine with Deduplication

```python
"""Reminder engine: fire reminders BEFORE events approach"""
from datetime import datetime, timedelta
from PySide6.QtCore import QTimer, Signal, QObject

from data.event import Event
from data.schedule_store import ScheduleStore


class ReminderEngine(QObject):
    """Proactive reminder engine.

    Polls every 60 seconds. When an event is within its
    `reminder_minutes` window, emits `reminder_fired` signal.
    Deduplicates via in-memory set of fired event IDs.
    """

    reminder_fired = Signal(Event)

    def __init__(self, store: ScheduleStore, parent=None):
        super().__init__(parent)
        self._store = store
        self._fired: set[str] = set()
        self._suppressed: bool = False  # tray "Hide" suppresses reminders

        self._timer = QTimer()
        self._timer.timeout.connect(self._check)
        self._timer.start(60000)

    def suppress(self, suppress: bool) -> None:
        """Suppress/restore reminders (tray Show/Hide)."""
        self._suppressed = suppress

    def clear_fired(self, event_id: str | None = None) -> None:
        """Clear dedup set for an event, or all events."""
        if event_id:
            self._fired.discard(event_id)
        else:
            self._fired.clear()

    def _check(self) -> None:
        if self._suppressed:
            return
        now = datetime.now()
        for ev in self._store.get_all():
            if ev.status != "pending" or not ev.datetime_str:
                continue
            if ev.id in self._fired:
                continue
            try:
                event_time = datetime.fromisoformat(ev.datetime_str)
            except ValueError:
                continue
            reminder_time = event_time - timedelta(minutes=ev.reminder_minutes)
            if now >= reminder_time:
                self._fired.add(ev.id)
                self.reminder_fired.emit(ev)
```

### SoundManager with QSoundEffect

```python
"""Sound manager for notification sounds"""
from pathlib import Path
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtCore import QUrl


class SoundManager:
    """Manages notification sound playback."""

    def __init__(self, sound_dir: Path):
        self._effect = QSoundEffect()
        self._effect.setVolume(0.5)
        self._sound_dir = sound_dir

    def set_volume(self, volume: float) -> None:
        """Set volume (0.0 to 1.0)."""
        self._effect.setVolume(max(0.0, min(1.0, volume)))

    def play_reminder(self, muted: bool = False) -> None:
        """Play the reminder notification sound."""
        if muted:
            return
        sound_path = self._sound_dir / "reminder.wav"
        if not sound_path.exists():
            return
        self._effect.setSource(QUrl.fromLocalFile(str(sound_path)))
        self._effect.play()
```

### ALERT State Extension

```python
# In pet/states.py - add ALERT state
class PetState(Enum):
    IDLE = "idle"
    WALK = "walk"
    SLEEP = "sleep"
    HAPPY = "happy"
    ALERT = "alert"  # NEW: reminder notification state

TRANSITIONS = {
    PetState.IDLE:  [PetState.WALK, PetState.SLEEP, PetState.HAPPY, PetState.ALERT],
    PetState.WALK:  [PetState.IDLE, PetState.HAPPY, PetState.ALERT],
    PetState.SLEEP: [PetState.IDLE, PetState.HAPPY, PetState.ALERT],
    PetState.HAPPY: [PetState.IDLE, PetState.ALERT],
    PetState.ALERT: [PetState.IDLE],
}

FRAME_INTERVALS = {
    PetState.IDLE:  500,
    PetState.WALK:  300,
    PetState.SLEEP: 800,
    PetState.HAPPY: 200,
    PetState.ALERT: 150,  # Fast blinking/shaking for alert
}
```

### ALERT Placeholder Frames

```python
# In pet/animator.py - add ALERT placeholder generation
def generate_placeholder_frame(state: PetState, frame_index: int, total_frames: int) -> QPixmap:
    # ... existing states ...
    elif state == PetState.ALERT:
        # Alert: shaking body + wide eyes + exclamation mark
        shake = (frame_index % 2) * 2 - 1  # -1, 1, -1, 1...
        painter.setBrush(QBrush(body_color))
        painter.setPen(QPen(body_color, 1))
        painter.drawEllipse(8 + shake, 10, 16, 18)

        # Wide eyes (larger than normal)
        painter.setBrush(QBrush(eye_color))
        painter.drawEllipse(11 + shake, 13, 4, 4)
        painter.drawEllipse(18 + shake, 13, 4, 4)

        # Exclamation mark
        painter.setPen(QPen(QColor(255, 0, 0), 2))
        painter.drawText(14, 8, "!")
```

### Wiring in main.py

```python
# In main.py - connect reminder engine to UI
from pet.reminder_engine import ReminderEngine
from pet.sound_manager import SoundManager

# Create reminder engine
reminder_engine = ReminderEngine(schedule_store)

# Create sound manager
sound_manager = SoundManager(Path("assets/sounds"))

# Handle reminder fired
def on_reminder_fired(ev):
    # Show bubble
    pos = window.get_position()
    bubble.show_message(f"Reminder: {ev.title}", pos[0] + 32, pos[1], duration_ms=5000)

    # Trigger ALERT animation
    behavior.on_user_interaction()  # This resets idle timer
    animator.set_state(PetState.ALERT)

    # Play sound
    sound_manager.play_reminder(muted=settings.muted)

    # Return to IDLE after 5 seconds
    QTimer.singleShot(5000, lambda: animator.set_state(PetState.IDLE))

reminder_engine.reminder_fired.connect(on_reminder_fired)

# Tray "Hide" suppresses reminders
def toggle_pet_visibility():
    if window.isVisible():
        window.hide()
        tray.update_visibility_state(False)
        reminder_engine.suppress(True)  # Suppress reminders when hidden
    else:
        window.show()
        tray.update_visibility_state(True)
        reminder_engine.suppress(False)  # Restore reminders when shown

tray.toggle_visibility.connect(toggle_pet_visibility)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No pre-event reminders | QTimer polling + signal emission | Phase 5 (this phase) | New capability |
| No ALERT state | ALERT in PetState enum | Phase 5 (this phase) | Visual feedback for reminders |
| No sound playback | QSoundEffect for WAV | Phase 5 (this phase) | Audio notification |
| Overdue-only detection | Pre-event + post-deadline | Phase 5 (this phase) | Two complementary engines |

**Deprecated/outdated:**
- The current `reminder_engine.py` is actually an overdue detector. It should be renamed to `overdue_detector.py` to avoid confusion with the new pre-event `ReminderEngine`.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | QTimer 60-second polling is sufficient precision for reminders | Pattern 1 | Reminders may fire up to 60 seconds late; acceptable for MVP |
| A2 | Naive datetimes (no timezone) are acceptable for local-only app | Pitfall 2 | Breaks if user changes system timezone; acceptable for v1 |
| A3 | ALERT state always returns to IDLE (no "return to previous state") | Pattern 3 | Pet may not return to SLEEP after alert; minor UX issue |
| A4 | QSoundEffect supports WAV playback on Windows without additional setup | Pattern 2 | Silent failure if multimedia backend missing; mitigated by PySide6-Addons |
| A5 | In-memory dedup set is sufficient (no persistence needed) | Pattern 1 | Reminders re-fire after app restart; acceptable for MVP |
| A6 | 5-second ALERT duration is appropriate | Code Examples | Too short/long; can be tuned |

## Open Questions

1. **Sound file sourcing**
   - What we know: `assets/sounds/` directory exists but is empty
   - What's unclear: Where to source a notification WAV file
   - Recommendation: Generate a simple beep programmatically or use a free CC0 sound effect. For MVP, a 0.5-second sine wave beep can be generated with Python's `wave` module.

2. **Reminder bubble interaction**
   - What we know: ChatBubble auto-dismisses after `duration_ms`
   - What's unclear: Should reminder bubbles be clickable (e.g., to open event details)?
   - Recommendation: For MVP, auto-dismiss only. Click interaction can be added in Phase 6 polish.

3. **Multiple simultaneous reminders**
   - What we know: ChatBubble is a single widget instance
   - What's unclear: What happens if 3 events all trigger reminders in the same 60-second window?
   - Recommendation: Show one bubble at a time, cycling through pending reminders. Or show the most recent one only.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| PySide6 | All UI, timers, signals | Yes | 6.11.0 | -- |
| PySide6-Addons | QSoundEffect multimedia backend | Yes | 6.11.0 | -- |
| QtMultimedia.pyd | QSoundEffect import | Yes (file exists) | -- | Use winsound.Beep as fallback |
| WAV sound file | Notification sound | No (directory empty) | -- | Generate programmatically |

**Missing dependencies with no fallback:**
- (none)

**Missing dependencies with fallback:**
- WAV sound file: Can generate a simple beep with Python's `wave` module, or use `winsound.Beep` for a basic system beep

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (not yet installed) |
| Config file | none -- see Wave 0 |
| Quick run command | `pytest tests/ -x` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REM-01 | Reminder bubble shows when event is N minutes away | unit | `pytest tests/test_reminder_engine.py::test_reminder_fires_within_window -x` | Wave 0 |
| REM-02 | Per-event reminder timing (5/15/60/custom) | unit | `pytest tests/test_reminder_engine.py::test_custom_reminder_minutes -x` | Wave 0 |
| REM-03 | Sound plays when reminder fires (if not muted) | unit | `pytest tests/test_sound_manager.py::test_play_reminder_not_muted -x` | Wave 0 |
| -- | Deduplication: same event doesn't fire twice | unit | `pytest tests/test_reminder_engine.py::test_deduplication -x` | Wave 0 |
| -- | Suppression: tray hide suppresses reminders | unit | `pytest tests/test_reminder_engine.py::test_suppress_reminders -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/test_reminder_engine.py -x`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_reminder_engine.py` -- covers REM-01, REM-02, deduplication, suppression
- [ ] `tests/test_sound_manager.py` -- covers REM-03
- [ ] `tests/conftest.py` -- shared fixtures (mock ScheduleStore, mock QSoundEffect)
- [ ] Framework install: `pip install pytest` -- if not already installed

## Security Domain

Not applicable for this phase. The reminder engine is a local-only feature with no network exposure, no user authentication, and no sensitive data handling beyond what already exists in the Event model.

## Sources

### Primary (HIGH confidence)
- PySide6 6.11.0 installed locally [VERIFIED: pip show]
- PySide6-Addons 6.11.0 installed locally [VERIFIED: pip show]
- QtMultimedia.pyd exists in site-packages [VERIFIED: file system]
- Event model has `reminder_minutes` field [VERIFIED: data/event.py line 15]
- Settings model has `muted` field [VERIFIED: data/settings.py line 35]
- ChatBubble exists with `show_message()` API [VERIFIED: pet/bubble.py]
- PetState enum has IDLE/WALK/SLEEP/HAPPY (no ALERT) [VERIFIED: pet/states.py]
- Current reminder_engine.py is overdue detector [VERIFIED: pet/reminder_engine.py]

### Secondary (MEDIUM confidence)
- QSoundEffect API patterns [CITED: Qt 6 documentation, PySide6 examples]
- QTimer polling pattern for background tasks [CITED: Qt documentation]

### Tertiary (LOW confidence)
- Sleep/wake drift handling with absolute timestamps [ASSUMED]
- ALERT state transition design (always return to IDLE) [ASSUMED]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all dependencies verified installed
- Architecture: HIGH -- existing codebase provides clear patterns to follow
- Pitfalls: MEDIUM -- some edge cases (sleep/wake, multiple reminders) are assumed

**Research date:** 2026-05-10
**Valid until:** 2026-06-10 (30 days -- PySide6 and project are stable)
