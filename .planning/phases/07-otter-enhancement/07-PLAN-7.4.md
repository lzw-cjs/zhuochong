# Plan 7.4 — 节日换装系统

**Wave:** 3 (依赖 7.1 的 animator, 独立于 7.2/7.3)
**Requirements:** OTTER-05

## Goal
水獭在节日期间自动换装，支持春节/中秋/端午/国庆/元旦/儿童节，含农历转换。

## Tasks

### T1: 安装依赖
```bash
pip install lunardate
```

### T2: 新建 `data/holidays.json` — 节日数据
```json
{
  "holidays": [
    {"id": "spring_festival", "name": "春节", "type": "lunar", "month": 1, "day": 1, "duration_days": 3, "costume": "red_lantern_hat", "emoji": "🧧"},
    {"id": "mid_autumn", "name": "中秋节", "type": "lunar", "month": 8, "day": 15, "duration_days": 1, "costume": "moon_cake", "emoji": "🥮"},
    {"id": "dragon_boat", "name": "端午节", "type": "lunar", "month": 5, "day": 5, "duration_days": 1, "costume": "dragon_hat", "emoji": "🐉"},
    {"id": "national_day", "name": "国庆节", "type": "solar", "month": 10, "day": 1, "duration_days": 3, "costume": "flag_ribbon", "emoji": "🇨🇳"},
    {"id": "new_year", "name": "元旦", "type": "solar", "month": 1, "day": 1, "duration_days": 1, "costume": "party_hat", "emoji": "🎉"},
    {"id": "children_day", "name": "儿童节", "type": "solar", "month": 6, "day": 1, "duration_days": 1, "costume": "balloon", "emoji": "🎈"}
  ]
}
```

### T3: 新建 `data/costumes.json` — 服装绘制命令
每个服装是 QPainter 绘制指令列表：
```json
{
  "red_lantern_hat": {
    "type": "hat",
    "commands": [
      {"shape": "ellipse", "x": 10, "y": 0, "w": 12, "h": 10, "color": [220, 20, 20]},
      {"shape": "rect", "x": 14, "y": -2, "w": 4, "h": 4, "color": [255, 215, 0]},
      {"shape": "line", "x1": 16, "y1": -2, "x2": 16, "y2": -6, "color": [139, 69, 19]}
    ]
  }
}
```
- 6 个节日各一个服装
- 类型：hat（头上）、ribbon（身上）、held_item（手中）

### T4: 新建 `pet/holiday_engine.py` — 节日检测引擎
```python
class HolidayEngine(QObject):
    holiday_active = Signal(str, str, str)  # holiday_id, costume_id, emoji
    holiday_ended = Signal()

    def __init__(self):
        # 加载 holidays.json
        # QTimer 每小时检查一次

    def _check(self):
        # 获取今天日期
        # 遍历 holidays
        # lunar 类型 → lunardate 转换
        # 在时间窗口内 → emit holiday_active
        # 不在窗口内且之前活跃 → emit holiday_ended
```

### T5: 新建 `pet/costume.py` — 换装渲染器
```python
class CostumeRenderer:
    def load_costumes(self, path: Path):
        # 加载 costumes.json

    def apply_costume(self, base_pixmap: QPixmap) -> QPixmap:
        # 创建新 QPixmap(32, 32)
        # QPainter: 先画 base，再画服装叠加
        # 根据 commands 逐个执行绘制

    def set_active_costume(self, costume_id: str):
    def clear_costume(self):
    def has_active_costume(self) -> bool:
```

### T6: 集成到 `main.py`
- 创建 HolidayEngine() 和 CostumeRenderer()
- 连接 holiday_active → costume_renderer.set_active_costume
- 连接 holiday_ended → costume_renderer.clear_costume
- 在 update_display() 中：先应用服装再设置 pixmap
- 节日触发时 bubble 显示 "🧧 节日快乐！"

### T7: 更新 `data/settings.py`
- 添加 `costume_enabled: bool = True`
- Schema 版本升到 2，注册迁移

## 验证
```bash
python main.py
# 修改系统日期到春节，观察换装
# 修改系统日期到非节日，观察服装消失
python -m pytest tests/  # 无回归
```

## 交付物
- [x] `data/holidays.json` — 节日数据
- [x] `data/costumes.json` — 服装绘制命令
- [x] `pet/holiday_engine.py` — 节日检测引擎
- [x] `pet/costume.py` — 换装渲染器
- [x] `data/settings.py` — costume_enabled
- [x] `main.py` — 集成
- [x] `pip install lunardate` — 农历依赖
