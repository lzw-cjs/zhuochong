---
type: quick
mode: execute
tasks: 8
waves: 3
created: "2026-05-17"
---

# 桌面宠物小獭 AI 增强功能

## 目标

为小獭实现全部 AI 增强功能：工具调用、智能日程、情绪感知、主动对话、习惯分析。

## 现有架构

- `pet/chat_engine.py` — LLMEngine 基类 + OpenAICompatibleEngine / AnthropicEngine
- `pet/chat_panel.py` — LLMWorker(QThread) 异步调用
- `data/schedule_store.py` — ScheduleStore 事件 CRUD
- `data/event.py` — Event 数据类
- `pet/behavior.py` — BehaviorScheduler 状态调度
- `pet/bubble.py` — ChatBubble 气泡显示
- `pet/indicator.py` — StateIndicator 状态头标
- `pet/states.py` — PetState 枚举 + 状态转换表
- `main.py` — 信号/槽连接，所有组件初始化

---

## Wave 1: 工具调用基础

### Task 1: LLM 工具注册与调用框架

**文件**: `pet/llm_tools.py` (新建), `pet/chat_engine.py` (修改)

**做什么**:

1. 新建 `pet/llm_tools.py`，实现工具注册框架：

```python
# 工具定义格式（OpenAI function calling 兼容）
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_event",
            "description": "创建日程事件",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "事件标题"},
                    "datetime_str": {"type": "string", "description": "ISO 8601 格式时间"},
                    "description": {"type": "string", "description": "事件描述"},
                    "category": {"type": "string", "enum": ["工作","学习","生活","其他"]},
                    "priority": {"type": "string", "enum": ["low","medium","high"]},
                },
                "required": ["title", "datetime_str"]
            }
        }
    },
    # query_events, delete_event, create_reminder, get_pet_state, get_current_time
]
```

2. 实现 `ToolRegistry` 类：
   - `register(name, func, schema)` — 注册工具
   - `get_tools()` — 返回 OpenAI 格式工具列表
   - `get_anthropic_tools()` — 返回 Anthropic 格式工具列表
   - `execute(name, arguments) -> str` — 执行工具，返回结果字符串

3. 实现 6 个工具函数（本地执行）：
   - `create_event(title, datetime_str, ...)` → 调用 ScheduleStore.add()
   - `query_events(start_date?, end_date?, category?)` → 调用 ScheduleStore.get_all() + 过滤
   - `delete_event(event_id)` → 调用 ScheduleStore.delete()
   - `create_reminder(text, delay_minutes)` → 返回确认（实际 QTimer 在 Task 5 接入）
   - `get_pet_state()` → 返回当前 PetState + 最近交互时间
   - `get_current_time()` → 返回当前日期时间字符串

4. 修改 `pet/chat_engine.py`：
   - `OpenAICompatibleEngine.get_reply_async()` 接受可选 `tools` 参数
   - 发送请求时附带 tools 定义
   - 收到 `finish_reason == "tool_calls"` 时，返回 `{"type": "tool_call", "name": ..., "arguments": ...}` 而非纯文本
   - `AnthropicEngine.get_reply_async()` 同理，使用 Anthropic 的 tool_use 格式
   - 两个引擎都支持多轮工具调用（tool result 回传后继续生成）

**关键约束**:
- 工具执行必须在 QThread 中（通过 LLMWorker 扩展）
- 工具函数抛异常时返回错误字符串，不崩溃
- 返回值必须是 JSON 字符串

**验证**:
```python
# 单元测试
def test_tool_registry():
    registry = ToolRegistry()
    registry.register("get_current_time", lambda: '{"time": "2026-05-17"}', {...})
    assert registry.execute("get_current_time", {}) == '{"time": "2026-05-17"}'

def test_create_event_tool():
    store = ScheduleStore()
    result = create_event_impl(store, title="开会", datetime_str="2026-05-18T15:00:00")
    assert "成功" in result
```

---

### Task 2: LLMWorker 支持工具调用循环

**文件**: `pet/chat_panel.py` (修改), `main.py` (修改)

**做什么**:

1. 扩展 `LLMWorker` 类：
   - 构造函数接受 `tool_registry` 参数（可选）
   - `run()` 方法中实现工具调用循环：
     ```
     while True:
         reply = await engine.get_reply_async(messages, tools)
         if reply is tool_call:
             result = tool_registry.execute(name, arguments)
             messages.append(tool_call_msg)
             messages.append(tool_result_msg)
             continue  # 让 LLM 基于结果继续生成
         else:
             self.reply_ready.emit(reply)  # 纯文本回复
             break
     ```
   - 新增信号 `tool_executed(str, str)` — 工具名 + 结果（用于 UI 反馈）

