"""LLM API + 语音配置对话框"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QComboBox, QSpinBox,
    QPushButton, QGroupBox, QCheckBox, QScrollArea,
    QWidget,
)
from PySide6.QtCore import Qt

from data.settings import Settings
from pet.voice_tts import TTS_VOICES


class LLMSettingsDialog(QDialog):
    """LLM API + 语音配置对话框。"""

    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("LLM / 语音 设置")
        self.setFixedSize(480, 700)
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint
        )
        self._settings = settings
        self._build_ui()
        self._load_from_settings()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # 协议选择
        layout.addWidget(QLabel("API 协议:"))
        self._protocol = QComboBox()
        self._protocol.addItems(["不使用 LLM", "OpenAI 兼容", "Anthropic"])
        self._protocol.currentIndexChanged.connect(self._on_protocol_changed)
        layout.addWidget(self._protocol)

        # Base URL
        layout.addWidget(QLabel("API 地址 (Base URL):"))
        self._base_url = QLineEdit()
        self._base_url.setPlaceholderText("例如: https://api.deepseek.com/v1")
        layout.addWidget(self._base_url)

        # API Key
        layout.addWidget(QLabel("API Key:"))
        self._api_key = QLineEdit()
        self._api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key.setPlaceholderText("sk-...")
        layout.addWidget(self._api_key)

        # 模型名称
        layout.addWidget(QLabel("模型名称:"))
        self._model = QLineEdit()
        self._model.setPlaceholderText("例如: deepseek-chat")
        layout.addWidget(self._model)

        # 系统提示词
        layout.addWidget(QLabel("系统提示词:"))
        self._system_prompt = QTextEdit()
        self._system_prompt.setMaximumHeight(100)
        self._system_prompt.setPlaceholderText("留空使用默认水獭人格")
        layout.addWidget(self._system_prompt)

        # 最大历史消息数
        history_row = QHBoxLayout()
        history_row.addWidget(QLabel("最大历史消息数:"))
        self._max_history = QSpinBox()
        self._max_history.setRange(0, 200)
        self._max_history.setValue(50)
        history_row.addWidget(self._max_history)
        layout.addLayout(history_row)

        # 提示信息
        info = QLabel(
            "提示: 未配置 LLM 时，将使用规则匹配回复。"
            "LLM 调用失败时也会自动回退。"
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(info)

        # ── 语音设置区域 ──────────────────────────────────
        voice_group = QGroupBox("语音设置")
        voice_layout = QVBoxLayout(voice_group)
        voice_layout.setSpacing(6)

        self._voice_enabled = QCheckBox("启用语音功能")
        voice_layout.addWidget(self._voice_enabled)

        # STT 子区域
        stt_group = QGroupBox("语音识别 (STT) — 科大讯飞")
        stt_layout = QVBoxLayout(stt_group)

        stt_layout.addWidget(QLabel("App ID:"))
        self._xfyun_app_id = QLineEdit()
        self._xfyun_app_id.setPlaceholderText("讯飞开放平台 App ID")
        stt_layout.addWidget(self._xfyun_app_id)

        stt_layout.addWidget(QLabel("API Key:"))
        self._xfyun_api_key = QLineEdit()
        self._xfyun_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._xfyun_api_key.setPlaceholderText("讯飞 API Key")
        stt_layout.addWidget(self._xfyun_api_key)

        stt_layout.addWidget(QLabel("API Secret:"))
        self._xfyun_api_secret = QLineEdit()
        self._xfyun_api_secret.setEchoMode(QLineEdit.EchoMode.Password)
        self._xfyun_api_secret.setPlaceholderText("讯飞 API Secret")
        stt_layout.addWidget(self._xfyun_api_secret)

        stt_tip = QLabel("需要在 xfyun.cn 注册并创建「语音听写」应用")
        stt_tip.setWordWrap(True)
        stt_tip.setStyleSheet("color: #888; font-size: 11px;")
        stt_layout.addWidget(stt_tip)

        voice_layout.addWidget(stt_group)

        # TTS 子区域
        tts_group = QGroupBox("语音合成 (TTS) — Edge TTS")
        tts_layout = QVBoxLayout(tts_group)

        tts_layout.addWidget(QLabel("音色:"))
        self._tts_voice = QComboBox()
        for voice_id, label in TTS_VOICES.items():
            self._tts_voice.addItem(label, voice_id)
        tts_layout.addWidget(self._tts_voice)

        tts_layout.addWidget(QLabel("语速:"))
        self._tts_rate = QComboBox()
        self._tts_rate.addItems(["-30%", "-20%", "-10%", "+0%", "+10%", "+20%", "+30%"])
        self._tts_rate.setCurrentText("+0%")
        tts_layout.addWidget(self._tts_rate)

        vol_row = QHBoxLayout()
        vol_row.addWidget(QLabel("音量:"))
        self._tts_volume = QSpinBox()
        self._tts_volume.setRange(0, 100)
        self._tts_volume.setValue(80)
        vol_row.addWidget(self._tts_volume)
        tts_layout.addLayout(vol_row)

        self._voice_auto_play = QCheckBox("回复自动播放语音")
        tts_layout.addWidget(self._voice_auto_play)

        voice_layout.addWidget(tts_group)
        layout.addWidget(voice_group)

        # 按钮
        btn_layout = QHBoxLayout()
        min_btn = QPushButton("最小化")
        min_btn.setStyleSheet("""
            QPushButton {
                background-color: #E8E0D0;
                border: 2px solid #C0B090;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #D4C8B0; }
        """)
        min_btn.clicked.connect(self.reject)
        save_btn = QPushButton("保存")
        cancel_btn = QPushButton("取消")
        save_btn.clicked.connect(self._on_save)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(min_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _on_protocol_changed(self, index: int) -> None:
        """根据协议选择启用/禁用字段，更新 placeholder。"""
        is_enabled = index > 0
        self._base_url.setEnabled(is_enabled)
        self._api_key.setEnabled(is_enabled)
        self._model.setEnabled(is_enabled)

        if index == 1:  # OpenAI 兼容
            self._base_url.setPlaceholderText("https://api.deepseek.com/v1")
            self._model.setPlaceholderText("deepseek-chat")
        elif index == 2:  # Anthropic
            self._base_url.setPlaceholderText("https://api.anthropic.com")
            self._model.setPlaceholderText("claude-sonnet-4-20250514")

    def _load_from_settings(self) -> None:
        protocol_map = {"": 0, "openai": 1, "anthropic": 2}
        self._protocol.setCurrentIndex(
            protocol_map.get(self._settings.llm_protocol, 0)
        )
        self._base_url.setText(self._settings.llm_base_url)
        self._api_key.setText(self._settings.llm_api_key)
        self._model.setText(self._settings.llm_model)
        if self._settings.llm_system_prompt:
            self._system_prompt.setPlainText(self._settings.llm_system_prompt)
        self._max_history.setValue(self._settings.llm_max_history)

        # 语音设置
        self._voice_enabled.setChecked(self._settings.voice_enabled)
        self._xfyun_app_id.setText(self._settings.voice_xfyun_app_id)
        self._xfyun_api_key.setText(self._settings.voice_xfyun_api_key)
        self._xfyun_api_secret.setText(self._settings.voice_xfyun_api_secret)
        # TTS 音色
        for i in range(self._tts_voice.count()):
            if self._tts_voice.itemData(i) == self._settings.voice_tts_voice:
                self._tts_voice.setCurrentIndex(i)
                break
        self._tts_rate.setCurrentText(self._settings.voice_tts_rate)
        self._tts_volume.setValue(self._settings.voice_tts_volume)
        self._voice_auto_play.setChecked(self._settings.voice_auto_play)

    def _on_save(self) -> None:
        protocol_map = {0: "", 1: "openai", 2: "anthropic"}
        self._settings.llm_protocol = protocol_map[self._protocol.currentIndex()]
        self._settings.llm_base_url = self._base_url.text().strip()
        self._settings.llm_api_key = self._api_key.text().strip()
        self._settings.llm_model = self._model.text().strip()
        prompt = self._system_prompt.toPlainText().strip()
        self._settings.llm_system_prompt = prompt
        self._settings.llm_max_history = self._max_history.value()

        # 语音设置
        self._settings.voice_enabled = self._voice_enabled.isChecked()
        self._settings.voice_xfyun_app_id = self._xfyun_app_id.text().strip()
        self._settings.voice_xfyun_api_key = self._xfyun_api_key.text().strip()
        self._settings.voice_xfyun_api_secret = self._xfyun_api_secret.text().strip()
        self._settings.voice_tts_voice = self._tts_voice.currentData()
        self._settings.voice_tts_rate = self._tts_rate.currentText()
        self._settings.voice_tts_volume = self._tts_volume.value()
        self._settings.voice_auto_play = self._voice_auto_play.isChecked()

        self._settings.save()
        self.accept()
