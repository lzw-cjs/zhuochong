"""聊天面板：独立窗口，消息列表 + 输入框"""
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea,
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer, QThread


class MessageBubble(QLabel):
    """单条消息气泡。"""

    def __init__(self, text: str, is_user: bool, parent=None):
        super().__init__(text, parent)
        self.setWordWrap(True)
        self.setMaximumWidth(240)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        if is_user:
            self.setStyleSheet("""
                QLabel {
                    background-color: #D4A574;
                    color: #333333;
                    border: 2px solid #A0784C;
                    border-radius: 10px;
                    padding: 8px 12px;
                    font-size: 13px;
                }
            """)
        else:
            self.setStyleSheet("""
                QLabel {
                    background-color: #F5F0E8;
                    color: #333333;
                    border: 2px solid #C0B090;
                    border-radius: 10px;
                    padding: 8px 12px;
                    font-size: 13px;
                }
            """)


class ChatPanel(QWidget):
    """聊天面板窗口。"""

    message_sent = Signal(str)
    voice_input = Signal(str)  # STT 识别结果
    mic_clicked = Signal()     # 麦克风按钮点击

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("与宠物聊天")
        self.setFixedSize(QSize(360, 480))
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # 标题栏
        title_bar = QHBoxLayout()
        title = QLabel("与宠物聊天")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                background-color: #8B5A2B;
                color: #FFFFFF;
                font-size: 14px;
                font-weight: bold;
                padding: 6px;
                border-radius: 6px;
            }
        """)
        min_btn = QPushButton("—")
        min_btn.setFixedSize(28, 28)
        min_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B5A2B;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #A0784C; }
        """)
        min_btn.clicked.connect(self.hide)
        title_bar.addWidget(title, 1)
        title_bar.addWidget(min_btn)
        layout.addLayout(title_bar)

        # 消息滚动区域
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet("""
            QScrollArea {
                border: 2px solid #C0B090;
                border-radius: 6px;
                background-color: #FDF8F0;
            }
        """)

        self._messages_widget = QWidget()
        self._messages_layout = QVBoxLayout(self._messages_widget)
        self._messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._messages_layout.setSpacing(6)
        self._scroll.setWidget(self._messages_widget)
        layout.addWidget(self._scroll, 1)

        # 输入区域
        input_layout = QHBoxLayout()
        input_layout.setSpacing(6)

        self._input = QLineEdit()
        self._input.setPlaceholderText("输入消息...")
        self._input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #C0B090;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
                background-color: #FFFFFF;
            }
            QLineEdit:focus {
                border-color: #8B5A2B;
            }
        """)
        self._input.returnPressed.connect(self._on_send)

        self._send_btn = QPushButton("发送")
        self._send_btn.setFixedWidth(60)
        self._send_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B5A2B;
                color: white;
                border: 2px solid #6B4A1B;
                border-radius: 6px;
                padding: 6px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #A0784C;
            }
            QPushButton:pressed {
                background-color: #6B4A1B;
            }
        """)
        self._send_btn.clicked.connect(self._on_send)

        # 麦克风按钮
        self._mic_btn = QPushButton("\U0001f3a4")
        self._mic_btn.setFixedSize(36, 36)
        self._mic_btn.setToolTip("点击录音，再次点击停止并识别")
        self._mic_btn.setStyleSheet("""
            QPushButton {
                background-color: #E8E0D0;
                border: 2px solid #C0B090;
                border-radius: 6px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #D4C8B0;
            }
        """)
        self._mic_btn.clicked.connect(self._on_mic_clicked)

        input_layout.addWidget(self._input, 1)
        input_layout.addWidget(self._mic_btn)
        input_layout.addWidget(self._send_btn)
        layout.addLayout(input_layout)

        # 录音状态
        self._mic_state = "idle"  # idle / recording / recognizing

    def _on_mic_clicked(self) -> None:
        """麦克风按钮点击：发射信号给外部处理录音逻辑。"""
        self.mic_clicked.emit()

    def set_mic_state(self, state: str) -> None:
        """设置麦克风按钮状态: idle / recording / recognizing。"""
        self._mic_state = state
        if state == "idle":
            self._mic_btn.setEnabled(True)
            self._mic_btn.setText("\U0001f3a4")
            self._mic_btn.setStyleSheet("""
                QPushButton {
                    background-color: #E8E0D0;
                    border: 2px solid #C0B090;
                    border-radius: 6px;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background-color: #D4C8B0;
                }
            """)
            self._input.setEnabled(True)
            self._send_btn.setEnabled(True)
        elif state == "recording":
            self._mic_btn.setText("\U0001f3a4")
            self._mic_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF6B6B;
                    border: 2px solid #CC4444;
                    border-radius: 6px;
                    font-size: 16px;
                    color: white;
                }
            """)
            self._input.setEnabled(False)
            self._send_btn.setEnabled(False)
        elif state == "recognizing":
            self._mic_btn.setEnabled(False)
            self._mic_btn.setText("...")
            self._mic_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFB74D;
                    border: 2px solid #E09000;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                }
            """)
            self._input.setEnabled(False)
            self._send_btn.setEnabled(False)

    def _on_send(self) -> None:
        text = self._input.text().strip()
        if not text:
            return
        self._input.clear()
        self.add_message(text, is_user=True)
        self.message_sent.emit(text)

    def add_message(self, text: str, is_user: bool) -> None:
        bubble = MessageBubble(text, is_user)

        wrapper = QHBoxLayout()
        wrapper.setContentsMargins(4, 2, 4, 2)

        if is_user:
            wrapper.addStretch()
            wrapper.addWidget(bubble)
        else:
            wrapper.addWidget(bubble)
            wrapper.addStretch()

        container = QWidget()
        container.setLayout(wrapper)
        self._messages_layout.addWidget(container)

        # 滚动到底部
        self._scroll.verticalScrollBar().setValue(
            self._scroll.verticalScrollBar().maximum()
        )

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def show_loading(self) -> None:
        """显示加载指示器，禁用输入。"""
        self._loading = LoadingIndicator()
        self._messages_layout.addWidget(self._loading)
        self._scroll.verticalScrollBar().setValue(
            self._scroll.verticalScrollBar().maximum()
        )
        self._input.setEnabled(False)
        self._send_btn.setEnabled(False)

    def hide_loading(self) -> None:
        """移除加载指示器，恢复输入。"""
        if hasattr(self, '_loading') and self._loading:
            self._loading.hide()
            self._messages_layout.removeWidget(self._loading)
            self._loading.deleteLater()
            self._loading = None
        self._input.setEnabled(True)
        self._send_btn.setEnabled(True)


