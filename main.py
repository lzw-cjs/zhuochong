"""Smart Desktop Pet — 应用入口"""
import os
import re
import sys
from datetime import date, datetime

# Win11 RHI 渲染修复：强制使用 OpenGL 后端
os.environ["QSG_RHI_BACKEND"] = "opengl"

# PyInstaller frozen mode: ensure Qt can find its platform plugins
if getattr(sys, 'frozen', False):
    os.environ['QT_PLUGIN_PATH'] = os.path.join(sys._MEIPASS, 'PySide6', 'Qt', 'plugins')

from PySide6.QtWidgets import QApplication, QDialog
from PySide6.QtCore import Qt, QTimer

from data.settings import Settings
from data.chat_history import ChatHistoryStore
from pet.settings_dialog import LLMSettingsDialog
from pet.window import PetWindow
from pet.states import PetState, FRAME_INTERVALS
from pet.animator import SpriteAnimator, generate_all_placeholder_frames
from pet.behavior import BehaviorScheduler
from pet.bubble import ChatBubble
from pet.tray import PetTrayIcon
from pet.chat_engine import RuleBasedEngine, OpenAICompatibleEngine, AnthropicEngine, DEFAULT_SYSTEM_PROMPT
from pet.chat_panel import ChatPanel, LLMWorker
from pet.schedule_panel import SchedulePanel
from pet.overdue_detector import ReminderEngine
from pet.overdue_widget import OverdueWidget
from data.schedule_store import ScheduleStore
from pet.reminder_engine import ReminderEngine as PreReminderEngine
from pet.sound_manager import SoundManager
from pet.movement import MovementController
from pet.indicator import StateIndicator
from pet.transition import TransitionAnimator
from pet.holiday_engine import HolidayEngine
from pet.costume import CostumeRenderer
from pet.voice_stt import MicrophoneRecorder, XfyunASR, STTWorker
from pet.voice_tts import EdgeTTSPlayer, TTSWorker
from pet.llm_tools import (
    ToolRegistry, TOOL_SCHEMAS,
    create_event_impl, query_events_impl, delete_event_impl,
    create_reminder_impl, get_pet_state_impl, get_current_time_impl,
    analyze_habits_impl,
)
from pet.temp_reminder import TempReminderManager
from pet.proactive_chat import ProactiveChatManager
from pet.habit_analyzer import HabitAnalyzer
from utils.assets import get_asset_path


# 情绪标记解析
EMOTION_STATE_MAP = {
    "happy": PetState.HAPPY,
    "eat": PetState.EAT,
    "play": PetState.PLAY,
    "groom": PetState.GROOM,
    "rest": PetState.REST,
    "alert": PetState.ALERT,
    "idle": PetState.IDLE,
}


def parse_emotion(reply: str) -> tuple[str, "PetState | None"]:
    """解析回复中的情绪标记，返回 (清理后文本, 状态)。"""
    match = re.search(r'\[emotion:(\w+)\]', reply)
    if match:
        emotion = match.group(1).lower()
        clean_text = reply[:match.start()].strip()
        state = EMOTION_STATE_MAP.get(emotion)
        return clean_text, state
    return reply, None


