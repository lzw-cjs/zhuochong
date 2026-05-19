# Smart Desktop Pet

A pixel-art desktop pet application built with Python + PySide6. An adorable otter lives on your desktop, capable of autonomous behavior, AI-powered chat, schedule management, voice interaction, and holiday-themed costumes.

## Features

### Desktop Pet

- **Transparent Frameless Window** — The otter floats directly on your desktop with per-pixel alpha transparency
- **9 Animation States** — IDLE, WALK, SLEEP, HAPPY, ALERT, EAT, PLAY, GROOM, REST, each with unique sprite animations
- **Autonomous Behavior** — Random state switching every 30–90s, auto-sleep after 5 minutes of inactivity
- **Screen Movement** — Walks freely across the screen during WALK state
- **Smooth Transitions** — 300ms alpha fade between state changes
- **Drag & Drop** — Reposition the pet by dragging; resize with scroll wheel (0.5x–3.0x)
- **State Indicator** — Emoji icon above the pet showing current state

### AI Chat

- **Dual Engine Architecture** — LLM engine (OpenAI-compatible / Anthropic) as primary, rule-based engine as fallback
- **Chat Panel** — Full chat UI with message history
- **Chat Bubble** — Reply messages displayed as floating bubbles near the pet
- **Conversation Memory** — Configurable history window (default 50 messages)

### Voice Interaction

- **Speech-to-Text (STT)** — Microphone recording via `sounddevice`, recognition via Xfyun IAT WebSocket API
- **Text-to-Speech (TTS)** — Microsoft Edge TTS with multiple voice options, auto-play replies
- **One-Click Mic Button** — Record → Recognize → Send in the chat panel

### Schedule Management

- **Calendar Grid** — Monthly calendar view with event management (add/edit/delete)
- **Reminder Engine** — Pre-reminder (15 min before) with bubble + ALERT animation + sound effect
- **Overdue Detection** — Floating notification when tasks are overdue, with "extend 1 hour" or "cancel" options
- **Early Completion** — Praise messages and HAPPY state when tasks are completed ahead of schedule
- **Midnight Refresh** — Auto-refresh calendar and reminders on day change

### Holiday Costumes

- **Automatic Detection** — Checks every hour if the current date falls within a holiday period
- **Lunar Calendar Support** — Uses `lunardate` for Chinese lunar holidays (Spring Festival, Mid-Autumn, Dragon Boat, etc.)
- **Costume Overlay** — Holiday-themed accessories rendered on top of the otter sprite
- **Configurable** — Toggle costumes on/off via right-click menu

### System Integration

- **System Tray** — Tray icon with visibility toggle, reminder suppress, and exit options
- **Persistent Settings** — JSON storage with atomic writes, file locking, and schema versioning
- **Position Memory** — Remembers pet position, scale, and animation state across sessions
- **Smart Topmost** — Periodically checks and restores window z-order

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| GUI Framework | **PySide6** | LGPL, Qt Company maintained, full animation support |
| Animation | **QPainter Programmatic Drawing** | Zero asset dependencies, full alpha, deterministic frame control |
| Audio | **QSoundEffect / QMediaPlayer** | Built-in to PySide6, low latency |
| STT | **Xfyun IAT** | Chinese speech recognition via WebSocket |
| TTS | **Edge TTS** | Free Microsoft TTS with multiple Chinese voices |
| Calendar | **icalendar** + **recurring-ical-events** | Full RFC 5545 support |
| Storage | **JSON** + atomic writes + filelock | Simple, crash-safe, schema-versioned |
| Lunar Calendar | **lunardate** | Chinese lunar date conversion |
| Packaging | **PyInstaller** (dev) / **Nuitka** (prod) | Easy builds / native performance |

## Requirements

- Python 3.11+
- Windows 10/11 (uses Windows-specific APIs for transparency and topmost)

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/smart-desktop-pet.git
cd smart-desktop-pet

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Dependencies

```
PySide6>=6.8.0
openai>=1.0.0
anthropic>=0.30.0
edge-tts>=6.1.0
sounddevice>=0.4.0
numpy>=1.24.0
websocket-client>=1.6.0
icalendar>=5.0
recurring-ical-events>=3.0
filelock>=3.13
lunardate
```

## Configuration

Settings are stored in `settings.json` (auto-created on first run). Key options:

