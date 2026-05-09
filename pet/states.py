"""宠物动画状态定义与状态转换表"""
from enum import Enum


class PetState(Enum):
    """宠物动画状态枚举。"""
    IDLE = "idle"       # 挂在树枝上（慢悠悠）
    WALK = "walk"       # 缓慢爬行
    SLEEP = "sleep"     # 蜷缩睡觉
    HAPPY = "happy"     # 开心摇晃
    ALERT = "alert"     # 提醒警报状态


# 状态转换表：当前状态 -> 允许的目标状态列表
TRANSITIONS: dict[PetState, list[PetState]] = {
    PetState.IDLE:  [PetState.WALK, PetState.SLEEP, PetState.HAPPY, PetState.ALERT],
    PetState.WALK:  [PetState.IDLE, PetState.HAPPY, PetState.ALERT],
    PetState.SLEEP: [PetState.IDLE, PetState.HAPPY, PetState.ALERT],
    PetState.HAPPY: [PetState.IDLE, PetState.ALERT],
    PetState.ALERT: [PetState.IDLE],
}

# 各状态的帧间隔（毫秒）
FRAME_INTERVALS: dict[PetState, int] = {
    PetState.IDLE:  500,   # 慢悠悠挂在树枝上
    PetState.WALK:  300,   # 缓慢爬行
    PetState.SLEEP: 800,   # 蜷缩呼吸起伏
    PetState.HAPPY: 200,   # 开心摇晃（最快）
    PetState.ALERT: 150,   # 快速抖动（提醒警报）
}


def can_transition(current: PetState, target: PetState) -> bool:
    """检查从 current 状态是否可以转换到 target 状态。"""
    return target in TRANSITIONS.get(current, [])
