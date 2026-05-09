# Roadmap — Smart Desktop Pet

## Overview

6 phases | 22 requirements mapped | All v1 requirements covered

| Phase | Name | Requirements |
|-------|------|--------------|
| 1 | Skeleton & Animation | PET-01, PET-03, DAT-01, DAT-02 |
| 2 | Interaction | PET-02, PET-04, INT-01, INT-02 |
| 3 | Chat System | INT-03, INT-04, INT-05 |
| 4 | Calendar Data Layer | SCH-01, SCH-02, SCH-03, SCH-04 |
| 5 | Reminder Engine | REM-01, REM-02, REM-03 |
| 6 | Polish & Packaging | DAT-03, PKG-01, PKG-02, PKG-03 |

---

### Phase 1: Skeleton & Animation

**Goal:** A pixel-art pet appears on the desktop in a transparent frameless window, cycles through idle/walk/sit/sleep/happy/alert animations, and persists its position and settings across restarts.
**Mode:** mvp

**Success Criteria:**
1. User sees a small animated pet rendered directly on their desktop background, visible over all other windows.
2. Pet cycles through at least 3 animation states (idle, walk, sit) automatically via sprite frame animation.
3. After closing and relaunching the app, the pet reappears at the same screen position with the same preferences.
4. Pet renders cleanly on Windows 11 with no white background, no flicker, and no taskbar entry.

**Requirements**: PET-01, PET-03, DAT-01, DAT-02

**Plans:**
1. **P1.1 — Project scaffold & data layer** — Set up project structure, PySide6 dependencies, JsonStore with atomic writes, Settings and AnimationConfig dataclasses, main.py entry point.
2. **P1.2 — Transparent pet window** — Implement PetWindow with FramelessWindowHint + WindowStaysOnTopHint + WA_TranslucentBackground, DPI awareness, PerMonitorV2 scaling.
3. **P1.3 — Sprite animation engine** — Build SpriteAnimator (QPixmap + QTimer), AnimationController with state machine (enum + transition table), load sprite sheets for all 6 states.
4. **P1.4 — Position & settings persistence** — Save/load pet position to JSON on move and on shutdown, persist theme and animation preferences, handle app startup restore.

---

### Phase 2: Interaction

**Goal:** User can drag the pet around the screen, click it for animation feedback and a speech bubble, right-click for a context menu, and access the pet from the system tray.
**Mode:** mvp

**Success Criteria:**
1. User can click and drag the pet to any position on screen; the pet stays where dropped.
2. Clicking the pet triggers a reaction animation (e.g., happy bounce) and a brief speech bubble appears above it.
3. Right-clicking anywhere on the pet opens a menu with "Schedule", "Chat", "Settings", and "Exit" options.
4. A pet icon appears in the system tray; right-clicking it shows "Show/Hide Pet" and "Exit".

**Requirements**: PET-02, PET-04, INT-01, INT-02

**Plans:**
1. **P2.1 — Drag-and-drop** — Implement mousePressEvent/mouseMoveEvent/mouseReleaseEvent on PetWindow, constrain to screen bounds, persist new position on drop.
2. **P2.2 — Click feedback & speech bubble** — Handle mouse click (non-drag) to trigger reaction animation state and show a transient ChatBubble widget anchored to the pet.
3. **P2.3 — Context menu** — Build QMenu on right-click with actions for Schedule, Chat, Settings, Exit; wire actions to signal bus for Phase 3+ panels.
4. **P2.4 — System tray icon** — Create QSystemTrayIcon with .ico asset, context menu for Show/Hide and Exit, handle double-click to toggle pet visibility.

---

### Phase 3: Chat System

**Goal:** User can open a chat panel, type messages to the pet, and receive rule-based replies. The architecture cleanly supports swapping in an LLM engine later.
**Mode:** mvp

**Success Criteria:**
1. User opens the chat panel (via right-click menu or clicking the pet) and sees a conversation-style message list.
2. Typing a message containing a keyword (e.g., "hello", "help", "schedule") produces a contextual reply from the pet.
3. Messages the pet does not recognize trigger a friendly fallback response, not an error.
4. The chat engine abstraction supports a single function swap to enable LLM-based replies in the future.

**Requirements**: INT-03, INT-04, INT-05

**Plans:**
1. **P3.1 — Chat engine abstraction** — Define ChatEngine ABC (Strategy pattern), implement RuleBasedEngine with keyword matching + template responses, load rules from chat_rules.json.
2. **P3.2 — Chat bubble UI** — Build ChatBubble widget (speech bubble anchored to pet) for quick one-line replies triggered by clicks.
3. **P3.3 — Chat panel UI** — Build ChatPanel as a separate window with message list (QScrollArea), text input (QLineEdit), send button, styled to match pixel-art aesthetic.
4. **P3.4 — Wire chat to interaction** — Connect right-click "Chat" action and pet click to open ChatPanel, route messages through ChatEngine, display replies in both ChatPanel and ChatBubble.

