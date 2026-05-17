"""LLM 工具注册与调用框架 — 兼容 OpenAI / Anthropic function calling"""
import json
import uuid
from datetime import datetime, date
from typing import Callable, Any


# ── 工具 Schema 定义（OpenAI function calling 格式）────────────────

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "create_event",
            "description": "创建日程事件",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "事件标题"},
                    "datetime_str": {"type": "string", "description": "ISO 8601 格式时间"},
                    "description": {"type": "string", "description": "事件描述"},
                    "category": {"type": "string", "enum": ["工作", "学习", "生活", "其他"], "description": "分类"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"], "description": "优先级"},
                },
                "required": ["title", "datetime_str"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_events",
            "description": "查询日程事件，支持日期范围和分类过滤",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "起始日期 (ISO 8601 日期)"},
                    "end_date": {"type": "string", "description": "结束日期 (ISO 8601 日期)"},
                    "category": {"type": "string", "description": "分类过滤"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_event",
            "description": "删除指定日程事件",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "事件 ID"},
                },
                "required": ["event_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_reminder",
            "description": "创建一个临时提醒",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "提醒内容"},
                    "delay_minutes": {"type": "integer", "description": "多少分钟后提醒"},
                },
                "required": ["text", "delay_minutes"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pet_state",
            "description": "获取宠物当前状态",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前日期和时间",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_habits",
            "description": "分析用户的日程习惯并给出建议",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


class ToolRegistry:
    """工具注册中心：管理工具 schema 和执行函数。"""

    def __init__(self):
        self._tools: dict[str, dict] = {}  # name -> {"func": Callable, "schema": dict}

    def register(self, name: str, func: Callable[..., str], schema: dict) -> None:
        """注册一个工具。

        Args:
            name: 工具名称
            func: 执行函数，接受关键字参数，返回 JSON 字符串
            schema: OpenAI function calling 格式的 schema
        """
        self._tools[name] = {"func": func, "schema": schema}

    def get_tools(self) -> list[dict]:
        """返回 OpenAI 格式的工具列表。"""
        return [t["schema"] for t in self._tools.values()]

    def get_anthropic_tools(self) -> list[dict]:
        """返回 Anthropic 格式的工具列表。"""
        result = []
        for t in self._tools.values():
            s = t["schema"]
            func = s.get("function", {})
            result.append({
                "name": func.get("name", ""),
                "description": func.get("description", ""),
                "input_schema": func.get("parameters", {"type": "object", "properties": {}}),
            })
        return result

    def execute(self, name: str, arguments: dict) -> str:
        """执行指定工具，返回结果 JSON 字符串。出错时返回错误信息。"""
        tool = self._tools.get(name)
        if not tool:
            return json.dumps({"error": f"未知工具: {name}"}, ensure_ascii=False)
        try:
            result = tool["func"](**arguments)
            return result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": f"工具执行失败: {e}"}, ensure_ascii=False)


# ── 工具实现函数 ─────────────────────────────────────────────────

def create_event_impl(schedule_store, **kwargs) -> str:
    """创建日程事件。"""
    from data.event import Event

    title = kwargs.get("title", "")
    datetime_str = kwargs.get("datetime_str", "")
    if not title or not datetime_str:
        return json.dumps({"error": "标题和时间不能为空"}, ensure_ascii=False)

    event = Event(
        title=title,
        datetime_str=datetime_str,
        description=kwargs.get("description", ""),
        category=kwargs.get("category", "其他"),
        priority=kwargs.get("priority", "medium"),
    )
    schedule_store.add(event)
    return json.dumps({"success": True, "message": f"日程已创建：{title}", "event_id": event.id}, ensure_ascii=False)


def query_events_impl(schedule_store, **kwargs) -> str:
    """查询日程事件。"""
    events = schedule_store.get_all()
    start_date = kwargs.get("start_date")
    end_date = kwargs.get("end_date")
    category = kwargs.get("category")

    filtered = []
    for e in events:
        # 日期过滤
        if start_date:
            try:
                event_date = datetime.fromisoformat(e.datetime_str).date()
                if event_date < date.fromisoformat(start_date):
                    continue
            except ValueError:
                continue
        if end_date:
            try:
                event_date = datetime.fromisoformat(e.datetime_str).date()
                if event_date > date.fromisoformat(end_date):
                    continue
            except ValueError:
                continue
        # 分类过滤
        if category and e.category != category:
            continue

        status = "已完成" if e.completed else "待办"
        filtered.append({
            "id": e.id,
            "title": e.title,
            "datetime": e.datetime_str,
            "category": e.category,
            "priority": e.priority,
            "status": status,
        })

    return json.dumps({"events": filtered, "count": len(filtered)}, ensure_ascii=False)


def delete_event_impl(schedule_store, event_id: str) -> str:
    """删除日程事件。"""
    success = schedule_store.delete(event_id)
    if success:
        return json.dumps({"success": True, "message": "事件已删除"}, ensure_ascii=False)
    return json.dumps({"success": False, "message": "未找到该事件"}, ensure_ascii=False)


def create_reminder_impl(reminder_manager, text: str, delay_minutes: int) -> str:
    """创建临时提醒。"""
    msg = reminder_manager.add_reminder(text, delay_minutes)
    return json.dumps({"success": True, "message": msg}, ensure_ascii=False)


def get_pet_state_impl(get_state_func) -> str:
    """获取宠物当前状态。"""
    state = get_state_func()
    return json.dumps({"state": state}, ensure_ascii=False)


def get_current_time_impl() -> str:
    """获取当前日期时间。"""
    now = datetime.now()
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return json.dumps({
        "datetime": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M"),
        "weekday": weekdays[now.weekday()],
    }, ensure_ascii=False)


def analyze_habits_impl(habit_analyzer) -> str:
    """分析日程习惯。"""
    result = habit_analyzer.analyze()
    return json.dumps({"analysis": result}, ensure_ascii=False)
