---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: otter-enhancement
status: planning
last_updated: "2026-05-11T00:00:00Z"
progress:
  total_phases: 7
  completed_phases: 7
  total_plans: 29
  completed_plans: 29
  percent: 100
---

# State — Smart Desktop Pet

## Phase 6 Complete

Phase 6 (Polish & Packaging) 执行完成，所有 4 个计划已交付。项目 v1.0 全部 6 个阶段完成。

## Progress

| Phase | Name | Status | Plans Done |
| --- | --- | --- | --- |
| 1 | Skeleton & Animation | **Complete** | 4/4 |
| 2 | Interaction | **Complete** | 4/4 |
| 3 | Chat System | **Complete** | 4/4 |
| 4 | Calendar Data Layer | **Complete** | 4/4 |
| 5 | Reminder Engine | **Complete** | 5/5 |
| 6 | Polish & Packaging | **Complete** | 4/4 |
| 7 | Otter Enhancement | **Complete** | 4/4 |

## Phase 4 Summary

| Plan | Name | Wave | Status |
| --- | --- | --- | --- |
| P4.1 | 事件数据模型 + 存储 | 0 | ✓ Complete |
| P4.2 | 多日历支持 | 0 | ✓ Complete |
| P4.3 | 日程面板 UI | 1 | ✓ Complete |
| P4.4 | 导入导出 | 2 | ✓ Complete |

## Phase 4 Deliverables

- **Event**: 事件数据模型（title, datetime, category, priority, calendar_id, deadline_str, status）
- **ScheduleStore**: 事件 CRUD + JSON 导入导出
- **Calendar**: 日历数据模型（name, color）
- **CalendarStore**: 日历 CRUD，默认日历
- **CalendarGrid**: 月历网格组件（月份导航、事件日期高亮、点击选择日期）
- **SchedulePanel**: 日程面板（月历视图 + 事件列表 + 日历管理）
- **EventDialog**: 事件编辑对话框（支持截止时间设置）
- **导入导出**: Markdown/纯文本/JSON 多格式导入 + 自动事件提取
- **导出**: 默认导出为 Markdown 格式
- **右键菜单**: 事件右键菜单（编辑/标记完成/取消标记完成/删除）
- **粘贴导入**: 打开文本框，支持粘贴各种格式内容

## Phase 5 Summary

| Plan | Name | Wave | Status |
| --- | --- | --- | --- |
| P5.1 | 提醒引擎核心 (TDD) | 0 | ✓ Complete |
| P5.2 | ALERT 动画状态 | 1 | ✓ Complete |
| P5.3 | 音效 + UI 集成 | 2 | ✓ Complete |
| P5.4 | 托盘提醒开关 | 3 | ✓ Complete |
| P5.5 | EventDialog 提醒时间选择 (Gap) | 3 | ✓ Complete |

### Phase 5 Deliverables

- **ReminderEngine**: 60 秒轮询、去重、抑制、提醒窗口检测
- **PetState.ALERT**: 新增提醒警报动画状态（抖动 + 红色感叹号）
- **SoundManager**: QSoundEffect 音效播放，支持静音
- **reminder.wav**: 双音提示音（880→1320 Hz）
- **托盘提醒开关**: "关闭提醒"/"开启提醒" 切换
- **EventDialog**: 提醒时间 QComboBox（5/15/30/60 分钟）
- **28+ 测试用例**: 提醒引擎、超时检测器、音效管理器、日程面板

## Phase 7 Summary (Complete)

| Plan | Name | Wave | Status |
| --- | --- | --- | --- |
| P7.1 | 扩展状态 + 水獭外观 | 0 | ✓ Complete |
| P7.2 | 屏幕移动 + 行为调度 | 1 | ✓ Complete |
| P7.3 | 状态头标 + 过渡动画 | 2 | ✓ Complete |
| P7.4 | 节日换装系统 | 3 | ✓ Complete |

### Phase 7 目标

- 新增 4 个状态：EAT（吃鱼）、PLAY（玩石头）、GROOM（梳理毛发）、REST（晒太阳）
- WALK 状态满屏幕走动（MovementController）
- 状态头标 emoji 指示器（StateIndicator）
- 300ms alpha 渐变过渡动画（TransitionAnimator）
- 节日自动换装（HolidayEngine + CostumeRenderer）
- 水獭外观重绘（流线型身体、短耳、蹼足、长尾）

### Phase 7.4 交付物

- **data/holidays.json**: 6 个节日数据（春节/中秋/端午/国庆/元旦/儿童节），支持农历和公历
- **data/costumes.json**: 6 个节日服装的 QPainter 绘制指令（灯笼帽/月饼/龙帽/国旗丝带/派对帽/气球）
- **pet/holiday_engine.py**: HolidayEngine 类，每小时检查节日，发射 holiday_active/holiday_ended 信号
- **pet/costume.py**: CostumeRenderer 类，根据绘制指令叠加服装到精灵上
- **data/settings.py**: 添加 costume_enabled 字段，Schema 版本 v1→v2 迁移
- **main.py**: 集成换装系统，右键菜单"节日换装"开关
- **pet/window.py**: 添加 costume_toggle 信号和菜单项

### 全屏透明窗口改造

- **pet/window.py**: 窗口全屏化，精灵位置改为窗口内偏移(_sprite_x, _sprite_y)，移除 setMask，鼠标只在精灵范围内响应
- **pet/movement.py**: 使用 set_sprite_position() 移动精灵坐标，修复硬编码 256 的边界问题
- **pet/indicator.py**: 连接线装饰、大小自适应(scale)、paintEvent 先清除防闪烁
- **main.py**: 适配新接口，初始化精灵位置和指示器缩放

**效果**: 窗口覆盖整个屏幕且完全透明，用户只看到水獭"浮"在桌面上，没有框

## Phase 6 Summary

| Plan | Name | Wave | Status |
| --- | --- | --- | --- |
| P6.1 | 资源路径助手 (TDD) | 0 | ✓ Complete |
| P6.2 | JSON Schema 版本管理 (TDD) | 0 | ✓ Complete |
| P6.3 | 系统托盘 .ico 图标 | 1 | ✓ Complete |
| P6.4 | PyInstaller 打包 | 2 | ✓ Complete |

### Phase 6 Deliverables

- **get_asset_path()**: 集中式资源路径解析，支持开发模式和 PyInstaller 冻结模式
- **utils/assets.py**: 资源路径助手模块
- **Migration Registry**: JsonStore 迁移注册表 + register_migration() 装饰器
- **ScheduleStore / CalendarStore**: 自动 Schema 版本管理
- **assets/icon.ico**: 多分辨率像素风 .ico（16x16 + 32x32）
- **scripts/generate_icon.py**: Pillow 图标生成脚本
- **desktop_pet.spec**: PyInstaller --onedir 打包配置
- **dist/SmartDesktopPet/**: 独立 .exe 输出（1.7 MB）
- **14+ 测试用例**: 资源路径、迁移注册表、图标验证

## AI 生成工具集成

| 脚本 | 功能 | API 模型 |
| --- | --- | --- |
| `scripts/generate_arch_diagram.py` | 生成项目架构图 | sensenova-u1-fast（文生图） |
| `scripts/generate_ppt.py` | 生成介绍 PPT | sensenova-6.7-flash-lite（LLM） |

- 使用 SenseNova 平台 API（OpenAI 兼容协议）
- 输出统一保存在 `output/` 目录
- 支持自定义提示词和 PPT 页数

## Blockers

(None)

---

Last updated: 2026-05-12 — 全屏透明窗口改造完成，水獭直接浮在桌面
