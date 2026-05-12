"""精灵动画引擎：Sprite 帧管理和动画控制（水獭外观 v5 — 萌系卡通风格）"""
import math
from PySide6.QtCore import QTimer, QObject, Signal, Qt, QPoint
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QBrush, QFont

from pet.states import PetState, FRAME_INTERVALS, can_transition

# ============================================================
# 画布
# ============================================================
CANVAS = 180

# ============================================================
# 颜色调色板 — 暖棕色系，更接近真实水獭
# ============================================================
_C_BODY     = QColor(101, 67, 33)    # 深棕身体
_C_BODY_L   = QColor(120, 82, 45)    # 浅棕（边缘/高光）
_C_BELLY    = QColor(225, 190, 130)  # 奶油色腹部
_C_BELLY_H  = QColor(240, 210, 155)  # 腹部高光
_C_HEAD     = QColor(110, 74, 38)    # 头部（略浅于身体）
_C_FACE     = QColor(210, 175, 120)  # 脸部浅色区域
_C_EAR_OUT  = QColor(90, 60, 28)     # 耳朵外侧
_C_EAR_IN   = QColor(190, 145, 90)   # 耳朵内侧
_C_EYE      = QColor(20, 15, 10)     # 瞳孔
_C_EYE_W    = QColor(255, 255, 255)  # 眼睛高光
_C_EYE_BG   = QColor(40, 30, 18)     # 眼眶底色
_C_NOSE     = QColor(50, 35, 25)     # 鼻子
_C_MOUTH    = QColor(180, 70, 70)    # 嘴巴/舌头
_C_TONGUE   = QColor(230, 100, 100)  # 舌头
_C_WHISKER  = QColor(160, 120, 70)   # 胡须
_C_TAIL     = QColor(85, 55, 25)     # 尾巴（最深）
_C_TAIL_U   = QColor(100, 68, 35)    # 尾巴上面
_C_PAWS     = QColor(80, 52, 24)     # 爪子（深色肉垫）
_C_TOE      = QColor(60, 40, 18)     # 脚趾

# 道具颜色
_C_FISH     = QColor(100, 180, 220)
_C_FISH_D   = QColor(60, 140, 180)
_C_FISH_B   = QColor(180, 220, 240)
_C_STONE    = QColor(150, 140, 130)
_C_STONE_H  = QColor(185, 175, 165)
_C_STONE_D  = QColor(115, 105, 95)
_C_SUN      = QColor(255, 210, 60)
_C_SUN_RAY  = QColor(255, 230, 100)
_C_HEART    = QColor(255, 70, 110)
_C_RED      = QColor(230, 40, 40)
_C_Z        = QColor(100, 150, 255)
_C_STAR     = QColor(255, 255, 100)

# ============================================================
# 身体基准参数
# ============================================================
# 头部
HX, HY = 50, 8       # 头部左上角
HW, HH = 80, 60      # 头部尺寸
HCX, HCY = 90, 38    # 头部中心

# 身体（在头部下方，部分重叠）
BX, BY = 46, 52
BW, BH = 88, 64


def _font(size: int, bold: bool = False) -> QFont:
    f = QFont("Segoe UI Emoji", size)
    f.setPixelSize(size)
    if bold:
        f.setBold(True)
    return f


# ============================================================
# 身体部件
# ============================================================

def _draw_head(p: QPainter, cx: int, cy: int, bounce: int = 0):
    """圆头 + 脸部浅色区域 + 耳朵。"""
    cy += bounce
    # 耳朵（在头后面）
    p.setBrush(QBrush(_C_EAR_OUT))
    p.setPen(QPen(_C_EAR_OUT, 1))
    p.drawEllipse(cx - 36, cy - 26, 22, 22)
    p.drawEllipse(cx + 14, cy - 26, 22, 22)
    # 耳朵内部
    p.setBrush(QBrush(_C_EAR_IN))
    p.setPen(QPen(Qt.PenStyle.NoPen))
    p.drawEllipse(cx - 32, cy - 22, 14, 14)
    p.drawEllipse(cx + 18, cy - 22, 14, 14)

    # 头（大椭圆）
    p.setBrush(QBrush(_C_HEAD))
    p.setPen(QPen(_C_HEAD, 1))
    p.drawEllipse(cx - 38, cy - 30, 76, 60)

    # 脸部浅色区域
    p.setBrush(QBrush(_C_FACE))
    p.setPen(QPen(Qt.PenStyle.NoPen))
    p.drawEllipse(cx - 26, cy - 14, 52, 38)


