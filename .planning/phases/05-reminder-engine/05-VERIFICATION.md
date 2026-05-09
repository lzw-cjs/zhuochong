---
phase: 05-reminder-engine
verified: 2026-05-10T12:00:00Z
status: gaps_found
score: 9/10 must-haves verified
overrides_applied: 0
gaps:
  - truth: "User can configure reminder timing per event (5 min, 15 min, 1 hr, or custom)"
    status: failed
    reason: "REM-02 requires configurable reminder timing per event. The Event data model has reminder_minutes field (default 15) and the engine uses it correctly, but EventDialog in schedule_panel.py has NO UI field for reminder_minutes. The get_event() method on line 132 does not include reminder_minutes in the Event constructor, so all events are created with default 15 minutes. Users cannot set 5 min, 1 hr, or custom reminder windows."
    artifacts:
      - path: "pet/schedule_panel.py"
        issue: "EventDialog (lines 23-141) has no QComboBox/QSpinBox for reminder_minutes. get_event() on line 132 omits reminder_minutes from Event constructor."
      - path: "data/event.py"
        issue: "Field exists (line 15: reminder_minutes: int = 15) but is never exposed to the user through any UI."
    missing:
      - "Add a reminder timing selector (QComboBox with 5/15/30/60 min + custom option) to EventDialog"
      - "Include reminder_minutes in EventDialog.get_event() return value"
human_verification:
  - test: "Run the app, create an event 10 minutes from now, wait for the reminder bubble to appear"
    expected: "Speech bubble with event title appears near pet, pet switches to ALERT animation, notification sound plays, pet returns to IDLE after 5 seconds"
    why_human: "Cannot run the app on this machine (Python not installed - Windows Store stub returns exit code 49). Requires visual and audio verification."
  - test: "Right-click tray, click toggle to suppress reminders, create a qualifying event, verify no reminder fires"
    expected: "No bubble, no ALERT animation, no sound when reminders are suppressed via tray toggle"
    why_human: "Requires running the app and observing tray toggle behavior"
  - test: "Create two events both within reminder window simultaneously, verify only one bubble shows"
    expected: "Only one bubble at a time (latest wins), dedup prevents second fire for same event"
    why_human: "Requires running the app with multiple events and observing dedup behavior"
---

# Phase 5: Reminder Engine Verification Report

