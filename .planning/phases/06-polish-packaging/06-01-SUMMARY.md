---
phase: 6
plan: 06-01
subsystem: utils
tags: [tdd, asset-paths, pyinstaller, refactoring]
depends_on: []
provides: [get_asset_path]
affects: [main.py, pet/chat_engine.py]
tech_stack:
  added: []
  patterns: [centralized-path-resolution]
key_files:
  created:
    - utils/__init__.py
    - utils/assets.py
    - tests/test_asset_path.py
  modified:
    - main.py
    - pet/chat_engine.py
decisions:
  - Used Path.parts comparison instead of str.endswith for cross-platform test assertions
metrics:
  duration: ~5 minutes
  completed: "2026-05-10"
  tasks_completed: 2
  tasks_total: 2
---

# Phase 6 Plan 01: Centralized Asset Path Helper Summary

TDD implementation of `get_asset_path()` that resolves asset paths correctly in both development and PyInstaller-frozen modes.

## Tasks Completed

### Task 1: Create utils/assets.py with get_asset_path() (TDD)

**RED phase:** Created `tests/test_asset_path.py` with 4 tests covering:
- Dev mode returns absolute path
- Dev mode base is project root (parent of utils/)
- Frozen mode uses sys._MEIPASS
- Frozen mode resolves data/ paths

Tests initially failed with `ModuleNotFoundError: No module named 'utils'`.

**GREEN phase:** Created `utils/__init__.py` (empty) and `utils/assets.py` with `get_asset_path()` function. All 4 tests passed.

**Deviation [Rule 1 - Bug]:** Fixed cross-platform path separator issue in test assertions. The original test used `str(result).endswith("assets/sounds")` which fails on Windows because `str(Path)` uses backslashes. Changed to `result.parts[-2:] == ("assets", "sounds")` for platform-agnostic comparison.

**Commits:**
- `c5aa88a` - test(06-01): add failing test for asset path helper
- `afb3d48` - feat(06-01): implement get_asset_path() for dev and frozen modes

### Task 2: Replace hardcoded asset paths

Updated two files to use `get_asset_path()` instead of hardcoded paths:

- `main.py`: Changed `SoundManager(Path("assets/sounds"))` to `SoundManager(get_asset_path("assets/sounds"))`. Removed unused `from pathlib import Path` import.
- `pet/chat_engine.py`: Changed `Path(__file__).parent.parent / "data" / "chat_rules.json"` to `get_asset_path("data/chat_rules.json")`. Kept `Path` import (still used in type hints).

**Commit:** `39adef9` - refactor(06-01): replace hardcoded asset paths with get_asset_path()

## Verification Results

- All 4 asset path tests pass
- `grep -n 'Path("assets' main.py` returns 0 matches
- `grep -n '__file__.*parent.*parent.*data' pet/chat_engine.py` returns 0 matches

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed cross-platform path separator in test assertions**
- **Found during:** Task 1 GREEN phase
- **Issue:** `str(result).endswith("assets/sounds")` fails on Windows because `Path` uses backslashes
- **Fix:** Changed to `result.parts[-2:] == ("assets", "sounds")` for platform-agnostic comparison
- **Files modified:** tests/test_asset_path.py
- **Commit:** c5aa88a

**2. [Rule 3 - Blocking] Disabled langsmith pytest plugin**
- **Found during:** Task 1 test execution
- **Issue:** langsmith pytest plugin has broken pydantic dependency (`validate_core_schema` import error)
- **Fix:** Used `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` to skip plugin loading. pytest.ini already had `addopts = -p no:langsmith` but the plugin crashes before pytest processes addopts.
- **Files modified:** None (environment workaround)

**3. [Rule 3 - Blocking] Found correct Python executable**
- **Found during:** Task 1 test execution
- **Issue:** `python` command on PATH points to Windows Store stub (exit code 49)
- **Fix:** Used `/c/Users/李打爷的电脑/Desktop/python.exe` (Python 3.12.4) for all test runs
- **Files modified:** None (environment workaround)

## Threat Flags

None - no new security surface introduced.

## Self-Check: PASSED

- FOUND: utils/__init__.py
- FOUND: utils/assets.py
- FOUND: tests/test_asset_path.py
- FOUND: 06-01-SUMMARY.md
- FOUND: c5aa88a (test commit)
- FOUND: afb3d48 (feat commit)
- FOUND: 39adef9 (refactor commit)
- FOUND: 51f7593 (docs commit)
