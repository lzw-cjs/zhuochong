"""习惯分析器 — 分析日程模式并给出建议"""
from collections import Counter
from datetime import datetime


class HabitAnalyzer:
    """分析用户日程习惯，生成统计和建议。"""

    def __init__(self, schedule_store):
        self._store = schedule_store

    def analyze(self) -> str:
        """分析日程模式，返回建议文本。"""
        events = self._store.get_all()
        if len(events) < 3:
            return "日程数据还不够多，多用几天我就能帮你分析啦~"

        # 统计分类分布
        categories = Counter(e.category for e in events)
        completed = sum(1 for e in events if e.completed)
        total = len(events)

        # 统计高峰时段
        hours = []
        for e in events:
            try:
                h = datetime.fromisoformat(e.datetime_str).hour
                hours.append(h)
            except ValueError:
                pass

        peak_hour = Counter(hours).most_common(1)[0][0] if hours else None

        # 生成建议
        lines = [f"你共有 {total} 个日程，完成了 {completed} 个。"]

        if peak_hour:
            lines.append(f"你的日程高峰在 {peak_hour}:00 左右。")

        top_cat = categories.most_common(1)[0] if categories else None
        if top_cat:
            lines.append(f"最多的分类是「{top_cat[0]}」（{top_cat[1]}个）。")

        completion_rate = completed / max(total, 1)
        if completion_rate < 0.5:
            lines.append("完成率有点低哦，试试把大任务拆成小块？")
        elif completion_rate >= 0.8:
            lines.append("完成率很高，继续保持！")

        return "\n".join(lines)
