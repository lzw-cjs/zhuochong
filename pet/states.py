"""宠物动画状态定义与状态转换表"""
from enum import Enum


class PetState(Enum):
    """宠物动画状态枚举。"""
    IDLE = "idle"       # 坐姿（水獭）
    WALK = "walk"       # 行走
    SLEEP = "sleep"     # 蜷缩睡觉
    HAPPY = "happy"     # 开心弹跳
    ALERT = "alert"     # 提醒警报状态
    EAT = "eat"         # 吃鱼
    PLAY = "play"       # 玩石头
    GROOM = "groom"     # 梳理毛发
    REST = "rest"       # 晒太阳休息


# 状态转换表：当前状态 -> 允许的目标状态列表
TRANSITIONS: dict[PetState, list[PetState]] = {
    PetState.IDLE:  [PetState.WALK, PetState.SLEEP, PetState.HAPPY, PetState.ALERT, PetState.EAT, PetState.PLAY, PetState.GROOM, PetState.REST],
    PetState.WALK:  [PetState.IDLE, PetState.HAPPY, PetState.ALERT, PetState.EAT],
    PetState.SLEEP: [PetState.IDLE, PetState.HAPPY, PetState.ALERT],
    PetState.HAPPY: [PetState.IDLE, PetState.ALERT],
    PetState.ALERT: [PetState.IDLE],
    PetState.EAT:   [PetState.IDLE, PetState.HAPPY, PetState.ALERT],
    PetState.PLAY:  [PetState.IDLE, PetState.WALK, PetState.HAPPY, PetState.ALERT],
    PetState.GROOM: [PetState.IDLE, PetState.WALK, PetState.ALERT],
    PetState.REST:  [PetState.IDLE, PetState.SLEEP, PetState.HAPPY, PetState.ALERT],
}

# 各状态的帧间隔（毫秒）
FRAME_INTERVALS: dict[PetState, int] = {
    PetState.IDLE:  500,   # 坐姿慢悠悠
    PetState.WALK:  300,   # 行走
    PetState.SLEEP: 800,   # 蜷缩呼吸起伏
    PetState.HAPPY: 200,   # 开心弹跳（最快）
    PetState.ALERT: 150,   # 快速抖动（提醒警报）
    PetState.EAT:   350,   # 吃鱼
    PetState.PLAY:  250,   # 玩石头
    PetState.GROOM: 400,   # 梳理毛发
    PetState.REST:  600,   # 晒太阳休息
}


def can_transition(current: PetState, target: PetState) -> bool:
    """检查从 current 状态是否可以转换到 target 状态。"""
    return target in TRANSITIONS.get(current, [])