2. 修改 `main.py`：
   - 初始化 `ToolRegistry`，注册所有工具（绑定 ScheduleStore、BehaviorScheduler 等）
   - `create_llm_engine()` 不变，工具注册在外部
   - `on_chat_message()` 中创建 LLMWorker 时传入 tool_registry
   - 连接 `tool_executed` 信号：在聊天面板显示 "正在查询日程..." 等提示

**验证**:
- 发送 "现在几点了" → LLM 调用 get_current_time → 返回当前时间
- 发送 "帮我建一个明天下午3点开会的日程" → LLM 调用 create_event → 确认创建成功

---

## Wave 2: 智能功能

### Task 3: 智能日程创建 + 查询总结

**文件**: `main.py` (修改，工具注册部分)

**做什么**:

1. 完善 `create_event` 工具的参数解析：
   - 支持自然语言时间（LLM 会转成 ISO 8601，工具直接用）
   - 创建成功后自动刷新 SchedulePanel
   - 创建成功后触发 HAPPY 状态 + 气泡 "日程已创建！"

2. 完善 `query_events` 工具：
   - 支持日期范围过滤（今日/本周/本月）
   - 支持分类过滤
   - 返回格式化文本（标题 + 时间 + 状态）

3. 在 `main.py` 中注册工具时绑定真实依赖：
   ```python
   registry.register("create_event", lambda **kw: create_event_impl(schedule_store, **kw), ...)
   registry.register("query_events", lambda **kw: query_events_impl(schedule_store, **kw), ...)
   registry.register("delete_event", lambda eid: delete_event_impl(schedule_store, eid), ...)
   ```

**验证**:
- "帮我建一个明天下午3点开会的日程" → 事件出现在日程面板
- "我这周有什么安排？" → LLM 列出本周事件
- "取消明天的会议" → 事件被删除

---

### Task 4: 自然语言临时提醒

**文件**: `pet/temp_reminder.py` (新建), `main.py` (修改)

**做什么**:

1. 新建 `pet/temp_reminder.py`：
   ```python
   class TempReminderManager(QObject):
       reminder_fired = Signal(str)  # 提醒文本

       def __init__(self):
           self._timers: dict[str, QTimer] = {}

       def add_reminder(self, text: str, delay_minutes: int) -> str:
           """创建临时提醒，返回确认消息。"""
           timer = QTimer()
           timer.setSingleShot(True)
           timer.timeout.connect(lambda: self.reminder_fired.emit(text))
           timer.start(int(delay_minutes * 60 * 1000))
           rid = uuid.uuid4().hex[:8]
           self._timers[rid] = timer
           return f"好的！{delay_minutes}分钟后提醒你：{text}"

       def cancel_all(self):
           """取消所有临时提醒。"""
           for t in self._timers.values():
               t.stop()
           self._timers.clear()
   ```

2. 在 `main.py` 中：
   - 初始化 TempReminderManager
   - 注册 `create_reminder` 工具绑定到 TempReminderManager.add_reminder()
   - 连接 `reminder_fired` 信号 → 气泡 + ALERT 状态 + 音效（复用 on_reminder_fired 逻辑）
   - 退出时 cancel_all()

**验证**:
- "半小时后提醒我喝水" → 30分钟后气泡显示 "喝水"
- "5分钟后提醒我站起来" → 5分钟后触发提醒

---

### Task 5: 情绪感知回复

**文件**: `pet/chat_engine.py` (修改), `main.py` (修改)

**做什么**:

1. 修改系统提示词，在末尾追加：
   ```
   回复格式要求：在回复末尾用 [emotion:XXX] 标记你想要表达的情绪。
   可选情绪：happy, eat, play, groom, rest, alert, idle
   例如："好的主人~ [emotion:happy]"
   如果不需要特殊情绪，不添加标记。
   ```

2. 在 `main.py` 的 `on_reply()` 中解析情绪标记：
   ```python
   import re

   EMOTION_STATE_MAP = {
       "happy": PetState.HAPPY,
       "eat": PetState.EAT,
       "play": PetState.PLAY,
       "groom": PetState.GROOM,
       "rest": PetState.REST,
       "alert": PetState.ALERT,
       "idle": PetState.IDLE,
   }

   def parse_emotion(reply: str) -> tuple[str, PetState | None]:
       """解析回复中的情绪标记，返回 (清理后文本, 状态)。"""
       match = re.search(r'\[emotion:(\w+)\]', reply)
       if match:
           emotion = match.group(1).lower()
           clean_text = reply[:match.start()].strip()
           state = EMOTION_STATE_MAP.get(emotion)
           return clean_text, state
       return reply, None
   ```

