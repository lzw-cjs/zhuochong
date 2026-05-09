# Architecture Research: Smart Desktop Pet (PySide6)

## 1. Qt Transparent Window Architecture

### Window Flags

The pet window requires three combined flags to behave as a desktop overlay:

```python
window.setWindowFlags(
    Qt.WindowType.FramelessWindowHint      # No title bar, no borders
    | Qt.WindowType.WindowStaysOnTopHint   # Always above other windows
    | Qt.WindowType.Tool                   # Hidden from taskbar and Alt+Tab
)
window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
```

- `FramelessWindowHint` removes the OS-decorated chrome entirely.
- `WindowStaysOnTopHint` keeps the pet visible above all other windows.
- `Tool` prevents the pet from appearing in the taskbar or Alt+Tab switcher.
- `WA_TranslucentBackground` makes the widget background fully transparent, so only painted pixels (the sprite) are visible.

### Click-Through on Windows

Qt does not natively support pixel-level click-through. On Windows, this requires the Win32 API via `pywin32` or `ctypes`.

**Approach: WS_EX_TRANSPARENT + WS_EX_LAYERED**

```python
import win32gui
import win32con

WS_EX_LAYERED    = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
GWL_EXSTYLE      = -20

hwnd = int(widget.winId())
ex = win32gui.GetWindowLong(hwnd, GWL_EXSTYLE)
win32gui.SetWindowLong(hwnd, GWL_EXSTYLE,
    ex | WS_EX_LAYERED | WS_EX_TRANSPARENT)
```

This makes the entire window click-through. To allow clicking on the pet sprite but passing through transparent areas, there are two strategies:

**Strategy A: Dynamic style toggling (recommended for v1)**

Toggle `WS_EX_TRANSPARENT` on/off based on mouse hover:

```python
class PetWindow(QWidget):
    def enterEvent(self, event):
        # Remove click-through when mouse enters the widget rect
        self._set_click_through(False)

    def leaveEvent(self, event):
        # Restore click-through when mouse leaves
        self._set_click_through(True)

    def _set_click_through(self, enable: bool):
        hwnd = int(self.winId())
        ex = win32gui.GetWindowLong(hwnd, GWL_EXSTYLE)
        if enable:
            win32gui.SetWindowLong(hwnd, GWL_EXSTYLE,
                ex | WS_EX_TRANSPARENT)
        else:
            win32gui.SetWindowLong(hwnd, GWL_EXSTYLE,
                ex & ~WS_EX_TRANSPARENT)
```

Limitation: The entire widget rect becomes clickable on hover, not just opaque pixels.

**Strategy B: WM_NCHITTEST override (pixel-accurate, more complex)**

Override the Windows hit-test message to return `HTTRANSPARENT` for transparent pixels and `HTCLIENT` for opaque pixels. Requires intercepting the native event via `nativeEvent()` and checking pixel alpha at the cursor position. More precise but harder to implement correctly.

**Recommendation for v1:** Strategy A is sufficient. The pet window is small (~64-128px), so the entire rect being clickable is acceptable. Strategy B can be added later if needed.

### Subclassing for the Pet Window

```python
class PetWindow(QWidget):
    """Transparent, frameless, always-on-top window that renders the pet sprite."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(SPRITE_WIDTH, SPRITE_HEIGHT)

    def paintEvent(self, event):
        # Delegated to animation engine
        ...
```

---

## 2. Animation Engine Design

### Sprite Sheet Format

Each state gets a row (or a separate sheet) in a PNG sprite sheet. Standard layout:

```
sprites/idle.png    -- row of N frames, e.g. 64x64 per frame, 8 frames = 512x64
sprites/walk.png    -- walk cycle, 4-6 frames
sprites/sit.png     -- sitting idle, 4 frames
sprites/sleep.png   -- sleeping, 4-6 frames
sprites/happy.png   -- reaction animation, 4 frames
sprites/alert.png   -- notification reaction, 4 frames
```

### State Machine

