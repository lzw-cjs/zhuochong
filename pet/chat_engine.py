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


# ── LLM 引擎 ──────────────────────────────────────────────────────

DEFAULT_SYSTEM_PROMPT = (
    "你是一只可爱的桌面宠物水獭，名叫小獭。"
    "你性格活泼、调皮、有点呆萌，喜欢用颜文字和emoji。"
    "你说话简短有趣，像在和好朋友聊天。"
    "你会关心主人的状态，偶尔撒娇。"
    "回复不要太长，控制在2-3句话以内。"
)


class LLMEngine(ChatEngine):
    """LLM 聊天引擎抽象基类。

    子类必须实现 get_reply_async()。通过 LLMWorker (QThread) 异步调用。
    get_reply() 为同步包装，仅供 ChatEngine ABC 兼容，生产环境请用异步路径。
    """

    @abstractmethod
    async def get_reply_async(self, messages: list[dict]) -> str:
        """根据对话历史生成回复。

        Args:
            messages: [{"role": "user"|"assistant", "content": "..."}, ...]
                      不含 system prompt（由子类注入）。
        """
        ...

    def get_reply(self, user_message: str) -> str:
        """同步包装，兼容 ChatEngine ABC。"""
        import asyncio
        messages = [{"role": "user", "content": user_message}]
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(
                        asyncio.run, self.get_reply_async(messages)
                    ).result()
            return loop.run_until_complete(self.get_reply_async(messages))
        except RuntimeError:
            return asyncio.run(self.get_reply_async(messages))


class OpenAICompatibleEngine(LLMEngine):
    """OpenAI 兼容协议引擎（支持 DeepSeek、Moonshot、Ollama 等）。"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-3.5-turbo",
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ):
        import openai
        self._client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._system_prompt = system_prompt

    async def get_reply_async(self, messages: list[dict]) -> str:
        full_messages = [{"role": "system", "content": self._system_prompt}]
        full_messages.extend(messages)
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=full_messages,
            max_tokens=512,
        )
        return response.choices[0].message.content


class AnthropicEngine(LLMEngine):
    """Anthropic 协议引擎（Claude 系列）。"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.anthropic.com",
        model: str = "claude-sonnet-4-20250514",
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ):
        import anthropic
        self._client = anthropic.AsyncAnthropic(api_key=api_key, base_url=base_url)
        self._model = model
        self._system_prompt = system_prompt

    async def get_reply_async(self, messages: list[dict]) -> str:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=512,
            system=self._system_prompt,
            messages=messages,
        )
        return response.content[0].text
