# Requirements — Smart Desktop Pet v1

## v1 Requirements

### Pet Core (宠物核心)
- [ ] **PET-01**: 透明无边框窗口，始终置顶，在桌面上渲染宠物（FramelessWindowHint + WindowStaysOnTopHint + WA_TranslucentBackground）
- [ ] **PET-02**: 鼠标拖拽移动宠物位置（mousePressEvent/mouseMoveEvent/mouseReleaseEvent）
- [ ] **PET-03**: 多状态 Sprite 帧动画（idle、walk、sit、sleep、happy、alert），使用 QPixmap + QTimer 实现
- [ ] **PET-04**: 点击宠物触发动画反馈和对话气泡

### Interaction (交互)
- [ ] **INT-01**: 右键上下文菜单（设置、日程、聊天、退出）
- [ ] **INT-02**: 系统托盘图标，支持快速访问和退出
- [ ] **INT-03**: 聊天对话界面，用户可打字与宠物交互
- [ ] **INT-04**: 规则引擎聊天回复（关键词匹配 + 模板回复）
- [ ] **INT-05**: LLM API 接口预留（Strategy 模式抽象，ChatEngine ABC）

### Schedule (日程)
- [ ] **SCH-01**: 创建/编辑/删除日程事件（标题、时间、描述）
- [ ] **SCH-02**: 多日历支持（颜色区分）
- [ ] **SCH-03**: 事件分类和优先级
- [ ] **SCH-04**: 日程数据导入/导出（JSON 格式）

### Reminder (提醒)
- [ ] **REM-01**: 气泡弹窗提醒（宠物旁弹出对话气泡）
- [ ] **REM-02**: 可配置提醒时间（5分钟/15分钟/1小时/自定义）
- [ ] **REM-03**: 声音通知（QSoundEffect，WAV 格式）

### Data (数据)
- [ ] **DAT-01**: JSON 文件存储（原子写入：write-to-temp + os.replace）
- [ ] **DAT-02**: 设置持久化（宠物位置、偏好、主题）
- [ ] **DAT-03**: 数据 schema 版本管理（嵌入 _schema_version，支持迁移）

### Packaging (打包)
- [ ] **PKG-01**: 使用 PyInstaller 打包为独立 .exe
- [ ] **PKG-02**: 资源路径辅助函数（get_asset_path，兼容打包后路径）
- [ ] **PKG-03**: 系统托盘 .ico 图标

---

## v2 Requirements (Deferred)

- [ ] 日历视图（日/周/月）
- [ ] 重复事件（每日/每周/每月/自定义 RRULE）
- [ ] 设置界面面板（自定义行为、外观、通知）
- [ ] iCal (.ics) 格式导入导出
- [ ] 全屏应用检测（自动隐藏宠物）
- [ ] 宠物自主移动行为（BehaviorScheduler）
- [ ] LLM 聊天集成（接入 OpenAI/Claude API）
- [ ] 多宠物支持

---

## Out of Scope

| 功能 | 原因 |
|------|------|
| 云同步/账号系统 | v1 本地优先，无需网络依赖 |
| Sprite 编辑器 | 使用预制素材，不做编辑工具 |
| 移动端伴侣 | 桌面专属 |
| 语音输入/输出 | 文本聊天足够，语音增加大量复杂度 |
| 物理模拟/重力 | 娱乐性功能，非核心价值 |
| 成就/升级系统 | 偏游戏化，偏离生产力定位 |
| 插件系统 | v1 架构不支持，v2 考虑 |

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PET-01 ~ PET-04 | TBD | Pending |
| INT-01 ~ INT-05 | TBD | Pending |
| SCH-01 ~ SCH-04 | TBD | Pending |
| REM-01 ~ REM-03 | TBD | Pending |
| DAT-01 ~ DAT-03 | TBD | Pending |
| PKG-01 ~ PKG-03 | TBD | Pending |

---
*Last updated: 2026-05-09 — Initial requirements definition*