Use a custom enum + transition table rather than Qt's `QStateMachine`. The Qt state machine framework is powerful but verbose for this use case. A lightweight custom implementation is clearer and easier to debug.

```python
from enum import Enum, auto

class PetState(Enum):
    IDLE    = auto()
    WALK    = auto()
    SIT     = auto()
    SLEEP   = auto()
    HAPPY   = auto()
    ALERT   = auto()
    DRAG    = auto()  # User is dragging the pet

# Valid transitions: current_state -> set of allowed next_states
TRANSITIONS = {
    PetState.IDLE:  {PetState.WALK, PetState.SIT, PetState.SLEEP, PetState.HAPPY, PetState.ALERT, PetState.DRAG},
    PetState.WALK:  {PetState.IDLE, PetState.SIT, PetState.DRAG},
    PetState.SIT:   {PetState.IDLE, PetState.SLEEP, PetState.HAPPY, PetState.ALERT, PetState.DRAG},
    PetState.SLEEP: {PetState.IDLE, PetState.ALERT},
    PetState.HAPPY: {PetState.IDLE, PetState.SIT},
    PetState.ALERT: {PetState.IDLE, PetState.HAPPY},
    PetState.DRAG:  {PetState.IDLE},  # Always returns to idle after drop
}
```

### SpriteAnimator Class

```python
class SpriteAnimator:
    """Manages frame cycling for a single animation state."""

    def __init__(self, sheet_path: str, frame_w: int, frame_h: int,
                 frame_count: int, fps: int = 8, loop: bool = True):
        self.sheet = QPixmap(sheet_path)
        self.frame_w = frame_w
        self.frame_h = frame_h
        self.frame_count = frame_count
        self.frame_duration_ms = 1000 // fps
        self.loop = loop
        self.current_frame = 0
        self.finished = False

    def advance(self) -> QPixmap:
        if not self.finished:
            self.current_frame += 1
            if self.current_frame >= self.frame_count:
                if self.loop:
                    self.current_frame = 0
                else:
                    self.current_frame = self.frame_count - 1
                    self.finished = True
        rect = QRect(self.current_frame * self.frame_w, 0,
                     self.frame_w, self.frame_h)
        return self.sheet.copy(rect)

    def reset(self):
        self.current_frame = 0
        self.finished = False
```

### AnimationController

Ties the state machine to animators:

```python
class AnimationController:
    def __init__(self, pet_widget: QWidget):
        self.widget = pet_widget
        self.state = PetState.IDLE
        self.animators: dict[PetState, SpriteAnimator] = {}
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)

    def register(self, state: PetState, animator: SpriteAnimator):
        self.animators[state] = animator

    def transition_to(self, new_state: PetState):
        if new_state not in TRANSITIONS[self.state]:
            return  # Invalid transition, ignore
        self.state = new_state
        self.animators[new_state].reset()
        self.timer.setInterval(self.animators[new_state].frame_duration_ms)
        if not self.timer.isActive():
            self.timer.start()

    def _tick(self):
        frame = self.animators[self.state].advance()
        self.widget.current_frame = frame
        self.widget.update()

    def current_frame(self) -> QPixmap:
        return self.animators[self.state].advance()
```

### Behavior Scheduler (Autonomous Movement)

A separate `QTimer` drives autonomous behavior decisions:

```python
class BehaviorScheduler:
    """Decides when the pet changes behavior on its own."""

    def __init__(self, controller: AnimationController):
        self.controller = controller
        self.timer = QTimer()
        self.timer.timeout.connect(self._decide)
        self.timer.start(random.randint(5000, 15000))  # Random interval

    def _decide(self):
        state = self.controller.state
        if state == PetState.IDLE:
            # Random chance to walk, sit, or stay idle
            roll = random.random()
            if roll < 0.3:
                self.controller.transition_to(PetState.WALK)
            elif roll < 0.5:
                self.controller.transition_to(PetState.SIT)
            # else stay idle
        elif state == PetState.WALK:
            self.controller.transition_to(PetState.IDLE)
        # ... etc.
        self.timer.setInterval(random.randint(5000, 15000))
```

