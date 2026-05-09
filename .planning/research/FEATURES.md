# Desktop Pet Application — Feature Research

Research compiled 2026-05-09. Sources: Shimeji-ee, Desktop Goose, Tamagotchi, Spirit City: Lofi Sessions, VS Code Pets, Bongo Cat, Habitica, and general desktop pet ecosystem analysis.

---

## 1. Existing Desktop Pet Apps — Feature Inventory

### Shimeji-ee (Open Source, Java)
- Small animated sprites that walk across the desktop
- Window interaction: climb window edges, sit on taskbar, drag windows
- Mouse interaction: pick up, throw, drag the pet
- Gravity/physics simulation (falling, bouncing)
- Multiple instances (spawn copies)
- Custom sprite sheets (community-created characters)
- XML-configurable behavior probabilities and timings
- Idle, walking, climbing, falling, sitting states
- No productivity features — purely decorative/entertaining

### Desktop Goose (Samperson, Unity)
- Aggressive/chaotic behavior: chases cursor, steals mouse control
- Delivers custom memes/images from a folder onto the screen
- Leaves "dirty footprints" and virtual poop on screen
- Honking sound effects
- Cannot be easily dismissed (runs away from clicks)
- Customizable content (drop images into folder for goose to deliver)
- Purely entertainment/disruption — zero utility

### Tamagotchi (Bandai, Hardware/Virtual)
- Needs system: hunger, happiness, discipline, health, hygiene
- Feeding (meals vs snacks), playing mini-games, cleaning waste
- Evolution system: care quality determines adult form
- Life cycle: egg → baby → child → teen → adult → death
- Persistent state — pet exists even when ignored (and suffers)
- Punishes neglect (sickness, bad evolutions, death)
- Later versions: marriage, breeding, jobs, items, currency

### Spirit City: Lofi Sessions (Steam)
- Collectible spirit companions on desktop
- Productivity tools: to-do lists, Pomodoro timer, journaling
- Ambient environments (bedroom, cafe) with lofi music
- Wellness features: mood check-ins, breathing exercises, sleep timer
- Character customization and room decoration
- Designed to run alongside other work without disruption

### VS Code Pets (VS Code Extension)
- Small pet lives in the editor panel
- Reacts to typing activity
- Multiple pet types (cat, dog, snake, rubber duck)
- Basic idle animations
- Minimal resource usage
- Zero configuration required

### Bongo Cat (Desktop)
- Cat that mimics your typing/mouse movements
- Plays bongo drums synchronized to keystrokes
- Pure novelty — no utility, high charm

---

## 2. Feature Analysis by Category

### TABLE STAKES (Must-have for v1)

These are non-negotiable. Users will consider the app broken without them.

| Feature | Complexity | Dependencies | Notes |
|---------|-----------|-------------|-------|
| Pet renders on desktop (transparent frameless window) | Medium | PySide6 transparency support | Core technical requirement |
| Always-on-top window behavior | Low | OS-level window flags | Must not interfere with other apps |
| Drag-to-reposition pet anywhere on screen | Low | Mouse event handling | Users expect this immediately |
| Idle animations (at minimum 2-3 states) | Medium | Sprite sheet art | Idle, sleeping, happy |
| Click interaction with visual feedback | Low | Event handling + animation trigger | Pet reacts to being clicked |
| Pet does not block normal desktop use | Medium | Window management, hit testing | Transparent hit areas, small footprint |
| System tray icon for quick access | Low | PySide6 QSystemTrayIcon | Minimize/restore, exit |
| Settings persistence (position, preferences) | Low | JSON storage | Pet remembers where user placed it |
| Low CPU/memory usage | Medium | Efficient animation loop | QTimer-based, not busy-waiting |
| Graceful startup and shutdown | Low | App lifecycle | No ghost processes, clean exit |

### DIFFERENTIATORS (Competitive advantage)

This is where the project stands out. Most desktop pets have NONE of these.

