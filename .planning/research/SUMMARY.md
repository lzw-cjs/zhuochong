# Desktop Pet Application — Research Summary

Synthesized from STACK.md, FEATURES.md, ARCHITECTURE.md, PITFALLS.md on 2026-05-09.

---

## 1. Stack Decision

- **GUI**: PySide6 (LGPL, maintained by Qt Company, full transparent window support)
- **Animation**: Sprite sheets via QPixmap + QTimer (zero extra deps, full alpha, deterministic frame control)
- **Audio**: QSoundEffect from PySide6-Addons (no pygame dependency, low latency)
- **Calendar**: `icalendar` + `recurring-ical-events` (full RFC 5545, handles RRULE/EXDATE)
- **Storage**: JSON files with atomic writes (`os.replace`), `filelock`, schema versioning
- **Packaging**: PyInstaller for dev/test, Nuitka for production release
- **Python**: 3.12+ recommended; PySide6 >= 6.8.0, < 6.10

## 2. Table Stakes Features (v1 Must-Haves)

- Transparent frameless always-on-top window (pet renders on desktop)
- Drag-to-reposition with position persistence
- Idle animations (minimum 3 states: idle, happy, alert)
- Click interaction with visual feedback
- System tray icon for quick access/exit
- Settings persistence (JSON)
- Low CPU/memory usage (15-30 FPS cap, QTimer-based)
- Graceful startup/shutdown (no ghost processes)

## 3. Key Architecture Decisions

- **Window flags**: `FramelessWindowHint | WindowStaysOnTopHint | Tool` with `WA_TranslucentBackground`
- **Click-through**: Dynamic `WS_EX_TRANSPARENT` toggle on mouse enter/leave (simple, sufficient for small sprites)
- **State machine**: Custom enum + transition table (not Qt QStateMachine — too verbose)
- **Multi-window**: PetWindow + ChatBubble + ChatPanel + SchedulePanel + SettingsPanel, connected via Qt signals
- **Chat engine**: Strategy pattern — ship RuleBasedEngine (keyword matching + templates), clean seam for future LLM
- **Data layer**: Dataclasses for models, JsonStore with atomic writes, ScheduleStore for event CRUD
- **DPI awareness**: `PerMonitorV2` set before QApplication construction; handle `screenChanged` signals
- **Reminders**: Polling-based ReminderEngine (60s interval), absolute UTC timestamps, deduplication via `last_fired` set

## 4. Watch Out For

| Pitfall | Severity | Key Mitigation |
|---------|----------|----------------|
| Qt translucent window rendering (Win11 RHI) | High | Pin PySide6 6.8.x; apply `QSG_RHI_BACKEND=opengl` workaround |
| DPI scaling across monitors | High | Set `PerMonitorV2` before any Qt object; handle `logicalDotsPerInchChanged` |
| Animation memory leaks | Medium | Sprite atlas (not individual files); lazy-load; cap at 15-30 FPS |
| JSON corruption on crash | High | Atomic writes (temp + `os.replace`); backup rotation; schema versioning |
| PyInstaller antivirus false positives | Medium | Use `--onedir` not `--onefile`; code-sign; exclude unused PySide6 modules |
| Blocking the main thread | High | Never do I/O or computation on GUI thread; use QThread + signals |
| Reminder drift after sleep/wake | Medium | Store absolute UTC timestamps; compare against wall clock, not elapsed time |
| Fullscreen app interference | Medium | Detect fullscreen foreground window; hide pet automatically |

## 5. Build Order

1. **Skeleton** — JsonStore, data models, PetWindow with transparency, main.py entry point
2. **Animation** — SpriteAnimator, AnimationController, state machine, BehaviorScheduler
3. **Interaction** — Drag/drop, click reactions, right-click context menu, system tray
4. **Chat** — ChatEngine abstraction, RuleBasedEngine, ChatBubble, ChatPanel
5. **Schedule** — ScheduleStore, SchedulePanel (day/week/month views), event CRUD
6. **Reminders** — ReminderEngine, wire to pet ALERT state and ChatBubble popups
7. **Polish** — Settings panel, error handling, sprite refinement, PyInstaller packaging

Phases 4 (chat) and 5 (schedule) are independent and can be parallelized.

## 6. Key Recommendation

**Ship the calendar as a standalone widget first, then attach the pet to it.** The calendar/schedule system is the largest single subsystem (~30% of effort) and the primary differentiator — no existing desktop pet combines full calendar functionality with a personality-driven companion. De-risking the hardest component first, then layering the pet animation and chat on top, is the safest path to a shippable product.