---

## 3. Mouse Event Handling on Transparent Windows

### Drag to Move

The pet must be draggable. Override `mousePressEvent`, `mouseMoveEvent`, `mouseReleaseEvent`:

```python
class PetWindow(QWidget):
    def __init__(self):
        super().__init__()
        self._drag_pos = None
        self._is_dragging = False

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._is_dragging = True
            self.anim_controller.transition_to(PetState.DRAG)
            event.accept()

    def mouseMoveEvent(self, event):
        if self._is_dragging and event.buttons() & Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self._drag_pos
            self.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = False
            self._drag_pos = None
            self.anim_controller.transition_to(PetState.IDLE)
            self._save_position()  # Persist to JSON
            event.accept()
```

### Click Detection

Single-click triggers a reaction animation (HAPPY or ALERT). Right-click opens context menu.

```python
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self._is_dragging or self._drag_distance < 5:
                # Was a click, not a drag
                self.anim_controller.transition_to(PetState.HAPPY)
                self.chat_bubble.show_random_greeting()
            # ... rest of drag cleanup

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction("Chat", self.open_chat)
        menu.addAction("Schedule", self.open_schedule)
        menu.addAction("Settings", self.open_settings)
        menu.addSeparator()
        menu.addAction("Exit", QApplication.quit)
        menu.exec(event.globalPos())
```

### Hit Testing Considerations

With Strategy A (dynamic click-through toggle), the entire widget rect is clickable when the mouse is inside. For a 64x64 or 128x128 sprite, this is acceptable. If pixel-accurate clicking is needed later, override `nativeEvent` to intercept `WM_NCHITTEST`:

```python
def nativeEvent(self, eventType, message):
    if eventType == b"windows_generic_MSG":
        msg = message
        if msg.message == 0x0084:  # WM_NCHITTEST
            # Check if cursor is over an opaque pixel
            # Return HTCLIENT if yes, HTTRANSPARENT if no
            ...
    return super().nativeEvent(eventType, message)
```

---

## 4. Multi-Window Architecture

### Window Inventory

| Window | Type | Flags | Purpose |
|--------|------|-------|---------|
| PetWindow | QWidget | Frameless, StayOnTop, Tool | Renders the pet sprite |
| ChatBubble | QWidget | Frameless, StayOnTop, Tool | Speech bubble near pet |
| ChatPanel | QWidget | Frameless, StayOnTop, Tool | Full chat input UI |
| SchedulePanel | QWidget | Dialog or Tool | Calendar view, event CRUD |
| SettingsPanel | QDialog | Normal dialog | Preferences, appearance |
| SystemTray | QSystemTrayIcon | N/A | Tray icon + context menu |

### Window Positioning

ChatBubble and ChatPanel must track the pet's position:

```python
class ChatBubble(QWidget):
    def __init__(self, pet_window: PetWindow):
        super().__init__()
        self.pet = pet_window
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def show_near_pet(self, text: str):
        pet_pos = self.pet.pos()
        # Position bubble above the pet
        self.move(pet_pos.x(), pet_pos.y() - self.height() - 10)
        self._text = text
        self.show()
        # Auto-hide after delay
        QTimer.singleShot(4000, self.hide)
```

### Communication Between Windows

Use Qt signals for loose coupling:

```python
class PetWindow(QWidget):
    # Signals emitted by pet
    chat_requested = Signal()
    schedule_requested = Signal()
    settings_requested = Signal()
    state_changed = Signal(PetState)

# In main.py, connect signals to slots:
pet.chat_requested.connect(chat_panel.show)
pet.schedule_requested.connect(schedule_panel.show)
pet.state_changed.connect(lambda s: tray.update_status(s.name))
```

### Z-Order Management

Multiple StayOnTop windows can conflict. Use `Qt.WindowType.WindowStaysOnTopHint` only on windows that must always be visible (PetWindow, ChatBubble). SchedulePanel and SettingsPanel should be normal dialogs that appear above the pet via `setParent` or `raise_()`.