**Phase Goal:** The pet proactively reminds the user of upcoming events with speech bubble popups and optional sound notifications, with configurable timing.
**Verified:** 2026-05-10
**Status:** gaps_found
**Re-verification:** No -- initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | ReminderEngine polls every 60 seconds and detects events within their reminder window | VERIFIED | `pet/reminder_engine.py` line 22: `self._timer.start(60000)`. Line 50: `reminder_time = event_time - timedelta(minutes=ev.reminder_minutes)`, line 51: `if now >= reminder_time:` fires signal. |
| 2 | Same event does not fire reminder twice (deduplication) | VERIFIED | `pet/reminder_engine.py` line 17: `self._fired: set[str] = set()`, line 52: `self._fired.add(ev.id)` after emit, line 44: `if ev.id in self._fired: continue`. 10 tests in `tests/test_reminder_engine.py` cover dedup. |
| 3 | Tray Hide suppresses all reminders; Tray Show restores them | VERIFIED | `main.py` lines 236-243: `toggle_pet_visibility()` calls `pre_reminder.suppress(True)` on hide, `pre_reminder.suppress(False)` on show. `pet/reminder_engine.py` lines 38-39: `_check()` returns early if `_suppressed`. |
| 4 | Existing overdue detection functionality is preserved after rename | VERIFIED | `pet/overdue_detector.py` contains full `ReminderEngine` class with `overdue = Signal(Event)` and `completed_early = Signal(Event)`. `main.py` line 21: `from pet.overdue_detector import ReminderEngine`. 3 tests in `tests/test_overdue_detector.py` verify import path and signals. |
| 5 | PetState.ALERT exists with correct transitions and frame interval | VERIFIED | `pet/states.py` line 11: `ALERT = "alert"`. All 4 states transition to ALERT (lines 16-19). ALERT only transitions to IDLE (line 20). FRAME_INTERVALS line 29: `PetState.ALERT: 150`. |
| 6 | ALERT placeholder frames render shaking body with exclamation mark | VERIFIED | `pet/animator.py` lines 111-128: ALERT branch with `shake = (frame_index % 2) * 2 - 1`, body ellipse at `(8 + shake, 10)`, 4x4 eyes at `(11 + shake, 13)` and `(18 + shake, 13)`, red exclamation `painter.drawText(14, 8, "!")` with `QColor(255, 0, 0)`. `generate_all_placeholder_frames()` line 140: `PetState.ALERT: 4`. |
| 7 | When reminder_fired signal emits, ChatBubble shows event title near pet | VERIFIED | `main.py` line 116: `bubble.show_message(f"提醒: {ev.title}", pos[0] + 32, pos[1], duration_ms=5000)`. `pet/bubble.py` line 58: `show_message(self, text, anchor_x, anchor_y, duration_ms=3000)` method exists with full implementation. |
| 8 | Notification sound plays when reminder fires (if not muted) | VERIFIED | `main.py` line 120: `sound_manager.play_reminder(muted=settings.muted)`. `pet/sound_manager.py` line 19-27: `play_reminder(muted)` returns early if muted, otherwise loads `reminder.wav` and calls `play()`. `assets/sounds/reminder.wav` exists (22094 bytes). 4 tests in `tests/test_sound_manager.py` cover mute/volume/missing-file. |
| 9 | User can configure reminder timing per event (5 min, 15 min, 1 hr, or custom) | FAILED | `Event.reminder_minutes` field exists (default 15) and engine uses it, but `pet/schedule_panel.py` EventDialog has NO UI to set this value. `get_event()` on line 132 does not pass `reminder_minutes` to Event constructor. All events default to 15 minutes. |
| 10 | Tray context menu has reminder toggle wired to engine | VERIFIED | `pet/tray.py` line 39: `reminder_suppress = Signal(bool)`. Lines 54-57: `_reminder_action` with checkable toggle. `main.py` line 251: `tray.reminder_suppress.connect(on_reminder_suppress)`. Line 249: `on_reminder_suppress` calls `pre_reminder.suppress(suppressed)`. |