def main():
    # DPI 感知设置：避免高 DPI 下宠物位置偏移
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)

    # 加载设置
    settings = Settings.load()

    # 创建精灵动画器
    animator = SpriteAnimator()
    animator.load_frames(generate_all_placeholder_frames())

    # 恢复上次的动画状态
    try:
        saved_state = PetState(settings.pet_state)
        animator.set_state(saved_state)
    except (ValueError, KeyError):
        pass  # 无效状态值，保持默认 IDLE

    # 创建宠物窗口（全屏透明）
    window = PetWindow(scale=settings.pet_scale)
    window.set_sprite_position(settings.pet_x, settings.pet_y)

    # 绑定动画器到窗口：定时刷新窗口显示当前帧
    _last_displayed = [None]

    def update_display():
        # 过渡期间由 TransitionAnimator 控制显示
        if transition.is_active:
            return
        pixmap = animator.current_pixmap()
        if pixmap:
            # 应用节日服装
            if costume_renderer.has_active_costume():
                pixmap = costume_renderer.apply_costume(pixmap)
            _last_displayed[0] = pixmap
            window.set_pixmap(pixmap)

    display_timer = QTimer()
    display_timer.timeout.connect(update_display)
    display_timer.start(50)  # 20 FPS 刷新率

    # 启动动画
    animator.start()

    # 创建行为调度器
    behavior = BehaviorScheduler(animator)
    behavior.start()

    # 创建移动控制器（WALK 时满屏走动）
    movement = MovementController(window, animator)

    # 创建状态指示器（emoji 头标）
    indicator = StateIndicator()
    sprite_w = int(window.BASE_CANVAS * 1.4 * settings.pet_scale)
    indicator.set_sprite_width(sprite_w)
    indicator.set_scale(settings.pet_scale)

    # 创建过渡动画器（300ms alpha 渐变）
    transition = TransitionAnimator()

    # 状态切换时：启动过渡动画 + 更新指示器
    def on_state_changed(state: PetState):
        # 中断当前过渡
        if transition.is_active:
            transition.interrupt()
        # 启动 alpha 渐变过渡：旧帧 → 新状态首帧
        from_pix = _last_displayed[0]
        to_pix = animator.current_pixmap()
        # 确保两帧都有效且不同，才启动过渡
        if (from_pix and to_pix
                and not from_pix.isNull() and not to_pix.isNull()
                and from_pix is not to_pix):
            transition.start_transition(from_pix, to_pix, duration_ms=300)
        elif to_pix and not to_pix.isNull():
            # 无有效旧帧时直接显示新帧，避免黑框
            window.set_pixmap(to_pix)
            _last_displayed[0] = to_pix
        # 更新指示器
        pos = window.get_position()
        indicator.show_for_state(state, pos[0], pos[1])

    animator.state_changed.connect(on_state_changed)

    # 过渡期间：过渡动画器控制显示
    def on_transition_frame(pixmap):
        window.set_pixmap(pixmap)

    transition.frame_ready.connect(on_transition_frame)

    # 过渡完成：恢复正常动画刷新
    def on_transition_done():
        pass  # update_display 会自动接管

    transition.transition_complete.connect(on_transition_done)

    # 对话气泡
    bubble = ChatBubble()

    # 创建聊天引擎
    chat_engine = RuleBasedEngine()

    # 创建对话历史存储
    chat_history = ChatHistoryStore(max_messages=settings.llm_max_history)

    # LLM 引擎工厂
    def create_llm_engine(s: Settings):
        """根据设置创建 LLM 引擎，未配置或 SDK 缺失时返回 None。"""
        if not s.llm_protocol or not s.llm_api_key:
            return None
        prompt = s.llm_system_prompt or DEFAULT_SYSTEM_PROMPT
        try:
            if s.llm_protocol == "openai":
                return OpenAICompatibleEngine(
                    api_key=s.llm_api_key,
                    base_url=s.llm_base_url or "https://api.openai.com/v1",
                    model=s.llm_model or "gpt-3.5-turbo",
                    system_prompt=prompt,
                )
            elif s.llm_protocol == "anthropic":
                return AnthropicEngine(
                    api_key=s.llm_api_key,
                    base_url=s.llm_base_url or "https://api.anthropic.com",
                    model=s.llm_model or "claude-sonnet-4-20250514",
                    system_prompt=prompt,
                )
        except ImportError:
            print(f"[LLM] SDK 未安装，回退到规则引擎")
            return None
        return None

    llm_engine = create_llm_engine(settings)

    # 为 LLM 引擎设置上下文提供者（动态系统提示词）
    def get_chat_context():
        now = datetime.now().isoformat()
        today_events = [
            f"{e.title}({e.datetime_str})"
            for e in schedule_store.get_all()
            if e.datetime_str.startswith(date.today().isoformat())
        ]
        return {
            "current_time": now,
            "today_events": today_events,
            "pet_state": animator.current_state.value,
        }

    if llm_engine:
        llm_engine.set_context_provider(get_chat_context)

    _worker = [None]  # 持有当前 worker 引用防止 GC

    # 创建聊天面板
    chat_panel = ChatPanel()

    # 创建语音系统
    recorder = MicrophoneRecorder()

    def create_xfyun_asr(s: Settings):
        """根据设置创建讯飞 ASR，未配置时返回 None。"""
        if s.voice_stt_provider != "xfyun" or not s.voice_xfyun_app_id:
            return None
        try:
            return XfyunASR(
                app_id=s.voice_xfyun_app_id,
                api_key=s.voice_xfyun_api_key,
                api_secret=s.voice_xfyun_api_secret,
            )
        except Exception as e:
            print(f"[语音] 讯飞 ASR 初始化失败: {e}")
            return None

    xfyun_asr = create_xfyun_asr(settings)
    tts_player = EdgeTTSPlayer(
        voice=settings.voice_tts_voice,
        rate=settings.voice_tts_rate,
    )
    tts_player.set_volume(settings.voice_tts_volume)

    _stt_worker = [None]  # 持有 STT worker 引用防止 GC
    _tts_worker = [None]  # 持有 TTS worker 引用防止 GC

    # TTS 播放辅助函数
    def speak_reply(text: str):
        """如果启用语音自动播放，合成并播放回复。"""
        if not settings.voice_enabled or not settings.voice_auto_play:
            return
        if settings.muted:
            return
        worker = TTSWorker(
            text, settings.voice_tts_voice, settings.voice_tts_rate
        )
        _tts_worker[0] = worker

        def on_mp3(data):
            tts_player.play(data)

        def on_tts_error(msg):
            print(f"[TTS] 合成失败: {msg}")

        worker.playback_ready.connect(on_mp3)
        worker.error_occurred.connect(on_tts_error)
        worker.start()

    # 麦克风按钮处理：录音 → STT → 发送消息
    def on_mic_clicked():
        if not settings.voice_enabled:
            chat_panel.add_message("(语音功能未启用，请在设置中开启)", is_user=False)
            return

        if recorder.is_recording:
            # 停止录音 → 识别
            pcm_data = recorder.stop_recording()
            chat_panel.set_mic_state("recognizing")

            if not xfyun_asr:
                chat_panel.set_mic_state("idle")
                chat_panel.add_message(
                    "(请先在设置中配置讯飞语音识别凭据)", is_user=False
                )
                return

            if not pcm_data:
                chat_panel.set_mic_state("idle")
                return

            worker = STTWorker(xfyun_asr, pcm_data)
            _stt_worker[0] = worker

            def on_stt_result(text):
                chat_panel.set_mic_state("idle")
                if text.strip():
                    # 自动填入并发送
                    chat_panel._input.setText(text)
                    chat_panel._on_send()

            def on_stt_error(msg):
                chat_panel.set_mic_state("idle")
                chat_panel.add_message(f"(语音识别失败: {msg})", is_user=False)

            worker.result_ready.connect(on_stt_result)
            worker.error_occurred.connect(on_stt_error)
            worker.start()
        else:
            # 开始录音
            try:
                recorder.start_recording()
                chat_panel.set_mic_state("recording")
            except RuntimeError as e:
                chat_panel.add_message(f"(录音启动失败: {e})", is_user=False)

    chat_panel.mic_clicked.connect(on_mic_clicked)

    # 点击宠物触发交互反馈 + 气泡显示
    def on_pet_clicked():
        movement.stop()  # 点击时停止移动
        behavior.on_user_interaction()
        proactive_chat.on_user_interaction()  # 记录交互时间
        reply = chat_engine.get_reply("你好")
        pos = window.get_position()
        bubble.show_message(reply, pos[0] + 128, pos[1])

    window.clicked.connect(on_pet_clicked)

    # 调试：数字键 1-9 手动切换状态，0 恢复自动
    _debug_mode = [False]

    def on_debug_state(state_name):
        if state_name == "__resume__":
            if _debug_mode[0]:
                behavior.start()
                _debug_mode[0] = False
                print("[调试] 已恢复自动模式")
            return
        try:
            target = PetState(state_name)
            # 暂停行为调度器和移动，防止自动切回
            if not _debug_mode[0]:
                behavior.stop()
                movement.stop()
                _debug_mode[0] = True
            # 绕过转换限制，直接切换
            animator._current_state = target
            animator._current_frame = 0
            interval = FRAME_INTERVALS.get(target, 500)
            animator._timer.setInterval(interval)
            animator.state_changed.emit(target)
            print(f"[调试] 切换到: {state_name}  (按 0 恢复自动)")
        except ValueError:
            pass

    window.debug_state_requested.connect(on_debug_state)

    # 聊天面板消息处理（LLM 优先，规则兜底）
    def on_chat_message(text):
        chat_history.append("user", text)
        proactive_chat.on_user_interaction()  # 记录交互时间

        if llm_engine:
            chat_panel.show_loading()
            messages = chat_history.get_context(limit=settings.llm_max_history)

            worker = LLMWorker(llm_engine, messages, tool_registry=tool_registry)
            _worker[0] = worker

            def on_reply(reply):
                chat_panel.hide_loading()
                # 解析情绪标记
                clean_text, emotion_state = parse_emotion(reply)
                chat_panel.add_message(clean_text, is_user=False)
                chat_history.append("assistant", clean_text)
                pos = window.get_position()
                bubble.show_message(clean_text, pos[0] + 128, pos[1])
                speak_reply(clean_text)
                # 应用情绪状态
                if emotion_state:
                    animator.set_state(emotion_state)
                    QTimer.singleShot(10000, lambda: animator.set_state(PetState.IDLE))

            def on_tool(name, result):
                """工具执行反馈。"""
                tool_names = {
                    "create_event": "正在创建日程...",
                    "query_events": "正在查询日程...",
                    "delete_event": "正在删除日程...",
                    "create_reminder": "正在设置提醒...",
                    "get_pet_state": "正在查看状态...",
                    "get_current_time": "正在获取时间...",
                    "analyze_habits": "正在分析习惯...",
                }
                msg = tool_names.get(name, f"正在执行 {name}...")
                chat_panel.add_message(msg, is_user=False)

            def on_error(error_msg):
                chat_panel.hide_loading()
                chat_panel.add_message(
                    f"(LLM 错误: {error_msg}，使用规则引擎)", is_user=False
                )
                reply = chat_engine.get_reply(text)
                chat_panel.add_message(reply, is_user=False)
                chat_history.append("assistant", reply)
                pos = window.get_position()
                bubble.show_message(reply, pos[0] + 128, pos[1])
                speak_reply(reply)

            worker.reply_ready.connect(on_reply)
            worker.tool_executed.connect(on_tool)
            worker.error_occurred.connect(on_error)
            worker.start()
        else:
            reply = chat_engine.get_reply(text)
            chat_panel.add_message(reply, is_user=False)
            pos = window.get_position()
            bubble.show_message(reply, pos[0] + 128, pos[1])
            speak_reply(reply)

    chat_panel.message_sent.connect(on_chat_message)

    # 创建日程面板
    schedule_panel = SchedulePanel()

    # 创建提醒引擎
    schedule_store = ScheduleStore()
    reminder = ReminderEngine(schedule_store)

    # 创建临时提醒管理器
    temp_reminder = TempReminderManager()

    # 创建习惯分析器
    habit_analyzer = HabitAnalyzer(schedule_store)

    # 创建工具注册中心
    tool_registry = ToolRegistry()
    tool_registry.register(
        "create_event",
        lambda **kw: create_event_impl(schedule_store, **kw),
        TOOL_SCHEMAS[0],
    )
    tool_registry.register(
        "query_events",
        lambda **kw: query_events_impl(schedule_store, **kw),
        TOOL_SCHEMAS[1],
    )
    tool_registry.register(
        "delete_event",
        lambda event_id: delete_event_impl(schedule_store, event_id),
        TOOL_SCHEMAS[2],
    )
    tool_registry.register(
        "create_reminder",
        lambda text, delay_minutes: create_reminder_impl(temp_reminder, text, delay_minutes),
        TOOL_SCHEMAS[3],
    )
    tool_registry.register(
        "get_pet_state",
        lambda: get_pet_state_impl(lambda: animator.current_state.value),
        TOOL_SCHEMAS[4],
    )
    tool_registry.register(
        "get_current_time",
        lambda: get_current_time_impl(),
        TOOL_SCHEMAS[5],
    )
    tool_registry.register(
        "analyze_habits",
        lambda: analyze_habits_impl(habit_analyzer),
        TOOL_SCHEMAS[6],
    )

    # 临时提醒触发：气泡 + ALERT 状态 + 音效
    def on_temp_reminder_fired(text):
        pos = window.get_position()
        bubble.show_message(f"提醒: {text}", pos[0] + 128, pos[1], duration_ms=5000)
        animator.set_state(PetState.ALERT)
        sound_manager.play_reminder(muted=settings.muted)
        QTimer.singleShot(5000, lambda: animator.set_state(PetState.IDLE))

    temp_reminder.reminder_fired.connect(on_temp_reminder_fired)

    # 创建主动对话管理器
    proactive_chat = ProactiveChatManager(schedule_store)

    def on_proactive_chat(text):
        pos = window.get_position()
        bubble.show_message(text, pos[0] + 128, pos[1], duration_ms=5000)
        chat_panel.add_message(text, is_user=False)

    proactive_chat.trigger_chat.connect(on_proactive_chat)

    # 创建前提醒引擎
    pre_reminder = PreReminderEngine(schedule_store)

    # 创建音效管理器
    sound_manager = SoundManager(get_asset_path("assets/sounds"))

    # 创建节日换装系统
    holiday_engine = HolidayEngine()
    costume_renderer = CostumeRenderer()

    # 节日激活时：设置服装 + 显示气泡
    def on_holiday_active(holiday_id, costume_id, emoji):
        if settings.costume_enabled:
            costume_renderer.set_active_costume(costume_id)
        pos = window.get_position()
        bubble.show_message(f"{emoji} 节日快乐！", pos[0] + 128, pos[1], duration_ms=5000)

    # 节日结束时：清除服装
    def on_holiday_ended():
        costume_renderer.clear_costume()

    holiday_engine.holiday_active.connect(on_holiday_active)
    holiday_engine.holiday_ended.connect(on_holiday_ended)

    # 换装开关处理
    def on_costume_toggle(enabled):
        settings.costume_enabled = enabled
        settings.save()
        window._costume_enabled = enabled
        if not enabled:
            costume_renderer.clear_costume()
        elif holiday_engine.active_holiday:
            # 如果当前有节日，重新激活服装
            h = holiday_engine.active_holiday
            costume_renderer.set_active_costume(h["costume"])

    window.costume_toggle.connect(on_costume_toggle)

    # 手动试穿服装
    def on_costume_try(costume_id):
        if costume_id:
            costume_renderer.set_active_costume(costume_id)
            pos = window.get_position()
            bubble.show_message("试穿成功！", pos[0] + 128, pos[1])
        else:
            costume_renderer.clear_costume()

    window.costume_try.connect(on_costume_try)

    # 初始化窗口的换装状态
    window._costume_enabled = settings.costume_enabled

    # 提醒触发处理：气泡 + 警报动画 + 音效
    def on_reminder_fired(ev):
        # 显示气泡
        pos = window.get_position()
        bubble.show_message(f"提醒: {ev.title}", pos[0] + 128, pos[1], duration_ms=5000)
        # 触发 ALERT 动画
        animator.set_state(PetState.ALERT)
        # 播放音效
        sound_manager.play_reminder(muted=settings.muted)
        # 5 秒后恢复 IDLE
        QTimer.singleShot(5000, lambda: animator.set_state(PetState.IDLE))

    pre_reminder.reminder_fired.connect(on_reminder_fired)

    # 提前完成 → 夸赞 + 开心状态
    praise_messages = [
        "太棒了！提前完成！你是最棒的！❤️",
        "好厉害！效率超高！给你比心！💕",
        "完美！提前搞定！树懒为你骄傲！🎉",
        "哇！这么快就完成了！爱你哟！💖",
    ]
    _praise_idx = [0]

    def on_completed_early(ev):
        behavior.on_user_interaction()  # 切换到 happy 状态
        msg = praise_messages[_praise_idx[0] % len(praise_messages)]
        _praise_idx[0] += 1
        pos = window.get_position()
        bubble.show_message(msg, pos[0] + 128, pos[1], duration_ms=5000)
        chat_panel.add_message(msg, is_user=False)

    reminder.completed_early.connect(on_completed_early)

    # 超时未完成 → 浮动通知 + 悲伤气泡
    _overdue_widgets = []

    def on_overdue(ev):
        behavior.on_user_interaction()  # 触发状态
        pos = window.get_position()
        bubble.show_message(f"😢 {ev.title} 还没完成...", pos[0] + 128, pos[1], duration_ms=5000)

        def on_extend(title):
            for w in _overdue_widgets:
                if w._event_title == title:
                    reminder.extend_deadline(ev.id, hours=1)
                    schedule_panel._refresh()
                    break

        def on_cancel(title):
            for w in _overdue_widgets:
                if w._event_title == title:
                    reminder.cancel_event(ev.id)
                    schedule_panel._refresh()
                    break

        widget = OverdueWidget(ev.title, on_extend, on_cancel)
        widget.move(pos[0], pos[1] + 80)
        widget.show()
        _overdue_widgets.append(widget)

    reminder.overdue.connect(on_overdue)

    # 日程面板"完成"按钮连接到提醒引擎
    schedule_panel.mark_completed.connect(lambda eid: (
        reminder.mark_completed(eid),
        schedule_panel._refresh(),
    ))

    # 右键菜单"聊天"打开面板
    window.chat_requested.connect(chat_panel.show)

    # 右键菜单"日程"打开面板
    window.schedule_requested.connect(schedule_panel.show)

    # 设置对话框
    def open_settings_dialog():
        nonlocal llm_engine, xfyun_asr
        dlg = LLMSettingsDialog(settings, window)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            settings_new = Settings.load()
            settings.__dict__.update(settings_new.__dict__)
            llm_engine = create_llm_engine(settings)
            # 为新引擎设置上下文提供者
            if llm_engine:
                llm_engine.set_context_provider(get_chat_context)
            chat_history.set_max_messages(settings.llm_max_history)
            # 更新语音组件
            xfyun_asr = create_xfyun_asr(settings)
            tts_player.set_voice(settings.voice_tts_voice)
            tts_player.set_rate(settings.voice_tts_rate)
            tts_player.set_volume(settings.voice_tts_volume)

    window.settings_requested.connect(open_settings_dialog)

    # 午夜自动刷新：每分钟检查是否跨天
    _current_date = [date.today()]

    def check_day_change():
        today = date.today()
        if today != _current_date[0]:
            _current_date[0] = today
            schedule_panel._cal_grid.go_to_today()
            reminder.daily_check()
            schedule_panel.refresh_today()
            print(f"[智能桌面宠物] 日期变更: {today}")

    day_timer = QTimer()
    day_timer.timeout.connect(check_day_change)
    day_timer.start(60000)

    # 智能置顶检测
    topmost_timer = QTimer()
    topmost_timer.timeout.connect(window.check_smart_topmost)
    topmost_timer.start(2000)

    # 位置变化时实时保存（节流：每 500ms 最多保存一次）
    _save_throttle = QTimer()
    _save_throttle.setSingleShot(True)
    _save_throttle.setInterval(500)

    def _do_save_position():
        pos = window.get_position()
        s = Settings.load()  # 读取当前设置
        s.pet_x = pos[0]
        s.pet_y = pos[1]
        s.save()

    _save_throttle.timeout.connect(_do_save_position)

    def _on_position_changed(x, y):
        # 拖拽时停止自主移动
        if movement.is_moving:
            movement.stop()
            animator.set_state(PetState.IDLE)
        # 更新指示器位置
        indicator.update_position(x, y)
        if not _save_throttle.isActive():
            _save_throttle.start()

    window.position_changed.connect(_on_position_changed)

    # 大小变化时保存设置
    def _on_scale_changed(scale):
        settings.pet_scale = scale
        settings.save()
        # 更新指示器的精灵宽度参考和缩放
        sprite_w = int(window.BASE_CANVAS * 1.4 * scale)
        indicator.set_sprite_width(sprite_w)
        indicator.set_scale(scale)
        pos = window.get_position()
        indicator.update_position(pos[0], pos[1])

    window.scale_changed.connect(_on_scale_changed)

    # 退出时保存最终状态
    def on_about_to_quit():
        movement.stop()  # 停止自主移动
        pre_reminder.stop()  # 停止前提醒轮询
        temp_reminder.cancel_all()  # 取消所有临时提醒
        pos = window.get_position()
        settings.pet_x = pos[0]
        settings.pet_y = pos[1]
        settings.pet_state = animator.current_state.value
        settings.pet_scale = window._scale
        settings.save()
        print(f"[智能桌面宠物] 状态已保存: ({pos[0]}, {pos[1]}) {animator.current_state.value}")

    app.aboutToQuit.connect(on_about_to_quit)

    # 创建系统托盘图标
    tray = PetTrayIcon()

    # 托盘图标切换可见性
    def toggle_pet_visibility():
        if window.isVisible():
            window.hide()
            tray.update_visibility_state(False)
            pre_reminder.suppress(True)
        else:
            window.show()
            tray.update_visibility_state(True)
            pre_reminder.suppress(False)

    tray.toggle_visibility.connect(toggle_pet_visibility)

    # 托盘提醒开关
    def on_reminder_suppress(suppressed):
        pre_reminder.suppress(suppressed)

    tray.reminder_suppress.connect(on_reminder_suppress)

    window.show()
    tray.show()

    print("[智能桌面宠物] 启动完成")
    print(f"  位置: ({settings.pet_x}, {settings.pet_y})")
    print(f"  状态: {settings.pet_state}")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
