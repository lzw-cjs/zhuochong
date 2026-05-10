---
wave: 2
depends_on:
  - P4.3
files_modified:
  - data/schedule_store.py
  - pet/schedule_panel.py
autonomous: true
---

# P4.4 — 导入导出

## 目标

实现 JSON 格式的事件导入导出。

**覆盖需求：** SCH-04

---

## 任务

### 任务 1：在 ScheduleStore 中添加导入导出方法

```python
    def export_json(self, filepath: str) -> None:
        """导出所有事件到 JSON 文件。"""
        data = {"events": self._load_events()}
        # 使用原子写入
        import tempfile, os
        fd, tmp = tempfile.mkstemp(suffix=".json")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, filepath)
        except:
            os.unlink(tmp)
            raise

    def import_json(self, filepath: str) -> int:
        """从 JSON 文件导入事件，返回导入数量。"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        imported = data.get("events", [])
        existing = self._load_events()
        existing_ids = {e.get("id") for e in existing}
        new_events = [e for e in imported if e.get("id") not in existing_ids]
        existing.extend(new_events)
        self._save_events(existing)
        return len(new_events)
```

### 任务 2：在面板中添加导入导出按钮

在 SchedulePanel 底部添加"导入"和"导出"按钮，使用 QFileDialog 选择文件。

**验收标准：**
- 导出生成 JSON 文件
- 导入合并事件（不重复）
- 导入导出使用 UTF-8 编码
