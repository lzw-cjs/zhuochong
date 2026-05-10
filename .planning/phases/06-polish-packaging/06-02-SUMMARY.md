---
phase: 06
plan: 02
name: "Schema Versioning Infrastructure"
subsystem: data
tags: [store, migration, schema, tdd]
requires: []
provides: [migration-registry, schema-version-support]
affects: [data/store.py, data/schedule_store.py, data/calendar_store.py]
tech_stack:
  added: []
  patterns: [migration-registry, decorator-registration, backup-before-migrate]
key_files:
  created:
    - tests/test_store_migration.py
  modified:
    - data/store.py
    - data/schedule_store.py
    - data/calendar_store.py
decisions:
  - "Decorator-based migration registration via @register_migration(store_name, from_version)"
  - "Backup .json.bak before running any migrations"
  - "Default store_name derived from filename stem"
metrics:
  duration: ~10m
  completed: "2026-05-10"
  tasks_completed: 2
  tasks_total: 2
  files_changed: 4
---

# Phase 06 Plan 02: Schema Versioning Infrastructure Summary

Migration registry for JsonStore enabling safe schema evolution with decorator-registered migrations and automatic backup.

## Tasks Completed

### Task 1: Add migration registry to JsonStore (TDD)

**RED phase:** Created `tests/test_store_migration.py` with 7 tests covering:
- Registration decorator stores functions in `_MIGRATIONS`
- Migrations run on version mismatch
- Migrations skipped when versions match
- Default returned when file missing (no migration)
- Sequential chaining (v1->v2->v3)
- Existing data preservation during migration
- Migrated data persisted to disk

Confirmed tests fail with `ImportError: cannot import name 'register_migration'`.

**GREEN phase:** Updated `data/store.py`:
- Added `_MIGRATIONS: dict[str, dict[int, Callable]]` registry at module level
- Added `register_migration(store_name, from_version)` decorator
- Added `store_name` parameter to `JsonStore.__init__()` (defaults to filename stem)
- Extended `load()` with `current_version` parameter
- Added `_migrate()` method that chains migrations sequentially
- Added `shutil.copy2` backup before running migrations (`.json.bak`)

All 7 tests pass.

**Commit:** `32e80b8` - `feat(06-02): add migration registry to JsonStore with TDD`

### Task 2: Update ScheduleStore and CalendarStore

Updated `data/schedule_store.py`:
- Added `SCHEDULE_SCHEMA_VERSION = 1`
- Passed `store_name="events"` to `JsonStore` constructor
- `_load_events()` passes `current_version=SCHEDULE_SCHEMA_VERSION`
- `_save_events()` includes `_schema_version` in saved dict

Updated `data/calendar_store.py`:
- Added `CALENDAR_SCHEMA_VERSION = 1`
- Passed `store_name="calendars"` to `JsonStore` constructor
- `_load()` passes `current_version=CALENDAR_SCHEMA_VERSION`
- `_save()` includes `_schema_version` in saved dict

**Commit:** `418e040` - `feat(06-02): wire schema versioning into ScheduleStore and CalendarStore`

## Verification

- `pytest tests/test_store_migration.py` -- 7/7 passed
- `grep -n 'current_version' data/schedule_store.py` -- line 18 confirmed
- `grep -n 'current_version' data/calendar_store.py` -- line 17 confirmed
- Existing tests (test_overdue_detector, test_asset_path, test_reminder_engine) -- no regressions

## Deviations from Plan

None -- plan executed exactly as written.

## Known Stubs

None.

## Threat Flags

None -- no new network endpoints, auth paths, or trust boundary changes.
