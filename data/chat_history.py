"""对话历史持久化存储"""
from datetime import datetime

from data.store import JsonStore


class ChatHistoryStore:
    """对话历史的 JSON 持久化，基于 JsonStore 原子写入。"""

    SCHEMA_VERSION = 1

    def __init__(self, max_messages: int = 50):
        self._store = JsonStore("chat_history.json", store_name="chat_history")
        self._max_messages = max_messages

    def _load(self) -> list[dict]:
        data = self._store.load(
            default={"_schema_version": self.SCHEMA_VERSION, "messages": []},
            current_version=self.SCHEMA_VERSION,
        )
        return data.get("messages", [])

    def _save(self, messages: list[dict]) -> None:
        self._store.save({
            "_schema_version": self.SCHEMA_VERSION,
            "messages": messages[-self._max_messages:],
        })

    def append(self, role: str, content: str) -> None:
        """追加一条消息。role 为 'user' 或 'assistant'。"""
        messages = self._load()
        messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        self._save(messages)

    def get_context(self, limit: int | None = None) -> list[dict]:
        """返回 LLM 上下文消息列表（不含 timestamp 字段）。"""
        messages = self._load()
        if limit:
            messages = messages[-limit:]
        return [{"role": m["role"], "content": m["content"]} for m in messages]

    def clear(self) -> None:
        """清空对话历史。"""
        self._store.save({
            "_schema_version": self.SCHEMA_VERSION,
            "messages": [],
        })

    def set_max_messages(self, max_messages: int) -> None:
        """更新最大消息数限制。"""
        self._max_messages = max_messages