3. 在 `on_reply()` 中应用：
   ```python
   clean_text, emotion_state = parse_emotion(reply)
   chat_panel.add_message(clean_text, is_user=False)
   if emotion_state:
       animator.set_state(emotion_state)
       QTimer.singleShot(10000, lambda: animator.set_state(PetState.IDLE))
   ```

**验证**:
- 发送 "我今天好累" → LLM 回复包含 [emotion:rest] → 宠物切换到 REST 状态
- 发送 "我们来玩吧" → LLM 回复包含 [emotion:play] → 宠物切换到 PLAY 状态
- 情绪标记不出现在用户看到的文本中

---

### Task 6: 角色扮演增强（上下文感知系统提示词）

**文件**: `pet/chat_engine.py` (修改)

**做什么**:

1. 创建 `build_system_prompt()` 函数，动态生成系统提示词：
   ```python
   def build_system_prompt(
       base_prompt: str = DEFAULT_SYSTEM_PROMPT,
       current_time: str = "",
       today_events: list[str] | None = None,
       pet_state: str = "idle",
   ) -> str:
       parts = [base_prompt]

       if current_time:
           hour = int(current_time.split("T")[1].split(":")[0])
           if 6 <= hour < 12:
               time_context = "现在是上午，主人可能刚开始一天的工作。"
           elif 12 <= hour < 14:
               time_context = "现在是中午，主人可能在吃午饭或午休。"
           elif 14 <= hour < 18:
               time_context = "现在是下午，主人可能在工作或学习。"
           elif 18 <= hour < 22:
               time_context = "现在是晚上，主人可能在休息或娱乐。"
           else:
               time_context = "现在是深夜了，主人应该早点休息。"
           parts.append(time_context)

       if today_events:
           parts.append(f"主人今天有这些日程：{'; '.join(today_events)}")

       parts.append(f"你当前的状态是 {pet_state}。")

       return "\n".join(parts)
   ```

2. 在 `OpenAICompatibleEngine` 和 `AnthropicEngine` 中：
   - 构造函数接受可选 `context_provider` 回调
   - 每次调用 `get_reply_async()` 时，调用 context_provider 获取上下文，动态构建 system prompt

3. 在 `main.py` 中创建 context_provider：
   ```python
   def get_chat_context():
       now = datetime.now().isoformat()
       today_events = [
           f"{e.title}({e.datetime_str})"
           for e in schedule_store.get_all()
           if e.datetime_str.startswith(date.today().isoformat())
       ]
       return {
           "current_time": now,
           "today_events": today_events,
           "pet_state": animator.current_state.value,
       }
   ```

**验证**:
- 深夜聊天时，小獭会说 "主人该睡觉了~"
- 有日程时，小獭会主动提起 "你下午3点有个会议哦"

---

## Wave 3: 主动功能

### Task 7: 主动对话系统

**文件**: `pet/proactive_chat.py` (新建), `main.py` (修改)

**做什么**:

