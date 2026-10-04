"""Agent tools for the Campus Customs assistant (Problem 6).

These let the agent read real data from data/campus_customs.db so it answers
with true descriptions, prices, and stock instead of guessing:

  - find_products(query):       search the catalogue to locate items
  - get_product_info(id):       description, price, colors, available sizes
  - check_stock(id, size=None): quantity on hand, by size, with sold-out flagged

All three read the database; none of them invent data. The agent is instructed
(prompts/prompt.md) to call them for any price/stock/description question.
"""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Callable

from pydantic_ai import RunContext

from models import CampusDeps, Product, ProductInfo, ProductMatch, SizeStock, StockResult

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DB_PATH = ROOT / "data" / "campus_customs.db"

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
MAX_MATCHES = 6  # keep tool output small so the prompt stays cheap and focused

# Filler/price words that shouldn't drive keyword matching (max_price handles budget).
_STOPWORDS = {
    "a", "an", "the", "for", "to", "of", "in", "on", "with", "and", "or", "me", "my",
    "i", "you", "do", "have", "any", "some", "show", "want", "need", "looking", "get",
    "buy", "please", "what", "whats", "is", "are", "something", "under", "over", "below",
    "above", "than", "less", "more", "cheaper", "cheapest", "around", "about", "price",
    "priced", "cost", "dollars", "dollar", "us", "that", "this", "it", "like",
}


def _tokens(query: str) -> list[str]:
    """Lowercase word tokens, dropping filler/price words and bare numbers."""
    words = re.findall(r"[a-z0-9]+", query.lower())
    return [w for w in words if w not in _STOPWORDS and not w.isdigit()]


def _matches(token: str, blob: str) -> bool:
    """Match a token against text, tolerating simple plurals (hoodies → hoodie)."""
    if token in blob:
        return True
    if len(token) > 3 and token.endswith("s") and token[:-1] in blob:
        return True
    return False


def _connect(ctx: RunContext[CampusDeps]) -> sqlite3.Connection:
    conn = sqlite3.connect(ctx.deps.db_path)
    conn.row_factory = sqlite3.Row
    return conn


def image_url(image_file_path: str) -> str:
    """Catalogue stores a path like 'products/foo.jpg'; the API serves it at /images/foo.jpg."""
    return "/images/" + Path(image_file_path).name


