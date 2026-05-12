"""使用 SenseNova API 生成项目架构图"""
import os
import sys
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env
load_dotenv()

BASE_URL = os.getenv("SNSDK_BASE_URL", "https://token.sensenova.cn/v1")
API_KEY = os.getenv("SNSDK_API_KEY", "")

if not API_KEY:
    print("错误：请在 .env 文件中设置 SNSDK_API_KEY")
    sys.exit(1)


def generate_image(prompt: str, output_path: str = "arch_diagram.png"):
    """调用 SenseNova 文生图 API"""
    url = f"{BASE_URL}/images/generations"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "sensenova-u1-fast",
        "prompt": prompt,
        "n": 1,
        "size": "2752x1536",  # 16:9 横版
    }

    print(f"正在生成架构图...")
    print(f"提示词: {prompt[:80]}...")

    resp = requests.post(url, headers=headers, json=payload, timeout=120)

    if resp.status_code != 200:
        print(f"API 错误: {resp.status_code}")
        print(resp.text)
        return None

    data = resp.json()

    # 获取图片 URL
    if "data" in data and len(data["data"]) > 0:
        image_url = data["data"][0].get("url") or data["data"][0].get("b64_json")
        if image_url and image_url.startswith("http"):
            # 下载图片
            img_resp = requests.get(image_url, timeout=60)
            with open(output_path, "wb") as f:
                f.write(img_resp.content)
            print(f"架构图已保存: {output_path}")
            return output_path
        elif image_url:
            # base64 编码
            import base64
            img_data = base64.b64decode(image_url)
            with open(output_path, "wb") as f:
                f.write(img_data)
            print(f"架构图已保存: {output_path}")
            return output_path

    print("未获取到图片数据")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return None


if __name__ == "__main__":
    # 桌面宠物项目架构图提示词
    arch_prompt = """
请生成一张专业的软件系统架构图，主题是"智能桌面宠物（Smart Desktop Pet）"项目。

架构要求：
1. 采用分层架构，从上到下分为 5 层：
   - UI 表现层：主窗口(Window)、系统托盘(Tray)、气泡提示(Bubble)、聊天面板(ChatPanel)、日程面板(SchedulePanel)
   - 交互控制层：行为控制(Behavior)、聊天引擎(ChatEngine)、拖拽交互(Drag)、右键菜单(ContextMenu)
   - 核心逻辑层：状态机(States)、动画引擎(Animator)、提醒引擎(ReminderEngine)、超时检测(OverdueDetector)
   - 数据存储层：设置(Settings)、事件(Event)、日历(Calendar)、JSON存储(JsonStore)
   - 基础设施层：音效管理(SoundManager)、资源路径(Assets)、Schema迁移(Migration)

2. 视觉风格：
   - 浅色背景，使用蓝色系为主色调
   - 每层用不同深浅的颜色区分
   - 模块之间用箭头表示依赖关系
   - 中文标注模块名称
   - 专业简洁的扁平化设计

3. 右上角标注技术栈：Python + PySide6 + JSON Storage
"""

    # 确保输出目录存在
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "arch_diagram.png"

    result = generate_image(arch_prompt, str(output_path))
    if result:
        print(f"\n生成完成！文件: {result}")
