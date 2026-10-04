"""Campus Customs backend (FastAPI app).

Serves the product catalogue, per-size inventory, product images, and account
auth, and exposes /api/chat backed by the PydanticAI shopping agent (agent.py).

Run from the backend/ folder:
    uvicorn main:app --reload --port 8000

API docs:  http://127.0.0.1:8000/docs
Frontend:  http://127.0.0.1:5173  (Vite proxies /api and /images here)
"""

import json
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import memory
from agent import run_agent
from db import DATA_DIR, get_db
from models import (
    ChatHistoryMessage,
    ChatRequest,
    ChatResponse,
    CustomerContext,
    PageContext,
    Product,
    ProductDetail,
)
from routes_auth import PublicUser, get_current_user, get_optional_user
from routes_auth import router as auth_router

HERE = Path(__file__).resolve().parent
HW4_DIR = HERE.parent
# PORTKEY_API_KEY lives in the course-root .env (three levels up); load hw4/.env too.
load_dotenv(HW4_DIR / ".env")
load_dotenv(HW4_DIR.parent.parent / ".env")

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]

app = FastAPI(title="Campus Customs API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

# image_file_path in the DB is relative to data/ (e.g. "products/foo.jpg"),
# so mounting data/products at /images gives /images/foo.jpg.
app.mount("/images", StaticFiles(directory=DATA_DIR / "products"), name="images")


def image_url(image_file_path: str) -> str:
    return "/images/" + Path(image_file_path).name


def product_summary(row: sqlite3.Row, total_stock: int) -> dict:
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "garment_type": row["garment_type"],
        "description": row["description"],
        "colors": json.loads(row["colors"]),
        "price": row["price"],
        "image_url": image_url(row["image_file_path"]),
        "total_stock": total_stock,
    }


# ---------- Routes ----------

@app.get("/api/health")
def health() -> dict:
    import os
    return {"status": "ok", "portkey_key_set": bool(os.getenv("PORTKEY_API_KEY"))}


@app.get("/api/products", response_model=list[Product])
def list_products() -> list[dict]:
    with get_db() as conn:
        stock = dict(conn.execute(
            "SELECT product_id, SUM(quantity) FROM inventory GROUP BY product_id"
        ).fetchall())
        rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
    return [product_summary(r, stock.get(r["product_id"], 0)) for r in rows]


@app.get("/api/products/{product_id}", response_model=ProductDetail)
def get_product(product_id: str) -> dict:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM catalogue WHERE product_id = ?", (product_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        inv = dict(conn.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)
        ).fetchall())

    sizes = [{"size": s, "quantity": inv[s]} for s in SIZE_ORDER if s in inv]
    return {
        **product_summary(row, sum(inv.values())),
        "search_tags": json.loads(row["search_tags"]),
        "sizes": sizes,
    }


def _resolve_page(page: PageContext | None) -> PageContext | None:
    """Fill in the product name from product_id so the agent can refer to 'this' item."""
    if page is None or not page.product_id:
        return page
    with get_db() as conn:
        row = conn.execute(
            "SELECT name FROM catalogue WHERE product_id = ?", (page.product_id,)
        ).fetchone()
    page.product_name = row["name"] if row else None
    return page


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest, user: PublicUser | None = Depends(get_optional_user)) -> ChatResponse:
    """A message from the website chat widget, answered by the PydanticAI agent.

    Guests can chat. For logged-in users we load their prior thread so the agent
    remembers them, then save this exchange back to the database.
    """
    customer = None
    history = None
    if user is not None:
        customer = CustomerContext(
            user_id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
        )
        history = memory.load_history_for_agent(user.id)

    result = run_agent(
        req.message,
        customer=customer,
        page=_resolve_page(req.page),
        history=history,
    )

    # Persist this turn for logged-in users only (guests get no stored history).
    if user is not None:
        memory.save_message(user.id, "user", req.message)
        memory.save_message(user.id, "assistant", result.reply, result.products)

    return ChatResponse(
        reply=result.reply,
        products=result.products,
        tools_used=result.tools_used,
    )


@app.get("/api/chat/history", response_model=list[ChatHistoryMessage])
def chat_history(user: PublicUser = Depends(get_current_user)) -> list[ChatHistoryMessage]:
    """The logged-in user's saved chat thread, to reload when they return."""
    return memory.load_history_for_ui(user.id)


@app.delete("/api/chat/history")
def clear_chat_history(user: PublicUser = Depends(get_current_user)) -> dict:
    deleted = memory.clear_history(user.id)
    return {"deleted": deleted}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