def parse_json_list(raw: str) -> list[str]:
    try:
        value = json.loads(raw)
        return value if isinstance(value, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def _stock_by_product(conn: sqlite3.Connection) -> dict[str, int]:
    return dict(conn.execute(
        "SELECT product_id, SUM(quantity) FROM inventory GROUP BY product_id"
    ).fetchall())


def _row_to_card(row: sqlite3.Row, total_stock: int) -> Product:
    """Build a full product card (image, name, price, description) for the page."""
    return Product(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        description=row["description"],
        colors=parse_json_list(row["colors"]),
        price=row["price"],
        image_url=image_url(row["image_file_path"]),
        total_stock=total_stock,
    )


def _record_card(ctx: RunContext[CampusDeps], card: Product) -> None:
    """Record a product card to show on the page, de-duplicated and order-preserving."""
    shown = ctx.deps.shown_products
    if all(c.product_id != card.product_id for c in shown):
        shown.append(card)


# ---------- Tools ----------

def _search(
    ctx: RunContext[CampusDeps],
    query: str,
    max_price: float | None = None,
    in_stock_only: bool = False,
    exclude_product_id: str | None = None,
) -> list[ProductMatch]:
    """Shared catalogue search used by find_products and suggest_alternatives.

    Scores rows by keyword overlap, optionally filters by price / in-stock /
    excluded id, records cards for the page, and returns compact matches.
    """
    tokens = _tokens(query)
    with _connect(ctx) as conn:
        totals = _stock_by_product(conn)
        rows = conn.execute("SELECT * FROM catalogue").fetchall()

    scored: list[tuple[int, sqlite3.Row]] = []
    for row in rows:
        pid = row["product_id"]
        if exclude_product_id and pid == exclude_product_id:
            continue
        if max_price is not None and row["price"] > max_price:
            continue
        if in_stock_only and totals.get(pid, 0) <= 0:
            continue
        blob = " ".join([
            row["name"], row["garment_type"], row["description"],
            row["colors"], row["search_tags"],
        ]).lower()
        # No tokens (e.g. a pure budget query) → price/stock filters alone select items.
        score = sum(1 for t in tokens if _matches(t, blob)) if tokens else 1
        if score:
            scored.append((score, row))

    scored.sort(key=lambda s: (-s[0], s[1]["name"]))
    top = [row for _, row in scored[:MAX_MATCHES]]

    # Record full cards so the website shows these matches on the page (Problem 7).
    for row in top:
        _record_card(ctx, _row_to_card(row, totals.get(row["product_id"], 0)))

    return [
        ProductMatch(
            product_id=row["product_id"],
            name=row["name"],
            garment_type=row["garment_type"],
            price=row["price"],
            colors=parse_json_list(row["colors"]),
            total_stock=totals.get(row["product_id"], 0),
        )
        for row in top
    ]


def find_products(
    ctx: RunContext[CampusDeps], query: str, max_price: float | None = None
) -> list[ProductMatch]:
    """Search the Campus Customs catalogue for products matching a shopper's words.

    Use this first to locate items by name, garment type (hoodie, crewneck, tee,
    quarter-zip...), color, sport, residential college, school, recipient (mom,
    dad, grandpa...), or any descriptive keyword. Returns up to a handful of the
    best matches with their product_id, which you pass to get_product_info or
    check_stock. Returns an empty list if nothing matches.

    Pass `max_price` for budget requests ("hoodies under $60", "nothing over $50")
    to return only items at or below that price.
    """
    return _search(ctx, query, max_price=max_price)


def suggest_alternatives(
    ctx: RunContext[CampusDeps], query: str, exclude_product_id: str | None = None
) -> list[ProductMatch]:
    """Find IN-STOCK products similar to `query`, for when the item or size a shopper
    wanted is sold out or we don't carry it. Only returns items with stock available,
    so you never steer someone toward another dead end. Pass `exclude_product_id` to
    leave out the item they already looked at. Results also appear as cards on the page.
    """
    return _search(ctx, query, in_stock_only=True, exclude_product_id=exclude_product_id)


def get_product_info(ctx: RunContext[CampusDeps], product_id: str) -> ProductInfo | str:
    """Get the full details for one product: description, price, colors, and which
    sizes currently have any stock. Use this for description and price questions.
    `product_id` comes from find_products. Returns a short message if the id is unknown.
    """
    with _connect(ctx) as conn:
        row = conn.execute(
            "SELECT * FROM catalogue WHERE product_id = ?", (product_id,)
        ).fetchone()
        if row is None:
            return f"No product found with id '{product_id}'. Try find_products first."
        inv = dict(conn.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)
        ).fetchall())

    # Also surface this item as a card on the page.
    _record_card(ctx, _row_to_card(row, sum(inv.values())))

    available = [s for s in SIZE_ORDER if inv.get(s, 0) > 0]
    return ProductInfo(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        description=row["description"],
        colors=parse_json_list(row["colors"]),
        price=row["price"],
        available_sizes=available,
        total_stock=sum(inv.values()),
    )


def check_stock(
    ctx: RunContext[CampusDeps], product_id: str, size: str | None = None
) -> StockResult | str:
    """Check how many units are in stock for a product, broken out by size.

    Pass `size` (XS, S, M, L, XL, XXL) when the customer asks about one size; the
    result then also says whether that size is in stock and how many. Sizes with
    zero quantity are listed in out_of_stock_sizes — tell the customer clearly when
    something is sold out. `product_id` comes from find_products. Returns a short
    message if the id is unknown.
    """
    with _connect(ctx) as conn:
        row = conn.execute(
            "SELECT name FROM catalogue WHERE product_id = ?", (product_id,)
        ).fetchone()
        if row is None:
            return f"No product found with id '{product_id}'. Try find_products first."
        inv = dict(conn.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)
        ).fetchall())

    by_size = [SizeStock(size=s, quantity=inv[s]) for s in SIZE_ORDER if s in inv]
    in_stock = [s.size for s in by_size if s.quantity > 0]
    out_of_stock = [s.size for s in by_size if s.quantity == 0]

    result = StockResult(
        product_id=product_id,
        name=row["name"],
        by_size=by_size,
        in_stock_sizes=in_stock,
        out_of_stock_sizes=out_of_stock,
        total_stock=sum(inv.values()),
    )

    if size is not None:
        norm = size.strip().upper()
        result.requested_size = norm
        if norm in inv:
            result.requested_quantity = inv[norm]
            result.requested_in_stock = inv[norm] > 0
        else:
            # Unknown size label for this product: treat as unavailable, not invented.
            result.requested_quantity = 0
            result.requested_in_stock = False
    return result


# Registered on the agent in agent.py.
TOOLS: list[Callable[..., Any]] = [
    find_products,
    get_product_info,
    check_stock,
    suggest_alternatives,
]
