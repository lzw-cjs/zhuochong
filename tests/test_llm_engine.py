"""LLM 聊天引擎、对话历史、设置扩展的单元测试。"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path

from data.chat_history import ChatHistoryStore
from data.settings import Settings
from data.store import JsonStore, APPDATA_DIR
from pet.chat_engine import (
    ChatEngine, RuleBasedEngine,
    LLMEngine, OpenAICompatibleEngine, AnthropicEngine,
    DEFAULT_SYSTEM_PROMPT,
)


# ── ChatHistoryStore ──────────────────────────────────────────────


class TestChatHistoryStore:
    """对话历史持久化测试。"""

    @pytest.fixture(autouse=True)
    def _clean_history(self, tmp_path):
        """每个测试使用隔离的临时目录。"""
        with patch("data.store.APPDATA_DIR", tmp_path):
            self.store = ChatHistoryStore(max_messages=10)
            yield

    def test_append_and_get_context(self):
        self.store.append("user", "你好")
        self.store.append("assistant", "你好呀！")

        ctx = self.store.get_context()
        assert len(ctx) == 2
        assert ctx[0] == {"role": "user", "content": "你好"}
        assert ctx[1] == {"role": "assistant", "content": "你好呀！"}

    def test_context_strips_timestamp(self):
        self.store.append("user", "测试")
        ctx = self.store.get_context()
        assert "timestamp" not in ctx[0]

    def test_max_messages_truncation(self):
        for i in range(15):
            self.store.append("user", f"消息{i}")

        ctx = self.store.get_context()
        assert len(ctx) == 10
        assert ctx[0]["content"] == "消息5"  # 最早的被截断

    def test_clear(self):
        self.store.append("user", "你好")
        self.store.append("assistant", "嗨")
        self.store.clear()

        ctx = self.store.get_context()
        assert len(ctx) == 0

    def test_get_context_with_limit(self):
        for i in range(5):
            self.store.append("user", f"msg{i}")

        ctx = self.store.get_context(limit=3)
        assert len(ctx) == 3
        assert ctx[0]["content"] == "msg2"

    def test_set_max_messages(self):
        self.store.set_max_messages(3)
        for i in range(5):
            self.store.append("user", f"msg{i}")

        ctx = self.store.get_context()
        assert len(ctx) == 3

    def test_empty_store_returns_empty_list(self):
        ctx = self.store.get_context()
        assert ctx == []


# ── Settings LLM 字段 ─────────────────────────────────────────────


class TestSettingsLLMFields:
    """Settings 扩展的 LLM 字段测试。"""

    @pytest.fixture(autouse=True)
    def _clean_settings(self, tmp_path):
        with patch("data.store.APPDATA_DIR", tmp_path):
            yield

    def test_default_llm_fields_are_empty(self):
        s = Settings()
        assert s.llm_protocol == ""
        assert s.llm_base_url == ""
        assert s.llm_api_key == ""
        assert s.llm_model == ""
        assert s.llm_system_prompt == ""
        assert s.llm_max_history == 50

    def test_save_load_roundtrip(self):
        s = Settings(
            llm_protocol="openai",
            llm_base_url="https://api.deepseek.com/v1",
            llm_api_key="sk-test-key",
            llm_model="deepseek-chat",
            llm_system_prompt="你是测试助手",
            llm_max_history=30,
        )
        s.save()

        loaded = Settings.load()
        assert loaded.llm_protocol == "openai"
        assert loaded.llm_base_url == "https://api.deepseek.com/v1"
        assert loaded.llm_api_key == "sk-test-key"
        assert loaded.llm_model == "deepseek-chat"
        assert loaded.llm_system_prompt == "你是测试助手"
        assert loaded.llm_max_history == 30

    def test_backward_compatible_missing_llm_section(self, tmp_path):
        """旧版 settings.json 没有 llm 字段时应使用默认值。"""
        store = JsonStore("settings.json")
        store.save({
            "_schema_version": 1,
            "pet": {"x": 100, "y": 100, "state": "idle"},
            "preferences": {"volume": 50, "muted": False, "auto_start": False},
        })

        loaded = Settings.load()
        assert loaded.llm_protocol == ""
        assert loaded.llm_api_key == ""

    def test_save_preserves_pet_fields(self):
        """保存 LLM 设置时不丢失宠物位置等字段。"""
        s = Settings(pet_x=300, pet_y=400, llm_protocol="openai")
        s.save()

        loaded = Settings.load()
        assert loaded.pet_x == 300
        assert loaded.pet_y == 400
        assert loaded.llm_protocol == "openai"


# ── LLM 引擎 ──────────────────────────────────────────────────────


class TestLLMEngine:
    """LLM 引擎基类和子类测试。"""

    def test_default_system_prompt_exists(self):
        assert "水獭" in DEFAULT_SYSTEM_PROMPT
        assert len(DEFAULT_SYSTEM_PROMPT) > 20

    def test_rule_based_engine_still_works(self):
        """确保原有规则引擎不受影响。"""
        engine = RuleBasedEngine()
        reply = engine.get_reply("你好")
        assert len(reply) > 0

    def test_rule_based_engine_fallback(self):
        engine = RuleBasedEngine()
        reply = engine.get_reply("xyzabc123不存在的关键词")
        assert len(reply) > 0  # 应返回兜底回复


class TestOpenAICompatibleEngine:
    """OpenAI 兼容引擎测试（mock SDK）。"""

    @patch("pet.chat_engine.openai", create=True)
    def test_init_stores_params(self, mock_openai):
        mock_client = MagicMock()
        mock_openai.AsyncOpenAI.return_value = mock_client

        engine = OpenAICompatibleEngine(
            api_key="sk-test",
            base_url="https://api.test.com/v1",
            model="test-model",
            system_prompt="test prompt",
        )
        assert engine._model == "test-model"
        assert engine._system_prompt == "test prompt"

    def test_import_error_handling(self):
        """SDK 未安装时应抛出 ImportError。"""
        with patch.dict("sys.modules", {"openai": None}):
            with pytest.raises((ImportError, AttributeError)):
                OpenAICompatibleEngine(api_key="sk-test")


class TestAnthropicEngine:
    """Anthropic 引擎测试（mock SDK）。"""

    @patch("pet.chat_engine.anthropic", create=True)
    def test_init_stores_params(self, mock_anthropic):
        mock_client = MagicMock()
        mock_anthropic.AsyncAnthropic.return_value = mock_client

        engine = AnthropicEngine(
            api_key="sk-ant-test",
            base_url="https://api.anthropic.com",
            model="claude-test",
            system_prompt="test prompt",
        )
        assert engine._model == "claude-test"
        assert engine._system_prompt == "test prompt"

    def test_import_error_handling(self):
        with patch.dict("sys.modules", {"anthropic": None}):
            with pytest.raises((ImportError, AttributeError)):
                AnthropicEngine(api_key="sk-ant-test")


# ── create_llm_engine 工厂函数 ────────────────────────────────────


class TestCreateLLMEngine:
    """main.py 中 create_llm_engine 工厂的逻辑测试。"""

    def _create_engine(self, s):
        """复制 main.py 中的工厂逻辑。"""
        if not s.llm_protocol or not s.llm_api_key:
            return None
        prompt = s.llm_system_prompt or DEFAULT_SYSTEM_PROMPT
        try:
            if s.llm_protocol == "openai":
                with patch("pet.chat_engine.openai", create=True):
                    return OpenAICompatibleEngine(
                        api_key=s.llm_api_key,
                        base_url=s.llm_base_url or "https://api.openai.com/v1",
                        model=s.llm_model or "gpt-3.5-turbo",
                        system_prompt=prompt,
                    )
            elif s.llm_protocol == "anthropic":
                with patch("pet.chat_engine.anthropic", create=True):
                    return AnthropicEngine(
                        api_key=s.llm_api_key,
                        base_url=s.llm_base_url or "https://api.anthropic.com",
                        model=s.llm_model or "claude-sonnet-4-20250514",
                        system_prompt=prompt,
                    )
        except ImportError:
            return None
        return None

    def test_returns_none_when_no_protocol(self):
        s = Settings(llm_api_key="sk-test")
        assert self._create_engine(s) is None

    def test_returns_none_when_no_api_key(self):
        s = Settings(llm_protocol="openai")
        assert self._create_engine(s) is None

    def test_returns_none_when_empty_config(self):
        s = Settings()
        assert self._create_engine(s) is None

    @patch("pet.chat_engine.openai", create=True)
    def test_returns_openai_engine(self, mock_openai):
        mock_openai.AsyncOpenAI.return_value = MagicMock()
        s = Settings(llm_protocol="openai", llm_api_key="sk-test")
        engine = self._create_engine(s)
        assert isinstance(engine, OpenAICompatibleEngine)

    @patch("pet.chat_engine.anthropic", create=True)
    def test_returns_anthropic_engine(self, mock_anthropic):
        mock_anthropic.AsyncAnthropic.return_value = MagicMock()
        s = Settings(llm_protocol="anthropic", llm_api_key="sk-ant-test")
        engine = self._create_engine(s)
        assert isinstance(engine, AnthropicEngine)

    @patch("pet.chat_engine.openai", create=True)
    def test_uses_default_prompt_when_empty(self, mock_openai):
        mock_openai.AsyncOpenAI.return_value = MagicMock()
        s = Settings(llm_protocol="openai", llm_api_key="sk-test")
        engine = self._create_engine(s)
        assert engine._system_prompt == DEFAULT_SYSTEM_PROMPT
