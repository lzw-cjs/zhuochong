---
phase: 06
plan: 04
name: "PyInstaller Packaging"
subsystem: packaging
tags: [pyinstaller, packaging, distribution]
requires: [06-03]
provides: [pyinstaller-spec, frozen-check]
affects: [main.py, desktop_pet.spec]
tech_stack:
  added: [PyInstaller 6.20.0]
  patterns: [--onedir mode, frozen path detection]
key_files:
  created: [desktop_pet.spec]
  modified: [main.py]
decisions:
  - "Use --onedir mode instead of --onefile for faster startup and smaller exe"
  - "Exclude unused PySide6 modules (WebEngine, 3D, etc.) to reduce bundle size"
  - "Set QT_PLUGIN_PATH in frozen mode to ensure Qt platform plugins are found"
metrics:
  tasks_completed: 2
  duration_seconds: ~300
  completed_at: "2026-05-10"
---

# Phase 06 Plan 04: PyInstaller Packaging Summary

PyInstaller --onedir packaging configured with frozen path detection for the Smart Desktop Pet.

## Tasks Completed

### Task 1: Install PyInstaller and create desktop_pet.spec
- Installed PyInstaller 6.20.0 via pip
- Created `desktop_pet.spec` with --onedir mode configuration
- Configured PySide6 data/binary collection via `collect_data_files` and `collect_dynamic_libs`
- Bundled project assets: `assets/` directory and `data/chat_rules.json`
- Excluded 30+ unused PySide6 modules to reduce bundle size
- Set `console=False` for windowed mode

### Task 2: Add frozen check to main.py and verify build
- Added frozen path detection at lines 8-9 of `main.py`
- Sets `QT_PLUGIN_PATH` to `sys._MEIPASS/PySide6/Qt/plugins` when running from PyInstaller bundle
- Ran full PyInstaller build (completed in ~2 minutes)
- Verified all expected outputs exist:
  - `dist/SmartDesktopPet/SmartDesktopPet.exe` (1.7 MB)
  - `dist/SmartDesktopPet/_internal/assets/sounds/reminder.wav` (22 KB)
  - `dist/SmartDesktopPet/_internal/data/chat_rules.json` (5 KB)

## Verification Results

| Check | Result |
|-------|--------|
| `grep -n 'frozen' main.py` | Lines 8-9: QT_PLUGIN_PATH setting present |
| `ls dist/SmartDesktopPet/SmartDesktopPet.exe` | 1.7 MB executable exists |
| `ls dist/SmartDesktopPet/_internal/assets/sounds/reminder.wav` | 22 KB bundled asset exists |
| `ls dist/SmartDesktopPet/_internal/data/chat_rules.json` | 5 KB bundled data exists |

## Deviations from Plan

None - plan executed exactly as written.

## Key Decisions

1. **--onedir over --onefile**: Chosen for faster startup (no extraction step) and smaller exe size. The `_internal/` directory structure is standard for PyInstaller 6.x.

2. **Excluded PySide6 modules**: 30+ modules excluded (WebEngine, 3D, Charts, etc.) to significantly reduce bundle size without affecting core pet functionality.

3. **QT_PLUGIN_PATH detection**: Required for frozen mode because PySide6's platform plugins (QWindows.dll, etc.) live under `_internal/PySide6/Qt/plugins/` rather than the normal install path.

## Files Modified

| File | Action | Description |
|------|--------|-------------|
| `desktop_pet.spec` | Created | PyInstaller spec with --onedir mode, asset bundling, module exclusions |
| `main.py` | Modified | Added frozen path detection for QT_PLUGIN_PATH |
