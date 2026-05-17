"""聊天引擎：抽象基类 + 规则匹配实现 + LLM 工具调用支持"""
import json
import random
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable

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


def build_system_prompt(
    base_prompt: str = DEFAULT_SYSTEM_PROMPT,
    current_time: str = "",
    today_events: list[str] | None = None,
    pet_state: str = "idle",
) -> str:
    """动态构建系统提示词，注入时间、日程、状态上下文。"""
    parts = [base_prompt]

    # 情绪标记说明
    parts.append(
        "回复格式要求：在回复末尾用 [emotion:XXX] 标记你想要表达的情绪。"
        "可选情绪：happy, eat, play, groom, rest, alert, idle。"
        "例如：'好的主人~ [emotion:happy]'。如果不需要特殊情绪，不添加标记。"
    )

    if current_time:
        try:
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
        except (ValueError, IndexError):
            pass

    if today_events:
        parts.append(f"主人今天有这些日程：{'；'.join(today_events)}")

    parts.append(f"你当前的状态是 {pet_state}。")

    return "\n".join(parts)


class LLMEngine(ChatEngine):
    """LLM 聊天引擎抽象基类。

    子类必须实现 get_reply_async()。通过 LLMWorker (QThread) 异步调用。
    get_reply() 为同步包装，仅供 ChatEngine ABC 兼容，生产环境请用异步路径。
    """

    def __init__(self):
        self._context_provider: Callable[[], dict] | None = None

    def set_context_provider(self, provider: Callable[[], dict]) -> None:
        """设置上下文提供者回调，每次对话前调用获取动态上下文。"""
        self._context_provider = provider

    def _build_dynamic_system_prompt(self, base_prompt: str) -> str:
        """使用 context_provider 动态构建系统提示词。"""
        if not self._context_provider:
            return base_prompt
        ctx = self._context_provider()
        return build_system_prompt(
            base_prompt=base_prompt,
            current_time=ctx.get("current_time", ""),
            today_events=ctx.get("today_events"),
            pet_state=ctx.get("pet_state", "idle"),
        )

    @abstractmethod
    async def get_reply_async(self, messages: list[dict], tools: list[dict] | None = None) -> str | dict:
        """根据对话历史生成回复。

        Args:
            messages: [{"role": "user"|"assistant", "content": "..."}, ...]
                      不含 system prompt（由子类注入）。
            tools: 可选的 OpenAI 格式工具定义列表。
        Returns:
            纯文本回复，或 {"type": "tool_call", "name": ..., "arguments": ...} 字典。
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
                    result = pool.submit(
                        asyncio.run, self.get_reply_async(messages)
                    ).result()
                    return result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
            result = loop.run_until_complete(self.get_reply_async(messages))
            return result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
        except RuntimeError:
            result = asyncio.run(self.get_reply_async(messages))
            return result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)


class OpenAICompatibleEngine(LLMEngine):
    """OpenAI 兼容协议引擎（支持 DeepSeek、Moonshot、Ollama 等）。"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-3.5-turbo",
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ):
        super().__init__()
        import openai
        self._client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._system_prompt = system_prompt

    async def get_reply_async(self, messages: list[dict], tools: list[dict] | None = None) -> str | dict:
        dynamic_prompt = self._build_dynamic_system_prompt(self._system_prompt)
        full_messages = [{"role": "system", "content": dynamic_prompt}]
        full_messages.extend(messages)

        kwargs = {
            "model": self._model,
            "messages": full_messages,
            "max_tokens": 512,
        }
        if tools:
            kwargs["tools"] = tools

        response = await self._client.chat.completions.create(**kwargs)
        choice = response.choices[0]

        # 检查是否是工具调用
        if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
            tc = choice.message.tool_calls[0]
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}
            return {
                "type": "tool_call",
                "name": tc.function.name,
                "arguments": args,
                "tool_call_id": tc.id,
                "message": choice.message,  # 保留原始 message 用于回传
            }

        return choice.message.content


class AnthropicEngine(LLMEngine):
    """Anthropic 协议引擎（Claude 系列）。"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.anthropic.com",
        model: str = "claude-sonnet-4-20250514",
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ):
        super().__init__()
        import anthropic
        self._client = anthropic.AsyncAnthropic(api_key=api_key, base_url=base_url)
        self._model = model
        self._system_prompt = system_prompt

    async def get_reply_async(self, messages: list[dict], tools: list[dict] | None = None) -> str | dict:
        dynamic_prompt = self._build_dynamic_system_prompt(self._system_prompt)

        kwargs = {
            "model": self._model,
            "max_tokens": 512,
            "system": dynamic_prompt,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        response = await self._client.messages.create(**kwargs)

        # 检查是否是工具调用
        for block in response.content:
            if block.type == "tool_use":
                return {
                    "type": "tool_call",
                    "name": block.name,
                    "arguments": block.input,
                    "tool_call_id": block.id,
                    "content_blocks": response.content,  # 保留原始内容用于回传
                }

        # 纯文本回复
        text_parts = [b.text for b in response.content if hasattr(b, "text")]
        return "\n".join(text_parts)
