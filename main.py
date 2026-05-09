"""Smart Desktop Pet — 应用入口"""
import os
import sys

# Win11 RHI 渲染修复：强制使用 OpenGL 后端
os.environ["QSG_RHI_BACKEND"] = "opengl"

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer

from data.settings import Settings
from pet.window import PetWindow
from pet.states import PetState
from pet.animator import SpriteAnimator, generate_all_placeholder_frames
from pet.behavior import BehaviorScheduler
from pet.bubble import ChatBubble
from pet.tray import PetTrayIcon
from pet.chat_engine import RuleBasedEngine
from pet.chat_panel import ChatPanel
from pet.schedule_panel import SchedulePanel
from pet.overdue_detector import ReminderEngine
from pet.overdue_widget import OverdueWidget
from data.schedule_store import ScheduleStore
from pathlib import Path
from pet.reminder_engine import ReminderEngine as PreReminderEngine
from pet.sound_manager import SoundManager


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

    # 创建宠物窗口
    window = PetWindow()
    window.move_to(settings.pet_x, settings.pet_y)

    # 绑定动画器到窗口：定时刷新窗口显示当前帧
    def update_display():
        pixmap = animator.current_pixmap()
        if pixmap:
            window.set_pixmap(pixmap)

    display_timer = QTimer()
    display_timer.timeout.connect(update_display)
    display_timer.start(50)  # 20 FPS 刷新率

    # 启动动画
    animator.start()

    # 创建行为调度器
    behavior = BehaviorScheduler(animator)
    behavior.start()

    # 创建对话气泡
    bubble = ChatBubble()

    # 创建聊天引擎
    chat_engine = RuleBasedEngine()

    # 创建聊天面板
    chat_panel = ChatPanel()

    # 点击宠物触发交互反馈 + 气泡显示
    def on_pet_clicked():
        behavior.on_user_interaction()
        reply = chat_engine.get_reply("你好")
        pos = window.get_position()
        bubble.show_message(reply, pos[0] + 32, pos[1])

    window.clicked.connect(on_pet_clicked)

    # 聊天面板消息处理
    def on_chat_message(text):
        reply = chat_engine.get_reply(text)
        chat_panel.add_message(reply, is_user=False)
        pos = window.get_position()
        bubble.show_message(reply, pos[0] + 32, pos[1])

    chat_panel.message_sent.connect(on_chat_message)

    # 创建日程面板
    schedule_panel = SchedulePanel()

    # 创建提醒引擎
    schedule_store = ScheduleStore()
    reminder = ReminderEngine(schedule_store)

    # 创建前提醒引擎
    pre_reminder = PreReminderEngine(schedule_store)

    # 创建音效管理器
    sound_manager = SoundManager(Path("assets/sounds"))

    # 提醒触发处理：气泡 + 警报动画 + 音效
    def on_reminder_fired(ev):
        # 显示气泡
        pos = window.get_position()
        bubble.show_message(f"提醒: {ev.title}", pos[0] + 32, pos[1], duration_ms=5000)
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
        bubble.show_message(msg, pos[0] + 32, pos[1], duration_ms=5000)
        chat_panel.add_message(msg, is_user=False)

    reminder.completed_early.connect(on_completed_early)

    # 超时未完成 → 浮动通知 + 悲伤气泡
    _overdue_widgets = []

    def on_overdue(ev):
        behavior.on_user_interaction()  # 触发状态
        pos = window.get_position()
        bubble.show_message(f"😢 {ev.title} 还没完成...", pos[0] + 32, pos[1], duration_ms=5000)

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

    # 菜单动作信号占位
    window.settings_requested.connect(lambda: print("[菜单] 设置"))

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
        if not _save_throttle.isActive():
            _save_throttle.start()

    window.position_changed.connect(_on_position_changed)

    # 退出时保存最终状态
    def on_about_to_quit():
        pre_reminder.stop()  # 停止前提醒轮询
        pos = window.get_position()
        s = Settings(
            pet_x=pos[0],
            pet_y=pos[1],
            pet_state=animator.current_state.value,
            volume=settings.volume,
            muted=settings.muted,
            auto_start=settings.auto_start,
        )
        s.save()
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

    window.show()
    tray.show()

    print("[智能桌面宠物] 启动完成")
    print(f"  位置: ({settings.pet_x}, {settings.pet_y})")
    print(f"  状态: {settings.pet_state}")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