---

## 5. Timer/Scheduler Design for Reminders

### Architecture

```
ReminderEngine
    |
    +-- QTimer (60-second poll interval)
    |       |
    |       +-- check_due_events()
    |               |
    |               +-- reads from ScheduleStore (in-memory cache of JSON)
    |               +-- compares QDateTime.currentDateTime() against event times
    |               +-- emits reminder_due(event) signal
    |
    +-- Signal: reminder_due(Event)
            |
            +-- PetWindow.transition_to(PetState.ALERT)
            +-- ChatBubble.show_reminder(event.title, event.time)
            +-- SoundPlayer.play("reminder.wav")  # optional
```

### ReminderEngine Implementation

```python
class ReminderEngine(QObject):
    reminder_due = Signal(object)  # Emits the Event object

    def __init__(self, schedule_store: ScheduleStore):
        super().__init__()
        self.store = schedule_store
        self.timer = QTimer()
        self.timer.timeout.connect(self._check)
        self.timer.start(60_000)  # Check every 60 seconds
        self._fired_ids: set[str] = set()  # Prevent duplicate fires

    def _check(self):
        now = QDateTime.currentDateTime()
        events = self.store.get_events_in_range(
            now, now.addSecs(3600)  # Look ahead 1 hour
        )
        for event in events:
            if event.id in self._fired_ids:
                continue
            reminder_time = event.datetime.addSecs(-event.reminder_offset_secs)
            if now >= reminder_time:
                self._fired_ids.add(event.id)
                self.reminder_due.emit(event)
```

### Timer Precision

QTimer is not real-time. A 60-second interval is sufficient for minute-granularity reminders. For sub-minute precision, reduce to 10-second polling. Do not use sub-second polling -- it wastes CPU for no practical benefit.

### Recurring Event Expansion

Recurring events (daily, weekly, monthly) should be expanded at load time into individual occurrences within a lookahead window (e.g., 30 days). Store the expansion in memory; persist only the recurrence rule in JSON.

---

## 6. Data Layer

### Storage Structure

```
~/.smart-desktop-pet/
    settings.json       # App preferences, pet position, theme
    calendars/
        default.json    # Primary calendar events
        work.json       # Additional calendar (optional)
    chat_rules.json     # Keyword-response mappings
    state.json          # Current pet state, last position
```

### JSON File Manager

```python
class JsonStore:
    """Generic JSON file read/write with atomic writes."""

    def __init__(self, path: Path):
        self.path = path
        self._cache: dict | list | None = None

    def load(self) -> dict:
        if self._cache is not None:
            return self._cache
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as f:
                self._cache = json.load(f)
        else:
            self._cache = {}
        return self._cache

    def save(self, data: dict):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        tmp.replace(self.path)  # Atomic on most filesystems
        self._cache = data
```

Atomic write (write to `.tmp`, then rename) prevents data corruption if the app crashes mid-write.

### Data Models

Use `dataclasses` for type safety:

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import uuid4

class Recurrence(Enum):
    NONE    = "none"
    DAILY   = "daily"
    WEEKLY  = "weekly"
    MONTHLY = "monthly"
    CUSTOM  = "custom"

@dataclass
class CalendarEvent:
    id: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    description: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    category: str = "default"
    priority: int = 0  # 0=low, 1=medium, 2=high
    recurrence: Recurrence = Recurrence.NONE
    reminder_offset_secs: int = 900  # 15 minutes default
    calendar_id: str = "default"

    def to_dict(self) -> dict:
        ...
    @classmethod
    def from_dict(cls, d: dict) -> "CalendarEvent":
        ...

@dataclass
class AppSettings:
    pet_position: tuple[int, int] = (100, 100)
    pet_scale: float = 1.0
    sound_enabled: bool = True
    theme: str = "default"
    start_minimized: bool = False
    calendar_ids: list[str] = field(default_factory=lambda: ["default"])