| Feature | Complexity | Dependencies | Notes |
|---------|-----------|-------------|-------|
| **Integrated calendar view (day/week/month)** | High | Custom calendar widget, data model | No desktop pet does this well |
| **Pet-delivered reminders** | Medium | Reminder engine + animation system | Reminders come FROM the pet, not OS toast |
| **Rule-based chat companion** | Medium | Keyword engine, response templates | Personality without LLM dependency |
| **Chat bubble UI for interactions** | Low-Medium | Popup widget with auto-dismiss | Non-intrusive communication |
| **Recurring events support** | Medium | RRULE logic or custom recurrence | Daily/weekly/monthly/custom patterns |
| **Multiple color-coded calendars** | Low | Calendar data model with categories | Work, personal, health, etc. |
| **iCal import/export** | Medium | icalendar library parsing | Interop with Google/Apple/Outlook |
| **Right-click context menu** | Low | QMenu customization | Quick access to all features |
| **Configurable reminder timing** | Low | Settings + timer logic | 5min, 15min, 1hr, custom before event |
| **LLM-ready chat abstraction** | Low | Strategy pattern interface | Clean seam for future AI upgrade |

### ANTI-FEATURES (Do NOT build in v1)

Building these will delay launch without proportional value. Each has a reason it is excluded.

| Feature | Why NOT in v1 | When to Revisit |
|---------|--------------|-----------------|
| **Multi-pet support** | Dramatically increases animation, state, and rendering complexity. One pet is enough to prove the concept. | After v1 proves single-pet engagement |
| **Pet needs/hunger system** | Tamagotchi-style care creates obligation fatigue. Users already have calendar reminders — adding feeding schedules is annoying. Also requires persistent state simulation. | Only if users request "more interaction" |
| **Mini-games** | Massive scope (game design, input handling, scoring). Distracts from core value of schedule + companion. | v2+ if engagement metrics demand it |
| **Evolution/leveling system** | Requires long-term state tracking, achievement logic, multiple sprite sets. Adds gamification that may feel hollow. | After establishing user retention patterns |
| **Cloud sync / account system** | Network code, auth, server costs, privacy concerns. v1 is local-only by design. | Only with proven user base |
| **Voice input/output** | Speech recognition and TTS add massive dependencies and complexity. Text chat is sufficient. | When LLM integration is mature |
| **Sprite/customization editor** | Building a pixel art editor is a separate product. Use pre-made sprites. | Community contributions or asset packs |
| **Mobile companion** | Cross-platform mobile is a different project. Desktop-only focus. | Separate product track |
| **Physics simulation** | Realistic gravity, collision, ragdoll — overkill for a small sprite. Simple position-based movement is enough. | Never, unless the pet becomes a physics sandbox |
| **Inventory/collectibles** | Item systems are feature creep magnets. Adds UI complexity, save data bloat. | Only if the pet evolves into a virtual world |
| **Social features (sharing, multiplayer)** | Desktop pets are inherently personal. Networking adds servers, auth, moderation. | Separate product track |
| **Achievement/trophy system** | Premature gamification. Adds UI, tracking, notification complexity for uncertain engagement gain. | After user research shows demand |
| **Plugin/extension system** | Architectural complexity for hypothetical community. Build the core first. | After v1 proves the platform |

---

## 3. Calendar/Schedule Features — Essential vs Nice-to-Have

### Essential (v1)

| Feature | Complexity | Rationale |
|---------|-----------|-----------|
| Create event (title, date/time, description) | Low | Core CRUD — cannot have a calendar without this |
| Edit event | Low | Users make mistakes, plans change |
| Delete event | Low | Basic data management |
| Day view | Medium | Primary view for "what's happening today" |
| Week view | Medium | Planning ahead without overwhelming detail |
| Month view | Medium | At-a-glance overview |
| Recurring events (daily, weekly, monthly) | Medium | Most real schedules have recurring items |
| Event categories with color coding | Low | Visual organization (work/personal/health) |
| Configurable reminder alerts | Low | Core value prop — pet reminds you |
| Local JSON storage | Low | Already in tech stack |

### Nice-to-Have (v1.1 or v2)

| Feature | Complexity | Rationale |
|---------|-----------|-----------|
| Custom recurrence patterns (every 2 weeks, weekdays only) | Medium | Edge cases, but useful for real schedules |
| Multiple calendar support (separate calendars) | Medium | Work vs personal separation |
| iCal import/export | Medium | Interop with existing calendar apps |
| Event priority levels (high/medium/low) | Low | Adds visual noise, simple categories suffice |
| Natural language event creation ("meet John at 3pm") | High | NLP parsing, significant complexity |
| Drag-to-reschedule in calendar view | Medium | Nice UX but requires complex widget interaction |
| Search across events | Low | Useful once you have many events |
| Agenda/list view (flat sorted list) | Low | Alternative to grid views |

