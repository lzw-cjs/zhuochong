"""JSON 原子读写存储"""
import json
import os
import shutil
import tempfile
from collections.abc import Callable
from pathlib import Path

APPDATA_DIR = Path(os.environ.get("APPDATA", "~")) / "SmartDesktopPet"

# Migration registry: {store_name: {from_version: migration_fn}}
_MIGRATIONS: dict[str, dict[int, Callable]] = {}


def register_migration(store_name: str, from_version: int) -> Callable:
    """Decorator to register a migration function for a store.

    The decorated function receives the data dict and must return the
    migrated data dict.  Migrations are chained: v1->v2->v3 etc.
    """
    def decorator(fn: Callable) -> Callable:
        _MIGRATIONS.setdefault(store_name, {})[from_version] = fn
        return fn
    return decorator


class JsonStore:
    """JSON 文件的原子读写封装。

    使用 write-to-temp + os.replace 模式确保写入过程中断电或崩溃不会损坏数据。
    """

    def __init__(self, filename: str, store_name: str | None = None):
        self.filepath = APPDATA_DIR / filename
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self.store_name = store_name or Path(filename).stem

    def load(self, default: dict | None = None, current_version: int | None = None) -> dict:
        """读取 JSON 文件。文件不存在时返回 default。

        If current_version is provided and stored data has a different
        _schema_version, migrations are applied in order.  The migrated
        result is persisted back to disk and a .json.bak backup is
        created before migration begins.
        """
        if not self.filepath.exists():
            return default if default is not None else {}

        with open(self.filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        if current_version is not None:
            data = self._migrate(data, current_version)

        return data

    def save(self, data: dict) -> None:
        """原子写入 JSON 文件。

        先写入临时文件，再用 os.replace 原子替换目标文件。
        """
        fd, tmp_path = tempfile.mkstemp(
            dir=self.filepath.parent,
            suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self.filepath)
        except Exception:
            # 写入失败时清理临时文件
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def _migrate(self, data: dict, current_version: int) -> dict:
        """Apply registered migrations in sequence from stored version to current_version.

        Creates a .json.bak backup before running any migrations.
        """
        stored_version = data.get("_schema_version", 0)
        if stored_version == current_version:
            return data

        migrations = _MIGRATIONS.get(self.store_name, {})
        if not migrations:
            data["_schema_version"] = current_version
            return data

        # Backup before migration
        shutil.copy2(self.filepath, self.filepath.with_suffix(".json.bak"))

        version = stored_version
        while version < current_version:
            migrate_fn = migrations.get(version)
            if migrate_fn is not None:
                data = migrate_fn(data)
            version += 1

        data["_schema_version"] = current_version
        self.save(data)
        return data
