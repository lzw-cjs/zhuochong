---
wave: 1
depends_on:
  - P3.1
files_modified:
  - main.py
autonomous: true
---

# P3.2 — 聊天气泡增强

## 目标

点击宠物时，气泡显示由 ChatEngine 生成的随机回复（而非固定的 "你好呀！"），让每次点击都有不同的反馈。

**覆盖需求：** INT-03（部分）

---

## 任务

### 任务 1：连接 ChatEngine 到气泡显示

<task>
<action>
更新 `main.py`，将点击回调中的固定文本改为 ChatEngine 生成：

1. 添加导入：
```python
from pet.chat_engine import RuleBasedEngine
```

2. 在创建气泡之后创建聊天引擎：
```python
    # 创建聊天引擎
    chat_engine = RuleBasedEngine()
```

3. 修改 `on_pet_clicked` 函数：
```python
    def on_pet_clicked():
        behavior.on_user_interaction()
        reply = chat_engine.get_reply("你好")
        pos = window.get_position()
        bubble.show_message(reply, pos[0] + 32, pos[1])
```
</action>
<acceptance_criteria>
- `main.py` 包含 `from pet.chat_engine import RuleBasedEngine`
- `main.py` 包含 `chat_engine = RuleBasedEngine()`
- `main.py` 的 `on_pet_clicked` 调用 `chat_engine.get_reply("你好")`
- `main.py` 将 `reply` 传入 `bubble.show_message(reply, ...)`
</acceptance_criteria>
</task>

---

## 验证

1. **气泡回复验证：** 运行 `python main.py`，多次点击宠物，确认气泡显示不同的中文回复
2. **回复来源验证：** 确认回复来自 `chat_rules.json` 中的规则

---

## must_haves

- 点击宠物时气泡显示 ChatEngine 生成的回复
- ChatEngine 使用 RuleBasedEngine
- 回复文本为中文
