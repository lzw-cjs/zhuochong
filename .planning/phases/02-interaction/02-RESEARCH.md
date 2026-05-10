---
phase: 02-interaction
status: skipped
---

# Phase 2: Interaction — Research

**状态：跳过** — 早期阶段（Phase 1-3）使用了 discuss-phase 直接规划，未单独进行研究。Phase 2 的技术栈（PySide6 事件处理、QSystemTrayIcon、QMenu）均为 PySide6 标准 API，无需额外研究。

## 技术要点

- 拖拽：mousePressEvent / mouseMoveEvent / mouseReleaseEvent
- 系统托盘：QSystemTrayIcon + QMenu
- 气泡：自定义 QWidget + QTimer 自动隐藏
- 右键菜单：QMenu + QAction
