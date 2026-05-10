"""聊天引擎：抽象基类 + 规则匹配实现"""
import json
import random
from abc import ABC, abstractmethod
from pathlib import Path

from utils.assets import get_asset_path


class ChatEngine(ABC):
    """聊天引擎抽象基类。"""

    @abstractmethod
    def get_reply(self, user_message: str) -> str:
        """根据用户消息生成回复。"""
        ...


class RuleBasedEngine(ChatEngine):
    """基于关键词匹配的聊天引擎。"""

    def __init__(self, rules_path: str | Path | None = None):
        if rules_path is None:
            rules_path = get_asset_path("data/chat_rules.json")
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
        if isinstance(self._fallback, list):
            return random.choice(self._fallback)
        return self._fallback