```

### ScheduleStore

Wraps JsonStore with event-specific operations:

```python
class ScheduleStore:
    def __init__(self, calendars_dir: Path):
        self.dir = calendars_dir
        self._events: dict[str, list[CalendarEvent]] = {}

    def load_all(self):
        for f in self.dir.glob("*.json"):
            store = JsonStore(f)
            data = store.load()
            cal_id = f.stem
            self._events[cal_id] = [CalendarEvent.from_dict(e) for e in data.get("events", [])]

    def add_event(self, event: CalendarEvent):
        self._events.setdefault(event.calendar_id, []).append(event)
        self._save_calendar(event.calendar_id)

    def get_events_in_range(self, start: datetime, end: datetime) -> list[CalendarEvent]:
        results = []
        for events in self._events.values():
            for e in events:
                if start <= e.start_time <= end:
                    results.append(e)
        return sorted(results, key=lambda e: e.start_time)
```

---

## 7. Chat Engine Abstraction

### Strategy Pattern

Define an abstract chat engine interface. Ship with a rule-based engine; swap in LLM later.

```python
from abc import ABC, abstractmethod

class ChatEngine(ABC):
    @abstractmethod
    def respond(self, user_message: str, context: dict) -> str:
        """Generate a response to the user's message.
        
        Args:
            user_message: The user's input text.
            context: Optional context dict (e.g., current pet state, recent events).
        Returns:
            Response string.
        """
        ...

class RuleBasedEngine(ChatEngine):
    def __init__(self, rules_path: Path):
        self.rules = self._load_rules(rules_path)

    def _load_rules(self, path: Path) -> list[dict]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f).get("rules", [])

    def respond(self, user_message: str, context: dict) -> str:
        msg_lower = user_message.lower()
        for rule in self.rules:
            keywords = rule.get("keywords", [])
            if any(kw in msg_lower for kw in keywords):
                return random.choice(rule.get("responses", ["..."]))
        return random.choice(self.rules[0].get("default_responses", ["Hmm?"]))

class LLMEngine(ChatEngine):
    """Future: wraps an LLM API (OpenAI, Anthropic, etc.)."""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model

    def respond(self, user_message: str, context: dict) -> str:
        # Future implementation
        raise NotImplementedError("LLM engine not yet implemented")
```

### chat_rules.json Format

```json
{
  "rules": [
    {
      "keywords": ["hello", "hi", "hey"],
      "responses": ["Hello!", "Hi there!", "Hey! How are you?"]
    },
    {
      "keywords": ["schedule", "calendar", "event"],
      "responses": ["Want me to open your schedule?", "Let me show your calendar!"]
    },
    {
      "keywords": ["bye", "goodbye", "see you"],
      "responses": ["Bye!", "See you later!", "Take care!"]
    }
  ],
  "default_responses": ["Hmm?", "I'm listening!", "Tell me more!"]
}
```

### Future LLM Integration Path

1. Add `LLMEngine(ChatEngine)` implementation.
2. Add API key field in SettingsPanel.
3. Add a toggle in settings: "Chat mode: Rules / LLM".
4. The `ChatPanel` calls `engine.respond()` without knowing which engine is active.
5. Optionally add streaming support with `QThread` + signals for token-by-token display.

---

## 8. Suggested Build Order

### Component Dependency Graph

```
                    +-----------+
                    | JsonStore |
                    | (storage) |
                    +-----+-----+
                          |
              +-----------+-----------+
              |                       |
        +-----+------+        +------+------+
        | Data Models |        | AppSettings |
        | (Event, etc)|        +------+------+
        +-----+------+               |
              |                       |
     +--------+--------+             |
     |                  |             |
+----+-----+    +-------+------+     |
|Schedule  |    |ReminderEngine|     |
| Store    |    +-------+------+     |
+----+-----+            |            |
     |                  |            |
     |    +-------------+            |
     |    |                          |