class LoadingIndicator(QWidget):
    """等待 LLM 回复时的加载动画。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._label = QLabel("思考中...", self)
        self._label.setStyleSheet("""
            QLabel {
                background-color: #F5F0E8;
                color: #999;
                border: 2px solid #C0B090;
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 13px;
                font-style: italic;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.addWidget(self._label)
        layout.addStretch()

        self._dots = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(500)

    def _animate(self):
        self._dots = (self._dots + 1) % 4
        self._label.setText("思考中" + "." * self._dots)


class LLMWorker(QThread):
    """LLM API 异步调用工作线程，支持工具调用循环。"""

    reply_ready = Signal(str)
    error_occurred = Signal(str)
    tool_executed = Signal(str, str)  # (tool_name, tool_result)

    # 最大工具调用轮数，防止无限循环
    MAX_TOOL_ROUNDS = 5

    def __init__(self, llm_engine, messages: list[dict], tool_registry=None, parent=None):
        super().__init__(parent)
        self._engine = llm_engine
        self._messages = messages
        self._tool_registry = tool_registry

    def run(self):
        import asyncio
        try:
            result = asyncio.run(self._run_with_tools())
            if isinstance(result, str):
                self.reply_ready.emit(result)
            elif isinstance(result, dict) and result.get("type") == "tool_call":
                # 超出最大轮数时，返回最后一条消息
                self.reply_ready.emit("(工具调用次数过多，请稍后再试)")
            else:
                self.reply_ready.emit(str(result))
        except Exception as e:
            self.error_occurred.emit(str(e))

    async def _run_with_tools(self) -> str:
        """执行 LLM 对话，支持多轮工具调用。"""
        messages = list(self._messages)
        tools = None

        if self._tool_registry:
            tools = self._tool_registry.get_tools()

        for round_num in range(self.MAX_TOOL_ROUNDS):
            reply = await self._engine.get_reply_async(messages, tools=tools)

            # 纯文本回复，直接返回
            if isinstance(reply, str):
                return reply

            # 工具调用
            if isinstance(reply, dict) and reply.get("type") == "tool_call":
                tool_name = reply["name"]
                tool_args = reply["arguments"]
                tool_call_id = reply.get("tool_call_id", "")

                # 执行工具
                if self._tool_registry:
                    tool_result = self._tool_registry.execute(tool_name, tool_args)
                else:
                    tool_result = json.dumps({"error": "工具未注册"}, ensure_ascii=False)

                # 发射工具执行信号（用于 UI 反馈）
                self.tool_executed.emit(tool_name, tool_result)

                # 构造工具调用消息和结果消息（兼容两种协议）
                if "message" in reply:
                    # OpenAI 格式
                    messages.append(reply["message"])
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": tool_result,
                    })
                elif "content_blocks" in reply:
                    # Anthropic 格式：回传 assistant content + tool_result
                    messages.append({
                        "role": "assistant",
                        "content": reply["content_blocks"],
                    })
                    messages.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": tool_call_id,
                            "content": tool_result,
                        }],
                    })
                else:
                    # 简化格式（兜底）
                    messages.append({
                        "role": "assistant",
                        "content": f"[调用工具 {tool_name}]",
                    })
                    messages.append({
                        "role": "user",
                        "content": f"工具 {tool_name} 返回结果：{tool_result}",
                    })
                # 继续循环，让 LLM 基于结果生成最终回复
                continue

            # 未知格式，返回字符串表示
            return str(reply)

        # 超出最大轮数
        return "(工具调用次数过多，请稍后再试)"
