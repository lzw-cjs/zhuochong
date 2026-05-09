# Smart Desktop Pet (智能桌面宠物)

## What This Is

A pixel-art desktop pet application built with Python + PyQt/PySide. The pet lives on the user's desktop as a small animated creature that they can interact with, manage schedules through, and receive reminders from. Think of it as a modern take on classic desktop pets (like Shimeji or the old Windows BonziBuddy), but with practical utility built in.

## Why It Exists

Desktop pets combine emotional companionship with practical productivity tools. Instead of switching to a separate calendar app, the user interacts with their pet to manage schedules — making productivity feel less like a chore. The pixel-art aesthetic adds charm and nostalgia.

## Who It's For

Individual users who want a cute, functional desktop companion that helps them stay organized. The target user values aesthetics and enjoys playful UI over sterile productivity tools.

## Core Value

A pixel-art pet that is both charming to interact with AND practically useful for schedule management. If either half fails — ugly animations or broken reminders — the whole thing falls apart.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] **PET-01**: Pixel-art animal character with sprite frame animation (idle, walk, sit, sleep, happy, alert states)
- [ ] **PET-02**: Pet window is transparent/frameless, always-on-top, renders on desktop
- [ ] **PET-03**: User can drag-and-drop pet to move it anywhere on screen
- [ ] **PET-04**: Clicking the pet triggers feedback animation and a chat bubble
- [ ] **PET-05**: Right-click context menu with access to settings, schedule, chat, and exit
- [ ] **CHAT-01**: Typing chat interface where user can talk to the pet
- [ ] **CHAT-02**: Rule-based response engine (keyword matching + template replies)
- [ ] **CHAT-03**: LLM API interface reserved for future expansion (clean abstraction layer)
- [ ] **SCHED-01**: Full calendar view (day/week/month)
- [ ] **SCHED-02**: Create/edit/delete events with title, time, description, category, priority
- [ ] **SCHED-03**: Recurring events (daily, weekly, monthly, custom)
- [ ] **SCHED-04**: Multiple calendar support (color-coded)
- [ ] **SCHED-05**: Import/export calendar data (iCal/JSON format)
- [ ] **REMIND-01**: Bubble popup notification from pet when event is due
- [ ] **REMIND-02**: Configurable reminder timing (5min, 15min, 1hr before, custom)
- [ ] **REMIND-03**: Sound notification option
- [ ] **STORE-01**: All data stored in local JSON files
- [ ] **STORE-02**: Settings persistence (pet position, preferences, theme)
- [ ] **PKG-01**: Packageable as standalone .exe (PyInstaller)
- [ ] **UI-01**: Settings panel for customizing pet behavior, appearance, notifications
- [ ] **UI-02**: System tray icon for quick access

### Out of Scope

- Multi-pet support — v1 focuses on one pet, multi-pet adds complexity without core value
- Network/cloud sync — v1 is local-only, no account system
- Pet customization editor — v1 uses pre-made sprites, not a sprite editor
- Mobile companion — desktop only for v1
- Voice input/output — text chat only, voice adds significant complexity

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| PyQt/PySide over Tkinter | Better transparency, animation support, modern look | PySide6 (LGPL, more permissive) |
| Sprite frame animation | Classic pixel-art feel, full control over each frame | PNG sprite sheets |
| JSON over SQLite | Simpler for v1, human-readable, easy import/export | JSON files in user data dir |
| Rule-based chat first | Ship fast, clean abstraction for LLM later | Strategy pattern for chat engine |
| PyInstaller for .exe | Most mature Python-to-exe tool | Single-file bundled exe |

## Tech Stack (Initial)

- **Language**: Python 3.10+
- **GUI Framework**: PySide6 (Qt for Python)
- **Animation**: Sprite sheets (PNG) with QTimer-based frame cycling
- **Storage**: JSON files (json module)
- **Calendar**: Custom implementation with iCal import/export (icalendar lib)
- **Packaging**: PyInstaller
- **Audio**: pygame.mixer or QSoundEffect

## Architecture (Initial)

```
desktop_pet/
├── main.py                  # Entry point
├── ui/
│   ├── pet_window.py        # Transparent frameless pet window
│   ├── chat_bubble.py       # Speech bubble popup
│   ├── context_menu.py      # Right-click menu
│   ├── schedule_view.py     # Calendar/schedule UI
│   ├── settings_panel.py    # Settings dialog
│   └── tray_icon.py         # System tray
├── core/
│   ├── animation.py         # Sprite animation engine
│   ├── interaction.py       # Drag, click, hover handlers
│   ├── scheduler.py         # Schedule data management
│   ├── reminder.py          # Reminder engine with timers
│   └── chat_engine.py       # Chat response system
├── data/
│   ├── storage.py           # JSON file read/write
│   └── models.py            # Event, Settings data classes
├── assets/
│   ├── sprites/             # PNG sprite sheets
│   ├── sounds/              # Notification sounds
│   └── icons/               # App and tray icons
└── config/
    └── chat_rules.json      # Keyword-response mappings
```

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-09 after initialization*
