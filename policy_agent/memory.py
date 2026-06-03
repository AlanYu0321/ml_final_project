from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import DEFAULT_MEMORY_PATH


class JsonMemoryStore:
    """Small cross-session memory store keyed by user id."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or DEFAULT_MEMORY_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("{}", encoding="utf-8")

    def _read(self) -> dict[str, Any]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _write(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    def get_user(self, user_id: str) -> dict[str, Any]:
        return dict(self._read().get(user_id, {}))

    def remember(self, user_id: str, key: str, value: Any) -> None:
        data = self._read()
        user = dict(data.get(user_id, {}))
        user[key] = value
        data[user_id] = user
        self._write(data)

    def append_note(self, user_id: str, note: str) -> None:
        data = self._read()
        user = dict(data.get(user_id, {}))
        notes = list(user.get("notes", []))
        notes.append(note)
        user["notes"] = notes[-10:]
        data[user_id] = user
        self._write(data)

