from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import DEFAULT_AUDIT_PATH


@dataclass
class AuditEvent:
    event_type: str
    user_id: str
    question: str
    decision: str
    tool_calls: list[str]
    metadata: dict[str, Any]
    ts: str


class AuditLogger:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or DEFAULT_AUDIT_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(
        self,
        *,
        event_type: str,
        user_id: str,
        question: str,
        decision: str,
        tool_calls: list[str],
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            question=question,
            decision=decision,
            tool_calls=tool_calls,
            metadata=metadata or {},
            ts=datetime.now(timezone.utc).isoformat(),
        )
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(event), sort_keys=True) + "\n")
        return event