---

## 4. Chat Companion Features — What Works in Rule-Based Systems

### What Works Well

| Approach | Complexity | Example |
|----------|-----------|---------|
| **Keyword matching with templates** | Low | User says "hello" → pet responds with greeting from pool |
| **Mood/emotion keyword detection** | Low | Detect "sad", "tired", "happy" → appropriate response |
| **Time-aware responses** | Low | "Good morning!" before noon, "Working late?" after 10pm |
| **Contextual idle chatter** | Low | Pet proactively says things based on time since last interaction |
| **Fallback variety** | Low | Multiple "I don't understand" responses to avoid repetition |
| **Personality-consistent responses** | Medium | All responses match a defined character voice |
| **Schedule-aware chat** | Medium | "You have a meeting in 30 minutes!" integration |
| **Slot-filling templates** | Low | "Hello {username}!" using stored settings |

### What Does NOT Work in Rule-Based Systems

| Approach | Why It Fails |
|----------|-------------|
| Open-ended conversation | Rule systems cannot handle arbitrary topics |
| Remembering conversation history | Context window is expensive to implement correctly |
| Humor/jokes | Forced jokes from templates feel robotic fast |
| Complex multi-turn dialogue | Decision trees explode in size |
| Personality depth | Limited by response pool size |

### Recommended Chat Architecture for This Project

```
User Input
    ↓
Keyword/Pattern Matcher (priority-ordered rules)
    ↓
Context Augmenter (time of day, schedule state, pet mood)
    ↓
Template Response Selector (weighted random from matching pool)
    ↓
Slot Filler (username, event names, time references)
    ↓
Output (displayed in chat bubble)
```

Key design points:
- **Priority-ordered rules**: Specific patterns match before general ones
- **Response pools**: Multiple responses per rule, randomly selected
- **Cooldown timers**: Prevent the pet from spamming the same response
- **State awareness**: Pet knows if it was recently interacted with, if events are upcoming, time of day
- **Clean strategy interface**: Swap in LLM later without rewriting the UI

---

## 5. Competitive Landscape Summary

| App | Desktop Presence | Schedule/Utility | Chat/Personality | Open Source |
|-----|:---:|:---:|:---:|:---:|
| Shimeji-ee | Strong | None | None | Yes |
| Desktop Goose | Strong | None | None | No |
| Tamagotchi | Weak (app) | None | None | No |
| Spirit City | Medium | Some (to-do, timer) | None | No |
| VS Code Pets | Niche | None | None | Yes |
| **This Project** | **Strong** | **Full calendar** | **Rule-based** | **TBD** |

**The gap**: No existing desktop pet combines full calendar functionality with a personality-driven companion. This is the unique positioning.

---

## 6. Complexity Budget (v1 Feasibility)

Estimated relative effort by area:

```
Pet rendering + animation    ████████░░  ~25%  (sprite work + PySide6 window)
Calendar/schedule system     ██████████  ~30%  (CRUD, views, recurrence, storage)
Chat engine                  ████░░░░░░  ~12%  (keyword matching, templates)
Reminder system              ███░░░░░░░  ~10%  (timers, popup, sound)
UI panels (settings, etc.)   ████░░░░░░  ~12%  (settings, context menu, tray)
Packaging + polish           ███░░░░░░░  ~11%  (PyInstaller, testing, edge cases)
```

Calendar is the largest single subsystem. The pet/animation work is mostly art-dependent. Chat is intentionally simple.

---

## 7. Recommendations

1. **Ship the calendar first as a standalone widget**, then attach the pet to it. This de-risks the hardest subsystem.
2. **Start with 3-4 sprite states** (idle, happy, alert, sleeping). More states can be added post-launch.
3. **Keep chat responses to ~50-100 templates** for v1. This is enough personality without maintenance burden.
4. **Avoid the Tamagotchi trap** — do not add needs/feeding/hunger. It creates obligation, not delight.
5. **The reminder-as-chat-bubble is the killer feature** — make this feel magical, not like a system notification wearing a costume.
6. **Test early with real schedules** — the calendar must handle real-world edge cases (timezone, all-day events, overlapping) or users will abandon it.
