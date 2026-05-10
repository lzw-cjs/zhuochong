---
wave: 0
depends_on: []
files_modified:
  - pet/chat_engine.py
  - data/chat_rules.json
  - pet/__init__.py
autonomous: true
---

# P3.1 — 聊天引擎抽象

## 目标

实现 ChatEngine 抽象基类和 RuleBasedEngine 规则匹配引擎。规则存储在 JSON 文件中，支持关键词匹配和兜底回复。

**覆盖需求：** INT-04, INT-05

---

## 任务

### 任务 1：创建聊天规则 JSON

<task>
<action>
创建 `data/chat_rules.json`：

```json
{
  "rules": [
    {
      "keywords": ["你好", "hello", "hi", "嗨"],
      "reply": "你好呀！今天过得怎么样？"
    },
    {
      "keywords": ["名字", "你是谁", "叫什么"],
      "reply": "我是一只小树懒，你的桌面宠物！"
    },
    {
      "keywords": ["开心", "高兴", "快乐"],
      "reply": "看到你开心我也开心！"
    },
    {
      "keywords": ["难过", "伤心", "不开心"],
      "reply": "别难过，有我陪着你呢~"
    },
    {
      "keywords": ["饿", "吃饭", "午餐", "晚餐"],
      "reply": "我也想吃东西，但我只能吃数据...嘎嘣脆！"
    },
    {
      "keywords": ["累", "困", "睡觉"],
      "reply": "累了就休息一下吧，我帮你看着时间~"
    },
    {
      "keywords": ["日程", "安排", "计划"],
      "reply": "右键点击我可以查看日程哦！"
    },
    {
      "keywords": ["天气", "下雨", "晴天"],
      "reply": "我住在你的桌面上，看不到外面的天气呢~"
    },
    {
      "keywords": ["谢谢", "感谢", "多谢"],
      "reply": "不客气！能帮到你我很开心！"
    },
    {
      "keywords": ["再见", "拜拜", "bye"],
      "reply": "拜拜！我就在桌面上，随时找我玩！"
    }
  ],
  "fallback": "嗯...我不太明白你在说什么，但我很高兴和你聊天！"
}
```
</action>
<acceptance_criteria>
- `data/chat_rules.json` 文件存在
- 文件包含 `"rules"` 数组，至少 10 条规则
- 每条规则包含 `"keywords"` 数组和 `"reply"` 字符串
- 文件包含 `"fallback"` 字段
- 文件使用 UTF-8 编码
</acceptance_criteria>
</task>

---

### 任务 2：实现 ChatEngine ABC

<task>
<action>
创建 `pet/chat_engine.py`，先定义抽象基类：

```python
"""聊天引擎：抽象基类 + 规则匹配实现"""
import json
import random
from abc import ABC, abstractmethod
from pathlib import Path


class ChatEngine(ABC):
    """聊天引擎抽象基类。

    所有聊天引擎必须实现 get_reply 方法。
    """

    @abstractmethod
    def get_reply(self, user_message: str) -> str:
        """根据用户消息生成回复。

        Args:
            user_message: 用户输入的文本

        Returns:
            宠物的回复文本
        """
        ...
```
</action>
<acceptance_criteria>
- `pet/chat_engine.py` 包含 `class ChatEngine(ABC):`
- `pet/chat_engine.py` 包含 `@abstractmethod`
- `pet/chat_engine.py` 包含 `def get_reply(self, user_message: str) -> str:`
</acceptance_criteria>
</task>

---

### 任务 3：实现 RuleBasedEngine

<task>
<action>
在 `pet/chat_engine.py` 中添加 RuleBasedEngine：

```python
class RuleBasedEngine(ChatEngine):
    """基于关键词匹配的聊天引擎。

    从 JSON 文件加载规则，匹配用户消息中的关键词返回对应回复。
    未匹配到任何关键词时返回兜底回复。
    """

    def __init__(self, rules_path: str | Path | None = None):
        if rules_path is None:
            rules_path = Path(__file__).parent.parent / "data" / "chat_rules.json"
        self._rules: list[dict] = []
        self._fallback: str = "嗯...我不太明白你在说什么。"
        self._load_rules(rules_path)

    def _load_rules(self, path: str | Path) -> None:
        """从 JSON 文件加载聊天规则。"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._rules = data.get("rules", [])
            self._fallback = data.get("fallback", self._fallback)
        except (FileNotFoundError, json.JSONDecodeError):
            self._rules = []

    def get_reply(self, user_message: str) -> str:
        """匹配关键词返回回复，无匹配时返回兜底回复。"""
        text = user_message.lower()
        for rule in self._rules:
            keywords = rule.get("keywords", [])
            if any(kw.lower() in text for kw in keywords):
                return rule["reply"]
        return self._fallback
```
</action>
<acceptance_criteria>
- `pet/chat_engine.py` 包含 `class RuleBasedEngine(ChatEngine):`
- `pet/chat_engine.py` 包含 `def _load_rules(self, path) -> None:`
- `pet/chat_engine.py` 包含 `def get_reply(self, user_message: str) -> str:`
- `pet/chat_engine.py` 包含 `self._fallback` 兜底回复
- `pet/chat_engine.py` 包含 `any(kw.lower() in text for kw in keywords)` 关键词匹配
- `pet/chat_engine.py` 使用 `encoding="utf-8"` 读取 JSON
</acceptance_criteria>
</task>

---

### 任务 4：更新 pet/__init__.py

<task>
<action>
更新 `pet/__init__.py`，添加 ChatEngine 和 RuleBasedEngine 导出：

在导入区域添加：
```python
from pet.chat_engine import ChatEngine, RuleBasedEngine
```

在 `__all__` 列表中添加：
```python
    "ChatEngine",
    "RuleBasedEngine",
```
</action>
<acceptance_criteria>
- `pet/__init__.py` 包含 `from pet.chat_engine import ChatEngine, RuleBasedEngine`
- `pet/__init__.py` 的 `__all__` 包含 `ChatEngine` 和 `RuleBasedEngine`
</acceptance_criteria>
</task>

---

## 验证

1. **规则加载验证：** `python -c "from pet.chat_engine import RuleBasedEngine; e = RuleBasedEngine(); print(e.get_reply('你好'))"` 应输出中文回复
2. **关键词匹配验证：** 测试多个关键词确认匹配正确
3. **兜底回复验证：** `e.get_reply('xyzabc')` 应返回兜底回复

---

## must_haves

- ChatEngine 使用 ABC 抽象基类
- RuleBasedEngine 从 JSON 文件加载规则
- 关键词匹配不区分大小写（`kw.lower() in text`）
- 未匹配时返回 fallback 回复
- JSON 文件使用 `encoding="utf-8"` 读取
- 规则路径默认使用 `Path(__file__).parent.parent / "data" / "chat_rules.json"`
