<!-- GSD:project-start source:PROJECT.md -->
## Project

**Smart Desktop Pet (智能桌面宠物)**

A pixel-art desktop pet application built with Python + PySide6. The pet lives on the user's desktop as a small animated creature that they can interact with, manage schedules through, and receive reminders from. Think of it as a modern take on classic desktop pets (like Shimeji or the old Windows BonziBuddy), but with practical utility built in.

**Core Value:** A pixel-art pet that is both charming to interact with AND practically useful for schedule management. If either half fails — ugly animations or broken reminders — the whole thing falls apart.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

**Key decisions** (detailed analysis: [`.claude/rules/tech-stack.md`](.claude/rules/tech-stack.md)):

| Layer | Choice | Why |
|---|---|---|
| GUI Framework | **PySide6** | LGPL, Qt Company maintained, full animation support |
| Animation | **Sprite Sheet** (primary) + GIF (fallback) | Full 8-bit alpha, zero deps, deterministic frame control |
| Audio | **QSoundEffect** | Built-in to PySide6, low latency, no extra deps |
| Calendar | **icalendar** + **recurring-ical-events** | Full RFC 5545, active maintenance |
| Packaging | **PyInstaller** (dev) / **Nuitka** (prod) | Easy builds / native performance |
| Storage | **JSON** with atomic writes + filelock | Simple, crash-safe, schema-versioned |

### Key Dependencies
```
PySide6>=6.8.0, PySide6-Addons, icalendar>=5.0, recurring-ical-events>=3.0, filelock>=3.13
```

### Known Issues
- Qt 6.7+ translucent windows: set `WA_TranslucentBackground` after show, use `QSG_RHI_BACKEND=opengl`
- PyInstaller AV false positives: consider Nuitka for production
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