**Score:** 9/10 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ |------- |
| `pet/reminder_engine.py` | ReminderEngine with QTimer polling, dedup, suppression | VERIFIED | 54 lines. Contains `reminder_fired = Signal(Event)`, `_fired` set, `_suppressed` bool, `_timer.start(60000)`, `suppress()`, `stop()`, `clear_fired()`, `_check()`. |
| `pet/overdue_detector.py` | Renamed overdue detector preserving all original functionality | VERIFIED | 98 lines. Contains `ReminderEngine` with `overdue` and `completed_early` signals, full overdue detection, `mark_completed()`, `extend_deadline()`, `cancel_event()`. |
| `pet/sound_manager.py` | SoundManager class with QSoundEffect | VERIFIED | 27 lines. `QSoundEffect` wrapper with `play_reminder(muted)`, `set_volume()`, volume clamping. |
| `assets/sounds/reminder.wav` | 16-bit PCM WAV notification sound | VERIFIED | File exists, 22094 bytes. Python not available to verify WAV header format, but file size is consistent with 0.5s audio at 22050Hz 16-bit mono (expected ~22050 bytes). |
| `pet/states.py` | PetState.ALERT enum + TRANSITIONS + FRAME_INTERVALS | VERIFIED | ALERT value "alert", 5 transition entries (4 existing + ALERT), frame interval 150ms. |
| `pet/animator.py` | ALERT placeholder frame generation | VERIFIED | ALERT branch in `generate_placeholder_frame()` with shake, wide eyes, red "!". `PetState.ALERT: 4` in `generate_all_placeholder_frames()`. |
| `pet/tray.py` | PetTrayIcon with reminder_suppress signal | VERIFIED | `reminder_suppress = Signal(bool)`, checkable `_reminder_action`, `_on_reminder_toggle()`, `update_reminder_suppressed()`. |
| `main.py` | Wired reminder_fired -> bubble + ALERT + sound | VERIFIED | `on_reminder_fired` handler (lines 113-122): bubble show_message, animator set_state ALERT, sound_manager.play_reminder, QTimer.singleShot 5000 -> IDLE. Signal connected line 124. Tray wiring lines 248-251. Cleanup line 216: `pre_reminder.stop()`. |
| `tests/test_reminder_engine.py` | Unit tests for ReminderEngine | VERIFIED | 196 lines, 10 test functions across 5 test classes covering fire/no-fire, dedup, suppress, clear_fired, edge cases. |
| `tests/conftest.py` | Shared pytest fixtures | VERIFIED | 47 lines. `make_event` factory with sentinel for empty datetime_str, `mock_store` MagicMock fixture. |
| `tests/test_overdue_detector.py` | Tests for renamed module | VERIFIED | 21 lines, 3 tests: import path, overdue signal, completed_early signal. |
| `tests/test_sound_manager.py` | Tests for SoundManager | VERIFIED | 62 lines, 4 tests: not muted, muted, volume clamping, missing file. |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `pet/reminder_engine.py` | `data/schedule_store.py` | `self._store.get_all()` in `_check()` | WIRED | Line 41: `for ev in self._store.get_all()`. ScheduleStore.get_all() returns `list[Event]` from JSON store. |
| `pet/reminder_engine.py` | `data/event.py` | `ev.reminder_minutes` and `ev.datetime_str` | WIRED | Line 47: `datetime.fromisoformat(ev.datetime_str)`, line 50: `timedelta(minutes=ev.reminder_minutes)`. |
| `main.py` | `pet/reminder_engine.py` | `reminder_fired.connect(on_reminder_fired)` | WIRED | Line 124: `pre_reminder.reminder_fired.connect(on_reminder_fired)`. |
| `main.py` | `pet/bubble.py` | `bubble.show_message()` in handler | WIRED | Line 116: `bubble.show_message(f"提醒: {ev.title}", ...)`. |
| `main.py` | `pet/animator.py` | `animator.set_state(PetState.ALERT)` in handler | WIRED | Line 118: `animator.set_state(PetState.ALERT)`. |
| `main.py` | `pet/sound_manager.py` | `sound_manager.play_reminder()` in handler | WIRED | Line 120: `sound_manager.play_reminder(muted=settings.muted)`. |
| `pet/sound_manager.py` | `assets/sounds/reminder.wav` | `QUrl.fromLocalFile(sound_path)` | WIRED | Line 23: `sound_path = self._sound_dir / "reminder.wav"`, line 27: `self._effect.setSource(QUrl.fromLocalFile(str(sound_path)))`. |
| `pet/tray.py` | `main.py` | `reminder_suppress` signal connected | WIRED | `main.py` line 251: `tray.reminder_suppress.connect(on_reminder_suppress)`. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| ALERT state transitions | `python -c "from pet.states import PetState, can_transition; assert can_transition(PetState.IDLE, PetState.ALERT); assert not can_transition(PetState.ALERT, PetState.WALK)"` | SKIPPED -- Python not available (exit code 49) | ? SKIP |
| ReminderEngine tests pass | `python -m pytest tests/test_reminder_engine.py -x -v` | SKIPPED -- Python not available | ? SKIP |
| SoundManager tests pass | `python -m pytest tests/test_sound_manager.py -x -v` | SKIPPED -- Python not available | ? SKIP |
| main.py syntax valid | `python -c "import ast; ast.parse(open('main.py').read())"` | SKIPPED -- Python not available | ? SKIP |
| Code inspection: on_reminder_fired exists | grep "def on_reminder_fired" main.py | 1 match (line 113) | PASS |
| Code inspection: reminder_fired.connect exists | grep "reminder_fired.connect" main.py | 1 match (line 124) | PASS |