def _draw_eyes(p: QPainter, cx: int, cy: int, big: bool = False,
               closed: bool = False, happy: bool = False, bounce: int = 0):
    """大眼睛，萌系风格。"""
    cy += bounce
    if closed:
        # 睡眠：弧线闭眼
        p.setPen(QPen(_C_EYE, 3))
        p.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        p.drawChord(cx - 24, cy - 8, 18, 14, 0, 180 * 16)
        p.drawChord(cx + 6, cy - 8, 18, 14, 0, 180 * 16)
        return
    if happy:
        # 开心：弯弯笑眼
        p.setPen(QPen(_C_EYE, 3))
        p.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        p.drawChord(cx - 24, cy - 10, 18, 14, 0, 180 * 16)
        p.drawChord(cx + 6, cy - 10, 18, 14, 0, 180 * 16)
        return
    # 正常/大眼
    s = 18 if big else 15
    # 白眼底
    p.setBrush(QBrush(_C_EYE_W))
    p.setPen(QPen(Qt.PenStyle.NoPen))
    p.drawEllipse(cx - 24, cy - 12, s + 4, s + 4)
    p.drawEllipse(cx + 4, cy - 12, s + 4, s + 4)
    # 瞳孔
    p.setBrush(QBrush(_C_EYE))
    p.setPen(QPen(_C_EYE, 1))
    p.drawEllipse(cx - 22, cy - 10, s, s)
    p.drawEllipse(cx + 6, cy - 10, s, s)
    # 高光（大而明亮）
    p.setBrush(QBrush(_C_EYE_W))
    p.setPen(QPen(Qt.PenStyle.NoPen))
    hs = 6 if big else 5
    p.drawEllipse(cx - 20, cy - 10, hs, hs)
    p.drawEllipse(cx + 8, cy - 10, hs, hs)
    # 小高光
    p.drawEllipse(cx - 16, cy - 4, 3, 3)
    p.drawEllipse(cx + 12, cy - 4, 3, 3)


def _draw_nose(p: QPainter, cx: int, cy: int, bounce: int = 0):
    """小巧三角鼻。"""
    cy += bounce
    p.setBrush(QBrush(_C_NOSE))
    p.setPen(QPen(Qt.PenStyle.NoPen))
    p.drawEllipse(cx - 5, cy + 4, 10, 7)


def _draw_whiskers(p: QPainter, cx: int, cy: int, bounce: int = 0):
    """胡须。"""
    cy += bounce
    p.setPen(QPen(_C_WHISKER, 1))
    # 左边
    p.drawLine(cx - 30, cy + 8, cx - 48, cy + 2)
    p.drawLine(cx - 30, cy + 12, cx - 46, cy + 14)
    # 右边
    p.drawLine(cx + 30, cy + 8, cx + 48, cy + 2)
    p.drawLine(cx + 30, cy + 12, cx + 46, cy + 14)


def _draw_body(p: QPainter, cx: int, cy: int, bounce: int = 0):
    """圆润身体 + 奶油色腹部。"""
    cy += bounce
    # 身体
    p.setBrush(QBrush(_C_BODY))
    p.setPen(QPen(_C_BODY, 1))
    p.drawEllipse(cx - 44, cy, 88, 64)
    # 腹部
    p.setBrush(QBrush(_C_BELLY))
    p.setPen(QPen(Qt.PenStyle.NoPen))
    p.drawEllipse(cx - 30, cy + 18, 60, 40)
    # 腹部高光
    p.setBrush(QBrush(_C_BELLY_H))
    p.drawEllipse(cx - 18, cy + 24, 36, 20)


