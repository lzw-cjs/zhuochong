# Phase 2 Context — Interaction

## Scope

Phase 2 adds user interaction to the desktop pet: drag-and-drop movement, click feedback with speech bubbles, right-click context menu, and system tray integration.

**Requirements:** PET-02, PET-04, INT-01, INT-02

## Decisions

### D-01: Drag Detection Threshold
- Distinguish click from drag using a 5px movement threshold
- If mouse moves < 5px between press and release, treat as click
- If mouse moves >= 5px, treat as drag

### D-02: Screen Bounds Constraint
- Constrain pet window to stay within screen bounds during drag
- Use QScreen.availableGeometry() to get usable screen area
- Pet cannot be dragged off-screen

### D-03: ChatBubble Design
- Small floating widget anchored above the pet
- Auto-dismiss after 3 seconds (configurable later)
- Semi-transparent white background with rounded corners
- Pixel-art font if available, fallback to system font
- Maximum width 200px, word-wrap enabled

### D-04: Context Menu Items
- Right-click menu: Schedule, Chat, Settings, Exit
- Schedule/Chat/Settings emit signals (wired in Phase 3+)
- Exit triggers app.quit()

### D-05: System Tray
- Use QSystemTrayIcon with a 16x16 icon
- Right-click menu: Show/Hide Pet, Exit
- Double-click toggles pet visibility
- Placeholder icon generated programmatically (no .ico file yet)

### D-06: Click → BehaviorScheduler Integration
- Clicking the pet calls BehaviorScheduler.on_user_interaction()
- This triggers happy state for 10 seconds, then returns to idle

## Dependencies from Phase 1

- PetWindow (pet/window.py): transparent frameless window, position_changed signal
- SpriteAnimator (pet/animator.py): state machine with set_state()
- BehaviorScheduler (pet/behavior.py): on_user_interaction() method
- Settings (data/settings.py): position persistence
