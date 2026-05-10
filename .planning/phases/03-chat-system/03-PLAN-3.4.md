---
wave: 2
depends_on:
  - P3.2
  - P3.3
files_modified:
  - main.py
autonomous: true
---

# P3.4 — 连接聊天到交互

## 目标

将聊天功能连接到用户交互：右键菜单"聊天"打开聊天面板，用户消息通过 ChatEngine 处理，回复同时显示在面板和气泡中。

**覆盖需求：** INT-03, INT-04, INT-05

---

## 任务

### 任务 1：在 main.py 中集成聊天面板

<task>
<action>
更新 `main.py`，集成 ChatPanel：

1. 添加导入：
```python
from pet.chat_panel import ChatPanel
```

2. 在创建聊天引擎之后创建聊天面板：
```python
    # 创建聊天面板
    chat_panel = ChatPanel()
```

3. 连接聊天面板的消息信号：
```python
    # 聊天面板消息处理
    def on_chat_message(text):
        reply = chat_engine.get_reply(text)
        chat_panel.add_message(reply, is_user=False)
        # 同时在气泡中显示回复
        pos = window.get_position()
        bubble.show_message(reply, pos[0] + 32, pos[1])

    chat_panel.message_sent.connect(on_chat_message)
```

4. 连接右键菜单"聊天"到面板显示：
```python
    # 右键菜单"聊天"打开面板
    window.chat_requested.connect(chat_panel.show)
```
</action>
<acceptance_criteria>
- `main.py` 包含 `from pet.chat_panel import ChatPanel`
- `main.py` 包含 `chat_panel = ChatPanel()`
- `main.py` 包含 `chat_panel.message_sent.connect(on_chat_message)`
- `main.py` 包含 `window.chat_requested.connect(chat_panel.show)`
- `main.py` 包含 `chat_panel.add_message(reply, is_user=False)` 在消息处理中
- `main.py` 包含 `bubble.show_message(reply, ...)` 在消息处理中
</acceptance_criteria>
</task>

---

## 验证

1. **右键聊天验证：** 运行 `python main.py`，右键宠物点击"聊天"，确认聊天面板打开
2. **发送消息验证：** 在面板输入"你好"点击发送，确认：
   - 用户消息右对齐显示
   - 宠物回复左对齐显示
   - 气泡也显示回复
3. **关闭面板验证：** 关闭面板，确认应用继续运行
4. **再次打开验证：** 再次右键打开面板，确认之前的对话仍在

---

## must_haves

- 右键菜单"聊天"连接到 `chat_panel.show()`
- 用户消息通过 `chat_engine.get_reply()` 处理
- 回复同时显示在面板（`add_message`）和气泡（`show_message`）
- 关闭面板不退出应用