1. 新建 `pet/proactive_chat.py`：
   ```python
   class ProactiveChatManager(QObject):
       trigger_chat = Signal(str)  # 主动消息文本

       def __init__(self, schedule_store, animator):
           super().__init__()
           self._store = schedule_store
           self._animator = animator
           self._last_interaction = time.time()

           # 每 30 分钟检查一次是否该主动说话
           self._check_timer = QTimer()
           self._check_timer.timeout.connect(self._check_proactive)
           self._check_timer.start(30 * 60 * 1000)

           # 日程提醒（提前 10 分钟）
           self._event_timer = QTimer()
           self._event_timer.timeout.connect(self._check_upcoming_events)
           self._event_timer.start(60 * 1000)  # 每分钟检查

       def on_user_interaction(self):
           """记录用户交互时间。"""
           self._last_interaction = time.time()

       def _check_proactive(self):
           """空闲时主动聊天。"""
           idle_minutes = (time.time() - self._last_interaction) / 60
           if idle_minutes > 30:
               messages = [
                   "主人好久没理我了，你在忙吗？(´・ω・`)",
                   "主人~休息一下吧！",
                   "你在做什么呀？我想你了~",
                   "主人，要不要和我聊聊天？",
               ]
               self.trigger_chat.emit(random.choice(messages))

       def _check_upcoming_events(self):
           """即将开始的日程提醒。"""
           now = datetime.now()
           for event in self._store.get_all():
               if event.completed:
                   continue
               try:
                   event_time = datetime.fromisoformat(event.datetime_str)
                   diff = (event_time - now).total_seconds()
                   if 0 < diff <= 600:  # 10 分钟内
                       self.trigger_chat.emit(
                           f"主人，{event.title} 快要开始了哦！还有{int(diff//60)}分钟~"
                       )
               except ValueError:
                   pass
   ```

2. 在 `main.py` 中：
   - 初始化 ProactiveChatManager
   - 连接 `trigger_chat` 信号 → 气泡显示 + 聊天面板显示
   - 连接 window.clicked、chat_panel.message_sent → `on_user_interaction()`

**验证**:
- 30 分钟无操作 → 气泡显示关心消息
- 日程开始前 10 分钟 → 气泡提醒

---

### Task 8: 习惯分析与建议

**文件**: `pet/habit_analyzer.py` (新建), `main.py` (修改)

**做什么**:

1. 新建 `pet/habit_analyzer.py`：
   ```python
   class HabitAnalyzer:
       def __init__(self, schedule_store, chat_history):
           self._store = schedule_store
           self._history = chat_history

       def analyze(self) -> str:
           """分析日程模式，返回建议文本。"""
           events = self._store.get_all()
           if len(events) < 3:
               return "日程数据还不够多，多用几天我就能帮你分析啦~"

           # 统计分类分布
           categories = Counter(e.category for e in events)
           completed = sum(1 for e in events if e.completed)
           total = len(events)

           # 统计高峰时段
           hours = []
           for e in events:
               try:
                   h = datetime.fromisoformat(e.datetime_str).hour
                   hours.append(h)
               except ValueError:
                   pass

           peak_hour = Counter(hours).most_common(1)[0][0] if hours else None

           # 生成建议
           lines = [f"你共有 {total} 个日程，完成了 {completed} 个。"]

           if peak_hour:
               lines.append(f"你的日程高峰在 {peak_hour}:00 左右。")

           top_cat = categories.most_common(1)[0] if categories else None
           if top_cat:
               lines.append(f"最多的分类是「{top_cat[0]}」（{top_cat[1]}个）。")

           if completed / max(total, 1) < 0.5:
               lines.append("完成率有点低哦，试试把大任务拆成小块？")

           return "\n".join(lines)
   ```

2. 在 `main.py` 中注册 `analyze_habits` 工具：
   - LLM 可以调用此工具获取习惯分析
   - 用户说 "分析一下我的日程习惯" → LLM 调用 → 返回分析结果

**验证**:
- 有 5+ 个日程时，"分析一下我的习惯" → 返回统计和建议
- 日程少于 3 个时 → 返回 "数据不够" 提示

---

## 依赖关系

```
Task 1 (工具框架)
  └─→ Task 2 (LLMWorker 工具循环)
        ├─→ Task 3 (日程创建/查询)
        ├─→ Task 4 (临时提醒)
        ├─→ Task 5 (情绪感知)
        └─→ Task 6 (角色扮演)
              └─→ Task 7 (主动对话)
                    └─→ Task 8 (习惯分析)
```

## 信号/槽连接汇总

| 信号 | 发射者 | 接收者 | 用途 |
|------|--------|--------|------|
| `tool_executed(str, str)` | LLMWorker | ChatPanel | 显示工具执行状态 |
| `reminder_fired(str)` | TempReminderManager | main.py | 触发临时提醒 |
| `trigger_chat(str)` | ProactiveChatManager | main.py | 主动对话气泡 |

## 新增文件清单

| 文件 | 职责 |
|------|------|
| `pet/llm_tools.py` | 工具注册框架 + 6 个工具实现 |
| `pet/temp_reminder.py` | 临时提醒管理器 |
| `pet/proactive_chat.py` | 主动对话管理器 |
| `pet/habit_analyzer.py` | 习惯分析器 |

## 修改文件清单

| 文件 | 修改内容 |
|------|----------|
| `pet/chat_engine.py` | 工具调用支持 + 动态系统提示词 |
| `pet/chat_panel.py` | LLMWorker 工具调用循环 |
| `main.py` | 注册工具、初始化新组件、连接信号 |