+----+----+----+              +------+------+
|SchedulePanel |              | PetWindow   |
+--------------+              | (core UI)   |
                              +------+------+
                                     |
                         +-----------+-----------+
                         |                       |
                   +-----+------+        +-------+-------+
                   | Animation  |        | ChatBubble    |
                   | Controller |        | ChatPanel     |
                   +-----+------+        +-------+-------+
                         |                       |
                   +-----+------+        +-------+-------+
                   | SpriteAnim |        | ChatEngine    |
                   +------------+        | (Strategy)    |
                                         +---------------+
```

### Build Phases

**Phase 1: Skeleton (no sprites yet)**
- `JsonStore` -- read/write JSON
- `AppSettings` / `CalendarEvent` data models
- `PetWindow` with frameless transparency and placeholder rectangle
- `main.py` entry point with `QApplication`

Test: Window appears on desktop, transparent background, draggable.

**Phase 2: Animation**
- `SpriteAnimator` class
- `AnimationController` with state machine
- `BehaviorScheduler` for autonomous state changes
- Integrate with `PetWindow.paintEvent()`
- Placeholder or first-draft sprite sheets

Test: Pet animates, cycles through states, moves autonomously.

**Phase 3: Interaction**
- Drag-and-drop (mouse events)
- Click reactions (HAPPY state)
- Right-click context menu
- `SystemTray` icon with basic menu

Test: Full mouse interaction works. Tray icon functional.

**Phase 4: Chat**
- `ChatEngine` abstract class
- `RuleBasedEngine` with `chat_rules.json`
- `ChatBubble` widget (speech bubble near pet)
- `ChatPanel` widget (text input + conversation history)

Test: Click pet -> bubble appears. Open chat -> type -> get rule-based response.

**Phase 5: Schedule**
- `ScheduleStore` with CRUD operations
- `SchedulePanel` UI (day/week/month view)
- Event creation/edit dialog
- iCal import/export (optional, can defer)

Test: Create event, view in calendar, persist to JSON.

**Phase 6: Reminders**
- `ReminderEngine` with polling timer
- Wire to pet state (ALERT animation) and ChatBubble (reminder popup)
- Sound notification (optional)
- Recurring event expansion

Test: Create event with reminder -> pet reacts at reminder time.

**Phase 7: Polish**
- `SettingsPanel` (preferences, theme, sound toggle)
- Pet position persistence (save on drag, restore on launch)
- Error handling, edge cases
- Sprite art refinement
- PyInstaller packaging

Test: Full end-to-end workflow. Package as .exe.

### Phase Sizing Rationale

Each phase produces a testable, visible increment. Phases 1-3 form the core pet experience (must work before anything else). Phase 4 (chat) is independent of Phase 5 (schedule) -- they can be developed in parallel if desired. Phase 6 depends on both Phase 4 and Phase 5. Phase 7 is polish and can be partially deferred.

---

## Appendix: Key PySide6 Modules

| Module | Use |
|--------|-----|
| `PySide6.QtWidgets` | QWidget, QLabel, QMenu, QSystemTrayIcon, QDialog |
| `PySide6.QtCore` | QTimer, Signal, Slot, Qt, QPoint, QRect, QPropertyAnimation |
| `PySide6.QtGui` | QPainter, QPixmap, QColor, QFont, QIcon, QAction |
| `pywin32` (optional) | win32gui, win32con for click-through on Windows |
| `ctypes` (stdlib) | Alternative to pywin32 for Win32 API calls |

## Appendix: Cross-Platform Notes

This architecture targets Windows. Key platform-specific items:

- **Click-through**: `WS_EX_TRANSPARENT` is Windows-only. On macOS, use `NSWindow.setIgnoresMouseEvents_()`. On Linux, use `XShapeCombineRectangles`. All require platform-specific code.
- **Window flags**: `Qt.Tool` works on all platforms but behaves slightly differently. Test on each target.
- **Packaging**: PyInstaller works on all three platforms, but `.exe` packaging is Windows-specific.

For v1, Windows-only is acceptable. Cross-platform support can be added by abstracting the click-through logic behind a platform adapter.
