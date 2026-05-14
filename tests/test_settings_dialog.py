"""LLMSettingsDialog 逻辑测试"""
import pytest
from unittest.mock import MagicMock, patch
from data.settings import Settings
from data.store import JsonStore


@pytest.fixture
def settings(tmp_path):
    with patch("data.store.APPDATA_DIR", tmp_path):
        yield Settings()


class TestLLMSettingsDialog:
    """LLM 设置对话框测试"""

    def test_init(self, qtbot, settings):
        from pet.settings_dialog import LLMSettingsDialog

        dlg = LLMSettingsDialog(settings)
        assert dlg._settings is settings

    def test_protocol_map(self, qtbot, settings):
        from pet.settings_dialog import LLMSettingsDialog

        dlg = LLMSettingsDialog(settings)

        # 测试协议映射
        protocol_map = {"": 0, "openai": 1, "anthropic": 2}
        assert protocol_map.get("", 0) == 0
        assert protocol_map.get("openai", 0) == 1
        assert protocol_map.get("anthropic", 0) == 2

    def test_load_from_settings_empty(self, qtbot, settings):
        from pet.settings_dialog import LLMSettingsDialog

        dlg = LLMSettingsDialog(settings)

        # 默认设置应该是空的
        assert dlg._protocol.currentIndex() == 0
        assert dlg._base_url.text() == ""
        assert dlg._api_key.text() == ""
        assert dlg._model.text() == ""

    def test_load_from_settings_openai(self, qtbot, settings):
        from pet.settings_dialog import LLMSettingsDialog

        settings.llm_protocol = "openai"
        settings.llm_base_url = "https://api.deepseek.com/v1"
        settings.llm_api_key = "sk-test"
        settings.llm_model = "deepseek-chat"

        dlg = LLMSettingsDialog(settings)

        assert dlg._protocol.currentIndex() == 1
        assert dlg._base_url.text() == "https://api.deepseek.com/v1"
        assert dlg._api_key.text() == "sk-test"
        assert dlg._model.text() == "deepseek-chat"

    def test_load_from_settings_anthropic(self, qtbot, settings):
        from pet.settings_dialog import LLMSettingsDialog

        settings.llm_protocol = "anthropic"
        settings.llm_base_url = "https://api.anthropic.com"
        settings.llm_api_key = "sk-ant-test"
        settings.llm_model = "claude-sonnet-4-20250514"

        dlg = LLMSettingsDialog(settings)

        assert dlg._protocol.currentIndex() == 2
        assert dlg._base_url.text() == "https://api.anthropic.com"
        assert dlg._api_key.text() == "sk-ant-test"
        assert dlg._model.text() == "claude-sonnet-4-20250514"

    def test_load_voice_settings(self, qtbot, settings):
        from pet.settings_dialog import LLMSettingsDialog

        settings.voice_enabled = True
        settings.voice_xfyun_app_id = "test_app"
        settings.voice_xfyun_api_key = "test_key"
        settings.voice_xfyun_api_secret = "test_secret"
        settings.voice_tts_voice = "zh-CN-YunxiNeural"
        settings.voice_tts_rate = "+10%"
        settings.voice_tts_volume = 60
        settings.voice_auto_play = True

        dlg = LLMSettingsDialog(settings)

        assert dlg._voice_enabled.isChecked() is True
        assert dlg._xfyun_app_id.text() == "test_app"
        assert dlg._xfyun_api_key.text() == "test_key"
        assert dlg._xfyun_api_secret.text() == "test_secret"
        assert dlg._tts_rate.currentText() == "+10%"
        assert dlg._tts_volume.value() == 60
        assert dlg._voice_auto_play.isChecked() is True

    def test_save_settings(self, qtbot, settings):
        from pet.settings_dialog import LLMSettingsDialog

        dlg = LLMSettingsDialog(settings)

        # 模拟用户输入
        dlg._protocol.setCurrentIndex(1)
        dlg._base_url.setText("https://api.test.com/v1")
        dlg._api_key.setText("sk-new-key")
        dlg._model.setText("test-model")
        dlg._system_prompt.setPlainText("自定义提示词")
        dlg._max_history.setValue(100)

        # 保存
        dlg._on_save()

        assert settings.llm_protocol == "openai"
        assert settings.llm_base_url == "https://api.test.com/v1"
        assert settings.llm_api_key == "sk-new-key"
        assert settings.llm_model == "test-model"
        assert settings.llm_system_prompt == "自定义提示词"
        assert settings.llm_max_history == 100

    def test_save_voice_settings(self, qtbot, settings):
        from pet.settings_dialog import LLMSettingsDialog

        dlg = LLMSettingsDialog(settings)

        # 模拟用户输入
        dlg._voice_enabled.setChecked(True)
        dlg._xfyun_app_id.setText("new_app")
        dlg._xfyun_api_key.setText("new_key")
        dlg._xfyun_api_secret.setText("new_secret")
        dlg._tts_rate.setCurrentText("+20%")
        dlg._tts_volume.setValue(90)
        dlg._voice_auto_play.setChecked(True)

        # 保存
        dlg._on_save()

        assert settings.voice_enabled is True
        assert settings.voice_xfyun_app_id == "new_app"
        assert settings.voice_xfyun_api_key == "new_key"
        assert settings.voice_xfyun_api_secret == "new_secret"
        assert settings.voice_tts_rate == "+20%"
        assert settings.voice_tts_volume == 90
        assert settings.voice_auto_play is True

    def test_protocol_changed_enables_fields(self, qtbot, settings):
        from pet.settings_dialog import LLMSettingsDialog

        dlg = LLMSettingsDialog(settings)

        # 选择 OpenAI
        dlg._on_protocol_changed(1)

        assert dlg._base_url.isEnabled()
        assert dlg._api_key.isEnabled()
        assert dlg._model.isEnabled()
        assert dlg._base_url.placeholderText() == "https://api.deepseek.com/v1"

    def test_protocol_changed_disables_fields(self, qtbot, settings):
        from pet.settings_dialog import LLMSettingsDialog

        dlg = LLMSettingsDialog(settings)

        # 选择"不使用 LLM"
        dlg._on_protocol_changed(0)

        assert not dlg._base_url.isEnabled()
        assert not dlg._api_key.isEnabled()
        assert not dlg._model.isEnabled()

    def test_anthropic_placeholder(self, qtbot, settings):
        from pet.settings_dialog import LLMSettingsDialog

        dlg = LLMSettingsDialog(settings)

        dlg._on_protocol_changed(2)

        assert dlg._base_url.placeholderText() == "https://api.anthropic.com"
        assert dlg._model.placeholderText() == "claude-sonnet-4-20250514"