**Note:** All behavioral spot-checks requiring Python execution were skipped because the Windows Store Python stub returns exit code 49 (Python not actually installed). Code inspection confirms the logic is structurally correct.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| REM-01 | 05-01, 05-02, 05-03, 05-04 | Bubble popup reminder near pet | SATISFIED | `on_reminder_fired` handler calls `bubble.show_message()`. ChatBubble renders styled speech bubble with event title. ALERT animation state provides visual feedback. |
| REM-02 | 05-01 | Configurable reminder timing (5/15/60/custom) | BLOCKED | `Event.reminder_minutes` field exists and engine uses it, but NO UI to configure per event. EventDialog does not expose this field. All events default to 15 minutes. |
| REM-03 | 05-03, 05-04 | Sound notification (QSoundEffect, WAV) | SATISFIED | SoundManager uses QSoundEffect. reminder.wav exists. Muted flag respected. Tray toggle provides user control. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `main.py` | 120 | `settings.muted` captured by closure at startup | INFO | Settings.muted is read once at startup. If a future settings UI changes muted at runtime, the closure would still reference the same Settings object (Python closures capture variables, not values), so this works correctly. No current runtime UI exists to change this anyway. |
| `pet/schedule_panel.py` | 132-141 | `reminder_minutes` omitted from Event constructor | BLOCKER | Events created through EventDialog always get default 15 minutes. This is the root cause of the REM-02 failure. |

### Human Verification Required

### 1. End-to-End Reminder Flow

**Test:** Run the app, create an event 10 minutes from now via the schedule panel, wait for the reminder to fire.
**Expected:** Speech bubble with "提醒: {title}" appears near the pet for 5 seconds. Pet switches to ALERT animation (shaking body, wide eyes, red "!"). Notification sound plays (ascending beep). After 5 seconds, pet returns to IDLE.
**Why human:** Requires running the PySide6 application and observing visual/audio behavior. Cannot be tested without a display and audio output.

### 2. Tray Reminder Suppression Toggle

**Test:** Right-click the system tray icon, click "关闭提醒" toggle. Create a qualifying event. Verify no reminder fires. Click "开启提醒" to restore.
**Expected:** When suppressed, no bubble, no ALERT, no sound. When restored, reminders fire normally.
**Why human:** Requires interacting with the system tray and observing runtime behavior.

### 3. Deduplication with Multiple Events

**Test:** Create two events both within their reminder windows. Wait for both to trigger.
**Expected:** First event fires a reminder. Second event fires a separate reminder (different IDs). Same event does not fire twice.
**Why human:** Requires running the app with real events and observing dedup behavior over time.

### Gaps Summary

**1 gap blocking goal achievement:**

REM-02 ("User can configure reminder timing per event") is not satisfied. The data model (`Event.reminder_minutes`) and engine (`ReminderEngine._check()`) fully support configurable timing, but the `EventDialog` in `pet/schedule_panel.py` has no UI control for this field. The `get_event()` method on line 132 does not include `reminder_minutes` in the Event constructor, so all events are created with the default 15-minute window. Users cannot set 5 min, 1 hour, or custom reminder windows per event.

**Fix required:** Add a QComboBox (with options: 5 min, 15 min, 30 min, 1 hour, custom) or QSpinBox to the EventDialog, and pass the selected value through `get_event()`.

All other must-haves (9/10) are verified through code inspection. The ReminderEngine core, ALERT state, SoundManager, tray toggle, and main.py wiring are all structurally correct and properly connected.

---

_Verified: 2026-05-10_
_Verifier: Claude (gsd-verifier)_
