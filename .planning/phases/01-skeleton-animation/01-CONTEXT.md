# Phase 1: Skeleton & Animation - Context

**Gathered:** 2026-05-09
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase delivers a pixel-art sloth pet that appears on the user's desktop in a transparent frameless window, cycles through idle/walk/sit/sleep/happy/alert animations, and persists its position and settings across restarts. No interaction features (drag, click, menu) — that's Phase 2.

</domain>

<decisions>
## Implementation Decisions

### Sprite 素材设计
- **D-01:** Sprite 尺寸 32x32 像素，经典像素风
- **D-02:** 动物形象：树懒 (sloth)
- **D-03:** 素材方案：先用占位素材（代码生成简单占位图），后续替换为正式像素画
- **D-04:** Phase 1 动画状态：idle（挂在树枝上）、walk（缓慢爬行）、sleep（蜷缩睡觉）、happy（开心摇晃）
- **D-05:** 每个状态需要 Sprite 帧序列（建议每状态 4-8 帧，QTimer 驱动帧循环）

### 窗口行为细节
- **D-06:** 宠物窗口不在 Windows 任务栏中显示（Qt.Tool 标志）
- **D-07:** 智能置顶——正常情况始终置顶，但全屏应用（游戏/视频）时自动隐藏
- **D-08:** 多显示器自由跨屏，拖拽不受限制
- **D-09:** Windows 11 注意：RHI 渲染可能导致透明窗口问题，需设置 QSG_RHI_BACKEND=opengl 环境变量

### 数据存储结构
- **D-10:** 数据文件存放在 %APPDATA%/SmartDesktopPet/ 目录
- **D-11:** 持久化内容：宠物位置 (x, y)、宠物状态 (当前动画)、基础偏好 (音量/静音/自启动)、日历配置
- **D-12:** 使用 JSON 原子写入模式（write-to-temp + os.replace）
- **D-13:** 每个 JSON 文件嵌入 _schema_version 字段，支持未来迁移

### 宠物行为模式
- **D-14:** 无用户交互时，宠物原地切换动画状态（不移动位置）
- **D-15:** 状态切换逻辑：基于定时器的随机切换（如 5 分钟无操作 → sleep，操作后 → happy → idle）

### Claude's Discretion
- 项目结构组织方式（模块划分、文件命名）
- 具体的 PySide6 窗口标志组合
- Sprite 素材的帧数和帧率
- 数据模型的具体字段设计
- 占位素材的生成方式（代码绘制 vs 预制 PNG）

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Research
- `.planning/research/STACK.md` — 技术栈推荐（PySide6、Sprite、QSoundEffect、PyInstaller）
- `.planning/research/ARCHITECTURE.md` — 架构模式（窗口标志、动画引擎、数据层设计）
- `.planning/research/PITFALLS.md` — 常见坑点（DPI、透明窗口、内存泄漏）
- `.planning/research/SUMMARY.md` — 研究汇总

### Requirements
- `.planning/REQUIREMENTS.md` — v1 需求（PET-01, PET-03, DAT-01, DAT-02 为本阶段）
- `.planning/PROJECT.md` — 项目上下文和核心价值

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- 无现有代码——Greenfield 项目

### Established Patterns
- 研究建议使用 `QPixmap + QTimer + custom paintEvent()` 实现动画
- 研究建议自定义状态机（enum + transition table），避免 Qt 的 QStateMachine
- 研究建议原子 JSON 写入（write-to-temp + os.replace）+ filelock

### Integration Points
- 无——本阶段是项目骨架，后续阶段在此基础上构建

</code_context>

<specifics>
## Specific Ideas

- 树懒形象：挂在树枝上的 idle 动画是核心视觉特征，需要突出"慢悠悠"的感觉
- 占位素材：先用简单几何形状（圆形+线条）表示树懒，确保动画引擎正常工作后再替换正式素材
- 全屏检测：使用 GetWindowRect 比较方式检测全屏应用

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 1-Skeleton & Animation*
*Context gathered: 2026-05-09*