| Setting | Description | Default |
|---|---|---|
| `pet.x` / `pet.y` | Pet position on screen | `(200, 200)` |
| `pet.scale` | Display scale factor (0.5–3.0) | `1.0` |
| `preferences.costume_enabled` | Enable holiday costumes | `true` |
| `llm.protocol` | LLM provider (`openai` / `anthropic`) | _(empty)_ |
| `llm.api_key` | API key for LLM provider | _(empty)_ |
| `llm.model` | Model name | `gpt-3.5-turbo` / `claude-sonnet-4-20250514` |
| `voice.enabled` | Enable voice features | `true` |
| `voice.tts_voice` | Edge TTS voice | `zh-CN-XiaoxiaoNeural` |
| `voice.xfyun_app_id` | Xfyun app ID for STT | _(empty)_ |

### LLM Chat Setup

1. Right-click the pet → **Settings**
2. Select protocol (`openai` or `anthropic`)
3. Enter your API key and base URL
4. Optionally customize the system prompt

### Voice Setup

1. Get Xfyun credentials at [console.xfyun.com](https://console.xfyun.com)
2. Right-click the pet → **Settings** → Voice tab
3. Enter App ID, API Key, API Secret
4. Click the microphone button in the chat panel to start voice input

## Usage

| Action | How |
|---|---|
| **Move pet** | Left-click and drag |
| **Resize pet** | Scroll wheel up/down |
| **Chat** | Right-click → Chat |
| **Schedule** | Right-click → Schedule |
| **Settings** | Right-click → Settings |
| **Toggle costumes** | Right-click → Toggle costumes |
| **Hide/Show** | System tray icon → Toggle visibility |
| **Debug states** | Press number keys `1`–`9` to switch states, `0` to resume auto |

## Project Structure

```
smart-desktop-pet/
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── data/
│   ├── settings.py             # Settings read/write (JSON persistence)
│   ├── store.py                # Generic JSON store (atomic writes + filelock)
│   ├── chat_history.py         # Conversation history management
│   ├── schedule_store.py       # Schedule data storage
│   ├── holidays.json           # Holiday definitions (solar + lunar)
│   └── chat_rules.json         # Rule-based chat patterns
├── pet/
│   ├── window.py               # Transparent frameless window
│   ├── states.py               # 9 animation states + transition table
│   ├── animator.py             # Sprite animation engine (QPainter drawing)
│   ├── behavior.py             # Auto behavior scheduler
│   ├── movement.py             # Screen movement controller
│   ├── transition.py           # Alpha fade transitions
│   ├── indicator.py            # Emoji state indicator
│   ├── bubble.py               # Chat bubble widget
│   ├── chat_engine.py          # Chat engines (rule-based + LLM)
│   ├── chat_panel.py           # Chat panel UI
│   ├── schedule_panel.py       # Schedule panel UI
│   ├── calendar_grid.py        # Calendar grid component
│   ├── overdue_detector.py     # Overdue task detection
│   ├── overdue_widget.py       # Overdue floating notification
│   ├── reminder_engine.py      # Reminder engine (pre-reminder + on-time)
│   ├── sound_manager.py        # Sound effect manager
│   ├── holiday_engine.py       # Holiday detection (solar + lunar)
│   ├── costume.py              # Holiday costume renderer
│   ├── settings_dialog.py      # Settings dialog
│   ├── tray.py                 # System tray icon
│   ├── voice_stt.py            # Speech-to-text (Xfyun IAT)
│   └── voice_tts.py            # Text-to-speech (Edge TTS)
├── utils/
│   └── assets.py               # Asset path resolution
├── assets/
│   ├── sounds/                 # Sound effects (WAV)
│   └── icon.ico                # Application icon
├── scripts/
│   ├── generate_arch_diagram.py
│   └── generate_ppt.py
└── tests/
    ├── test_functional.py      # Functional tests
    ├── test_llm_engine.py      # LLM engine tests
    ├── test_voice.py           # Voice module tests
    └── ...
```

## Packaging

### Development

```bash
python main.py
```

### PyInstaller (Testing)

```bash
pyinstaller --onefile --windowed --add-data "assets;assets" --icon assets/icon.ico main.py
```

### Nuitka (Production)

```bash
nuitka --standalone --onefile --enable-plugin=pyside6 --include-data-dir=assets=assets main.py
```

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_functional.py

# Run with verbose output
pytest -v
```

## Acknowledgements

- [PySide6](https://wiki.qt.io/Qt_for_Python) — Qt for Python
- [Edge TTS](https://github.com/rany2/edge-tts) — Microsoft Edge TTS
- [Xfyun IAT](https://www.xfyun.cn/doc/asr/voicedictation_recuperation/API.html) — Speech recognition
- [lunardate](https://github.com/wolfhong/lunardate) — Chinese lunar calendar

## License

This project is for educational and personal use.