---

### Phase 4: Calendar Data Layer

**Goal:** User can create, view, edit, and delete schedule events with titles, times, descriptions, categories, and priorities. Events are organized into color-coded calendars and can be imported/exported as JSON.
**Mode:** mvp

**Success Criteria:**
1. User opens the schedule panel and sees a list/calendar view of their upcoming events.
2. User creates a new event with title, date/time, description, category, and priority — it appears in the view immediately.
3. User can edit any event field or delete an event; changes persist after restart.
4. User can import a JSON file and see those events appear; user can export their events to a JSON file.

**Requirements**: SCH-01, SCH-02, SCH-03, SCH-04

**Plans:**
1. **P4.1 — Event data model & store** — Define Event dataclass (title, datetime, description, category, priority, calendar_id), build ScheduleStore on top of JsonStore with full CRUD.
2. **P4.2 — Multi-calendar support** — Implement Calendar dataclass (id, name, color), calendar management in ScheduleStore, filter events by calendar.
3. **P4.3 — Schedule panel UI** — Build SchedulePanel with event list view, create/edit dialog (QDialog with form fields), delete confirmation, color-coded calendar indicators.
4. **P4.4 — Import/export** — Implement JSON import (file picker + validation + merge strategy) and JSON export (file picker + atomic write), handle schema version in exported files.

---

### Phase 5: Reminder Engine

**Goal:** The pet proactively reminds the user of upcoming events with speech bubble popups and optional sound notifications, with configurable timing.
**Mode:** mvp

**Success Criteria:**
1. When an event is 15 minutes away (default), the pet shows a speech bubble popup with the event title and switches to its alert animation state.
2. User can configure reminder timing per event (5 min, 15 min, 1 hr, or custom).
3. A notification sound plays when a reminder fires (if enabled in settings).
4. After dismissing a reminder, it does not fire again for the same event occurrence.

**Requirements**: REM-01, REM-02, REM-03

**Plans:**
1. **P5.1 — Reminder engine core** — Build ReminderEngine with 60s polling loop, compare event times against wall clock using absolute UTC timestamps, deduplication via last_fired set, connect to ScheduleStore.
2. **P5.2 — Bubble popup & alert state** — Show ChatBubble near pet with event title when reminder fires, trigger ALERT animation state on the pet, auto-dismiss after timeout or click.
3. **P5.3 — Configurable timing & sound** — Add reminder_minutes field to Event model, support per-event timing (5/15/60/custom), implement QSoundEffect playback for WAV notification sound, respect mute setting.
4. **P5.4 — Reminder lifecycle** — Handle sleep/wake drift (compare absolute timestamps), clear fired reminders, wire "Show/Hide" from tray to suppress/restore reminders, graceful shutdown cleanup.

---

### Phase 6: Polish & Packaging

**Goal:** The application is packaged as a standalone .exe with all assets bundled, schema versioning ensures safe data migrations, and the system tray displays a polished icon.
**Mode:** mvp

**Success Criteria:**
1. User downloads and runs a single .exe file; the pet appears on their desktop with no Python installation required.
2. Sprite images, sounds, and icons all load correctly from the bundled package (no "file not found" errors).
3. If a future version changes the data schema, the app migrates old JSON files automatically without data loss.
4. The system tray displays a crisp 16x16 pixel-art icon matching the pet character.

**Requirements**: DAT-03, PKG-01, PKG-02, PKG-03

**Plans:**
1. **P6.1 — Asset path helper** — Implement get_asset_path() that resolves correctly in both dev (relative) and packaged (sys._MEIPASS) modes, replace all hardcoded asset paths across the codebase.
2. **P6.2 — Schema versioning** — Add _schema_version field to all JSON data files, implement migration registry (version -> transform function), auto-migrate on load when version mismatch detected.
3. **P6.3 — System tray icon** — Design/source 16x16 and 32x32 .ico files for the pet character, wire into QSystemTrayIcon, ensure icon displays correctly in Windows notification area.
4. **P6.4 — PyInstaller packaging** — Configure PyInstaller spec file (--onedir mode), bundle all assets/sprites/sounds/icons, exclude unused PySide6 modules to reduce size, test clean install on a machine without Python.

---

*Last updated: 2026-05-09 — Roadmap created with 6 phases, 22 requirements mapped*
