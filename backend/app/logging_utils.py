from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def log_tool_call(log_path: Path, tool: str, inputs: dict, outputs: dict) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool": tool,
        "inputs": inputs,
        "outputs": outputs,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=True) + "\n")
