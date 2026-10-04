"""Customer chat memory, stored in the existing `chat_messages` table.

Only logged-in users get persistence: each turn we save the shopper's message and
the agent's reply (plus any product cards it showed) keyed by `user_id`. On their
return we reload the thread so the conversation — and the agent's memory of it —
picks up where it left off. Guests are never written here.

Table (data/campus_customs.db):
    chat_messages(id, user_id, role, content, products_json, created_at)
"""

from __future__ import annotations

import json

from db import get_db
from models import ChatHistoryMessage, Product

MAX_HISTORY_MESSAGES = 40  # cap how much past context we replay to the model


def save_message(
    user_id: int, role: str, content: str, products: list[Product] | None = None
) -> None:
    products_json = (
        json.dumps([p.model_dump() for p in products]) if products else None
    )
    with get_db() as conn:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) "
            "VALUES (?, ?, ?, ?)",
            (user_id, role, content, products_json),
        )
        conn.commit()


def _rows_for_user(user_id: int) -> list:
    with get_db() as conn:
        return conn.execute(
            "SELECT role, content, products_json FROM chat_messages "
            "WHERE user_id = ? ORDER BY id",
            (user_id,),
        ).fetchall()


def load_history_for_ui(user_id: int) -> list[ChatHistoryMessage]:
    """Full thread for the chat widget to render when the user returns."""
    out: list[ChatHistoryMessage] = []
    for row in _rows_for_user(user_id):
        products: list[Product] = []
        if row["products_json"]:
            try:
                products = [Product(**p) for p in json.loads(row["products_json"])]
            except (json.JSONDecodeError, TypeError, ValueError):
                products = []
        out.append(ChatHistoryMessage(role=row["role"], content=row["content"], products=products))
    return out


def load_history_for_agent(user_id: int) -> list[tuple[str, str]]:
    """Recent (role, content) pairs to replay to the model as message history."""
    rows = _rows_for_user(user_id)
    pairs = [(r["role"], r["content"]) for r in rows if r["content"]]
    return pairs[-MAX_HISTORY_MESSAGES:]


def clear_history(user_id: int) -> int:
    with get_db() as conn:
        cur = conn.execute("DELETE FROM chat_messages WHERE user_id = ?", (user_id,))
        conn.commit()
        return cur.rowcount