def _draw_mouth(p: QPainter, cx: int, cy: int, bounce: int = 0):
    """张嘴（吃东西时）。"""
    cy += bounce
    p.setBrush(QBrush(_C_MOUTH))
    p.setPen(QPen(Qt.PenStyle.NoPen))
    p.drawEllipse(cx - 8, cy + 14, 16, 10)
    # 舌头
    p.setBrush(QBrush(_C_TONGUE))
    p.drawEllipse(cx - 4, cy + 18, 8, 6)


def _draw_tongue(p: QPainter, cx: int, cy: int, length: int, bounce: int = 0):
    """伸出的舌头。"""
    cy += bounce
    p.setBrush(QBrush(_C_TONGUE))
    p.setPen(QPen(Qt.PenStyle.NoPen))
    p.drawEllipse(cx - 4, cy + 14, 8, length)


def _draw_paws_down(p: QPainter, cx: int, cy: int, bounce: int = 0):
    """坐姿小短腿。"""
    cy += bounce
    p.setBrush(QBrush(_C_PAWS))
    p.setPen(QPen(Qt.PenStyle.NoPen))
    # 左脚
    p.drawEllipse(cx - 32, cy + 58, 22, 14)
    # 右脚
    p.drawEllipse(cx + 10, cy + 58, 22, 14)
    # 脚趾
    p.setBrush(QBrush(_C_TOE))
    for toe_x in [cx - 30, cx - 24, cx + 12, cx + 18]:
        p.drawEllipse(toe_x, cy + 62, 6, 6)


def _draw_tail(p: QPainter, cx: int, cy: int, up: bool = False, bounce: int = 0):
    """扁平大尾巴。"""
    cy += bounce
    if up:
        # 尾巴翘起
        points = [
            QPoint(cx + 38, cy + 48),
            QPoint(cx + 64, cy + 20),
            QPoint(cx + 72, cy + 14),
            QPoint(cx + 68, cy + 24),
            QPoint(cx + 44, cy + 56),
        ]
    else:
        # 尾巴平放
        points = [
            QPoint(cx + 38, cy + 52),
            QPoint(cx + 62, cy + 60),
            QPoint(cx + 72, cy + 66),
            QPoint(cx + 66, cy + 72),
            QPoint(cx + 42, cy + 62),
        ]
    p.setBrush(QBrush(_C_TAIL))
    p.setPen(QPen(_C_TAIL, 1))
    p.drawPolygon(points)
    # 尾巴纹理
    p.setPen(QPen(_C_TAIL_U, 1))
    p.drawLine(cx + 48, cy + 54, cx + 60, cy + 58)


