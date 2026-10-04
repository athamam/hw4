"""Append-only audit trail of agent-loop activity -> output/audit_trail.json.

Every chat run records a row: timestamp, who asked, the model, each tool call
(name + short args + short result), the stop reason, and a short reply. The file is
never wiped between runs — new rows are appended, with an atomic write under a lock
so concurrent requests don't corrupt it.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic_ai.messages import (
    BaseToolCallPart,
    BaseToolReturnPart,
    ModelRequest,
    ModelResponse,
    RetryPromptPart,
    TextPart,
)
from pydantic_core import to_json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
AUDIT_PATH = ROOT / "output" / "audit_trail.json"

PREVIEW_CHARS = 200  # cap args/result/reply so the log stays readable
_lock = threading.Lock()


def _preview(value: Any) -> str:
    text = value if isinstance(value, str) else to_json(value).decode("utf-8", "replace")
    text = " ".join(text.split())
    return text if len(text) <= PREVIEW_CHARS else text[: PREVIEW_CHARS - 1] + "…"


def summarize_run(messages: list[Any]) -> tuple[list[dict[str, Any]], str]:
    """Pull tool calls (name/args/short result) and a stop reason out of a run."""
    calls: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    finish_reason: str | None = None

    for message in messages:
        if isinstance(message, ModelResponse):
            finish_reason = getattr(message, "finish_reason", None) or finish_reason
            for part in message.parts:
                if isinstance(part, BaseToolCallPart):
                    entry = {"tool": part.tool_name, "args": _preview(part.args_as_dict()), "result": None}
                    calls.append(entry)
                    by_id[part.tool_call_id] = entry
                elif isinstance(part, BaseToolReturnPart):
                    entry = by_id.get(part.tool_call_id)
                    if entry is not None:
                        entry["result"] = _preview(part.content)
        elif isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, (BaseToolReturnPart, RetryPromptPart)):
                    entry = by_id.get(part.tool_call_id)
                    if entry is not None:
                        entry["result"] = _preview(part.content)

    return calls, f"final answer (finish_reason={finish_reason or 'stop'})"


def append(entry: dict[str, Any]) -> None:
    """Append one run to output/audit_trail.json without touching earlier rows."""
    with _lock:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        rows: list[Any] = []
        if AUDIT_PATH.exists() and AUDIT_PATH.stat().st_size > 0:
            try:
                loaded = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
                rows = loaded if isinstance(loaded, list) else [loaded]
            except json.JSONDecodeError:
                # Never lose a corrupt log: set it aside, start fresh.
                stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                AUDIT_PATH.replace(AUDIT_PATH.with_name(f"audit_trail.corrupt-{stamp}.json"))
        rows.append(entry)
        tmp = AUDIT_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(AUDIT_PATH)


def record(
    *,
    user_message: str,
    model: str,
    who: str,
    tool_calls: list[dict[str, Any]],
    stopped: str,
    reply: str,
) -> None:
    append({
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "who": who,
        "user_message": _preview(user_message),
        "model": model,
        "tool_calls": tool_calls,
        "stopped": stopped,
        "reply": _preview(reply),
    })
