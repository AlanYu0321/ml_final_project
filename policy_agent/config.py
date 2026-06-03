from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
POLICY_DIR = DATA_DIR / "policies"
DEFAULT_MEMORY_PATH = DATA_DIR / "memory.json"
DEFAULT_AUDIT_PATH = DATA_DIR / "audit.log"