def _draw_fish(p: QPainter, x: int, y: int, sz: int):
    """鱼。"""
    # 身体
    p.setBrush(QBrush(_C_FISH))
    p.setPen(QPen(_C_FISH_D, 1))
    p.drawEllipse(x, y, sz, sz // 2 + 4)
    # 腹部
    p.setBrush(QBrush(_C_FISH_B))
    p.setPen(QPen(Qt.PenStyle.NoPen))
    p.drawEllipse(x + 3, y + sz // 3, sz - 6, sz // 4)
    # 尾巴
    p.setBrush(QBrush(_C_FISH_D))
    p.setPen(QPen(Qt.PenStyle.NoPen))
    tx, ty = x + sz, y + sz // 4
    p.drawPolygon([
        QPoint(tx, ty), QPoint(tx + 12, ty - 8), QPoint(tx + 12, ty + 8)
    ])
    # 眼睛
    p.setBrush(QBrush(_C_EYE))
    p.drawEllipse(x + sz - 10, y + 4, 6, 6)
    # 鱼鳍
    p.setPen(QPen(_C_FISH_D, 1))
    p.drawLine(x + sz // 2, y, x + sz // 2 - 4, y - 8)
    p.drawLine(x + sz // 2, y, x + sz // 2 + 4, y - 8)


def _draw_stone(p: QPainter, x: int, y: int, w: int = 32, h: int = 24):
    """石头。"""
    p.setBrush(QBrush(_C_STONE))
    p.setPen(QPen(_C_STONE_D, 2))
    p.drawEllipse(x, y, w, h)
    p.setBrush(QBrush(_C_STONE_H))
    p.setPen(QPen(Qt.PenStyle.NoPen))
    p.drawEllipse(x + w // 4, y + h // 4, w // 3, h // 3)


def _draw_sun(p: QPainter, x: int, y: int, frame: int, radius: int = 14):
    """太阳 + 旋转光线。"""
    bright = [200, 255, 200, 255][frame % 4]
    p.setPen(QPen(QColor(255, 230, 100, bright), 2))
    angles = range(0, 360, 45)
    rot = frame * 15
    ray_len = radius + 8
    for a in angles:
        rad = math.radians(a + rot)
        dx = int(ray_len * math.cos(rad))
        dy = int(ray_len * math.sin(rad))
        p.drawLine(x, y, x + dx, y + dy)
    p.setBrush(QBrush(_C_SUN))
    p.setPen(QPen(_C_SUN, 1))
    p.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)


# ============================================================
# 各状态帧生成
# ============================================================

def generate_placeholder_frame(state: PetState, frame_index: int, total_frames: int) -> QPixmap:
    """为指定状态生成 180x180 水獭占位图。"""
    pixmap = QPixmap(CANVAS, CANVAS)
    pixmap.fill(Qt.GlobalColor.transparent)
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    cx, cy = HCX, HCY  # 头部中心

    # --- IDLE: 坐姿呼吸 ---
    if state == PetState.IDLE:
        b = [0, 3, 6, 3][frame_index % 4]
        _draw_tail(p, cx, cy, up=False, bounce=b)
        _draw_body(p, cx, cy, bounce=b)
        _draw_paws_down(p, cx, cy, bounce=b)
        _draw_head(p, cx, cy, bounce=b)
        _draw_eyes(p, cx, cy, bounce=b)
        _draw_nose(p, cx, cy, bounce=b)
        _draw_whiskers(p, cx, cy, bounce=b)

    # --- WALK: 行走摆动 ---
    elif state == PetState.WALK:
        swing = [0, 10, 0, -10, 0, 10][frame_index % 6]
        _draw_tail(p, cx + swing, cy, up=True)
        _draw_body(p, cx + swing, cy)
        # 交替抬脚
        p.setBrush(QBrush(_C_PAWS))
        p.setPen(QPen(Qt.PenStyle.NoPen))
        if frame_index % 2 == 0:
            p.drawEllipse(cx + swing - 32, cy + 58, 22, 14)
            p.drawEllipse(cx + swing + 14, cy + 52, 22, 14)
        else:
            p.drawEllipse(cx + swing - 28, cy + 52, 22, 14)
            p.drawEllipse(cx + swing + 10, cy + 58, 22, 14)
        _draw_head(p, cx + swing, cy)
        _draw_eyes(p, cx + swing, cy)
        _draw_nose(p, cx + swing, cy)
        _draw_whiskers(p, cx + swing, cy)

    # --- SLEEP: 蜷缩睡觉 + Z ---
    elif state == PetState.SLEEP:
        _draw_tail(p, cx, cy + 6)
        _draw_body(p, cx, cy + 6)
        _draw_paws_down(p, cx, cy + 6)
        _draw_head(p, cx, cy + 6)
        _draw_eyes(p, cx, cy + 6, closed=True)
        _draw_nose(p, cx, cy + 6)
        # Z 浮动
        z_pos = [(cx + 48, cy - 20), (cx + 58, cy - 36), (cx + 66, cy - 50)]
        for i, (zx, zy) in enumerate(z_pos):
            alpha = 255 - i * 50
            p.setPen(QPen(QColor(_C_Z.red(), _C_Z.green(), _C_Z.blue(), max(100, alpha)), 3))
            p.setFont(_font(22 + i * 6))
            off = [(0, 0), (3, -2), (-2, 3)][frame_index % 3]
            p.drawText(zx + off[0], zy + off[1], "Z")

    # --- HAPPY: 开心弹跳 + 爱心 ---
    elif state == PetState.HAPPY:
        b = [0, 12, 20, 12][frame_index % 4]
        _draw_tail(p, cx, cy - b, up=True)
        _draw_body(p, cx, cy - b)
        _draw_paws_down(p, cx, cy - b)
        _draw_head(p, cx, cy - b)
        _draw_eyes(p, cx, cy - b, happy=True)
        _draw_nose(p, cx, cy - b)
        _draw_whiskers(p, cx, cy - b)
        # 张嘴笑
        p.setBrush(QBrush(_C_MOUTH))
        p.setPen(QPen(Qt.PenStyle.NoPen))
        p.drawEllipse(cx - 8, cy + 14 - b, 16, 10)
        # 爱心
        p.setPen(QPen(_C_HEART, 2))
        p.setFont(_font(28))
        hy = [4, 0, -4, 0][frame_index % 4]
        p.drawText(cx - 8, cy - 42 + hy - b, "♥")

    # --- ALERT: 警报抖动 + 感叹号 ---
    elif state == PetState.ALERT:
        shake = [0, 14, 0, -14][frame_index % 4]
        # 红色光晕
        if frame_index % 2 == 0:
            p.setBrush(QBrush(QColor(255, 0, 0, 35)))
            p.setPen(QPen(Qt.PenStyle.NoPen))
            p.drawEllipse(cx - 54, cy - 44, 108, 128)
        _draw_tail(p, cx + shake, cy)
        _draw_body(p, cx + shake, cy)
        _draw_paws_down(p, cx + shake, cy)
        _draw_head(p, cx + shake, cy)
        _draw_eyes(p, cx + shake, cy, big=True)
        _draw_nose(p, cx + shake, cy)
        _draw_whiskers(p, cx + shake, cy)
        # 感叹号
        p.setPen(QPen(_C_RED, 5))
        p.setFont(_font(40, bold=True))
        p.drawText(cx - 8 + shake, cy - 46, "!")

    # --- EAT: 吃鱼 ---
    elif state == PetState.EAT:
        _draw_tail(p, cx, cy)
        _draw_body(p, cx, cy)
        _draw_paws_down(p, cx, cy)
        _draw_head(p, cx, cy)
        _draw_eyes(p, cx, cy)
        _draw_nose(p, cx, cy)
        _draw_whiskers(p, cx, cy)
        # 嘴巴张合
        if frame_index % 2 == 0:
            _draw_mouth(p, cx, cy)
        else:
            p.setPen(QPen(_C_MOUTH, 2))
            p.drawLine(cx - 6, cy + 16, cx + 6, cy + 16)
        # 鱼 — 右侧，逐渐缩小
        fish_sz = [36, 32, 28, 24, 20, 16][frame_index % 6]
        fx = cx + 48
        fy = cy + 6
        _draw_fish(p, fx, fy, fish_sz)

    # --- PLAY: 玩石头 ---
    elif state == PetState.PLAY:
        _draw_tail(p, cx, cy - 4)
        _draw_body(p, cx, cy - 4)
        _draw_head(p, cx, cy - 4)
        _draw_eyes(p, cx, cy - 4)
        _draw_nose(p, cx, cy - 4)
        _draw_whiskers(p, cx, cy - 4)
        # 爪子朝上挥动
        p.setBrush(QBrush(_C_PAWS))
        p.setPen(QPen(Qt.PenStyle.NoPen))
        paw = [0, 14, 0, -14][frame_index % 4]
        p.drawEllipse(cx - 38 + paw, cy - 14, 16, 12)
        p.drawEllipse(cx + 22 - paw, cy - 14, 16, 12)
        # 石头在上方滚动
        sx = cx - 16 + [0, 18, 36, 18][frame_index % 4]
        sy = cy - 40
        _draw_stone(p, sx, sy, 30, 22)

    # --- GROOM: 梳理毛发 ---
    elif state == PetState.GROOM:
        _draw_tail(p, cx, cy)
        _draw_body(p, cx, cy)
        _draw_head(p, cx, cy)
        _draw_eyes(p, cx, cy)
        _draw_nose(p, cx, cy)
        _draw_whiskers(p, cx, cy)
        # 前爪抬到嘴边
        p.setBrush(QBrush(_C_PAWS))
        p.setPen(QPen(Qt.PenStyle.NoPen))
        p.drawEllipse(cx - 30, cy + 10, 14, 12)
        p.drawEllipse(cx + 16, cy + 10, 14, 12)
        # 舌头伸出
        tongue_len = [0, 16, 0, 16][frame_index % 4]
        if tongue_len:
            _draw_tongue(p, cx, cy, tongue_len)
        # 闪光
        p.setPen(QPen(_C_STAR, 2))
        p.setFont(_font(22))
        sp = [(cx - 50, cy - 10), (cx + 46, cy - 6),
              (cx - 46, cy + 60), (cx + 42, cy + 56)]
        sx, sy = sp[frame_index % 4]
        p.drawText(sx, sy, "✦")

    # --- REST: 晒太阳 ---
    elif state == PetState.REST:
        _draw_tail(p, cx, cy + 4)
        _draw_body(p, cx, cy + 4)
        _draw_paws_down(p, cx, cy + 4)
        _draw_head(p, cx, cy + 4)
        # 半闭眼（放松）
        _draw_eyes(p, cx, cy + 4, closed=True)
        _draw_nose(p, cx, cy + 4)
        # 太阳 — 右上角
        _draw_sun(p, cx + 54, cy - 44, frame_index)

    p.end()
    return pixmap


def generate_all_placeholder_frames() -> dict[PetState, list[QPixmap]]:
    """为所有 9 个状态生成占位帧序列。"""
    frame_counts = {
        PetState.IDLE: 4,
        PetState.WALK: 6,
        PetState.SLEEP: 4,
        PetState.HAPPY: 4,
        PetState.ALERT: 4,
        PetState.EAT: 6,
        PetState.PLAY: 6,
        PetState.GROOM: 4,
        PetState.REST: 4,
    }
    frames = {}
    for state, count in frame_counts.items():
        state_frames = []
        for i in range(count):
            state_frames.append(generate_placeholder_frame(state, i, count))
        frames[state] = state_frames
    return frames


# ============================================================
# SpriteAnimator
# ============================================================

class SpriteAnimator(QObject):
    """精灵帧动画控制器。"""

    state_changed = Signal(PetState)

    def __init__(self):
        super().__init__()
        self._frames: dict[PetState, list[QPixmap]] = {}
        self._current_state = PetState.IDLE
        self._current_frame = 0
        self._timer = QTimer()
        self._timer.timeout.connect(self._advance_frame)

    def load_frames(self, frames: dict[PetState, list[QPixmap]]) -> None:
        self._frames = frames

    def set_state(self, state: PetState) -> bool:
        if state == self._current_state:
            return True
        if not can_transition(self._current_state, state):
            return False
        self._current_state = state
        self._current_frame = 0
        interval = FRAME_INTERVALS.get(state, 500)
        self._timer.setInterval(interval)
        self.state_changed.emit(state)
        return True

    def start(self) -> None:
        if not self._frames:
            return
        interval = FRAME_INTERVALS.get(self._current_state, 500)
        self._timer.start(interval)

    def stop(self) -> None:
        self._timer.stop()

    def current_pixmap(self) -> QPixmap | None:
        frames = self._frames.get(self._current_state)
        if not frames:
            return None
        return frames[self._current_frame]

    @property
    def current_state(self) -> PetState:
        return self._current_state

    def _advance_frame(self) -> None:
        frames = self._frames.get(self._current_state)
        if frames:
            self._current_frame = (self._current_frame + 1) % len(frames)
