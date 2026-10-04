"""Pydantic models and agent dependencies shared across the backend.

These cover the catalogue API (product cards + detail), the chat contract the
React widget uses, and the result the PydanticAI agent returns.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field


# ---------- Product cards (used by the catalogue API and by chat results) ----------

class SizeStock(BaseModel):
    size: str
    quantity: int


class Product(BaseModel):
    """A product "card": the summary the grid, home page, and chat results render."""

    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str] = Field(default_factory=list)
    price: float
    image_url: str
    total_stock: int


class ProductDetail(Product):
    """Everything on a single-item page: card fields plus tags and per-size stock."""

    search_tags: list[str] = Field(default_factory=list)
    sizes: list[SizeStock] = Field(default_factory=list)


# ---------- Chat contract (React widget <-> FastAPI <-> agent) ----------

class PageContext(BaseModel):
    """Where the shopper is on the site, so 'this'/'it' can be resolved."""

    product_id: str | None = None
    product_name: str | None = None  # resolved server-side from product_id
    path: str | None = None


class CustomerContext(BaseModel):
    """The logged-in shopper the agent is talking to (never includes the password)."""

    user_id: int
    first_name: str
    last_name: str
    email: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    page: PageContext | None = None


class ChatHistoryMessage(BaseModel):
    role: str
    content: str
    products: list[Product] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """What the chat widget receives. `products` lets the agent surface cards
    (populated once the product tools land in Problem 6/7)."""

    reply: str
    products: list[Product] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)


class AgentResult(BaseModel):
    """Internal result produced by agent.run_agent()."""

    reply: str
    products: list[Product] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)


# ---------- Tool return types (what the agent sees from tools.py) ----------

class ProductMatch(BaseModel):
    """One hit from find_products: just enough to recognize and pick an item."""

    product_id: str
    name: str
    garment_type: str
    price: float
    colors: list[str] = Field(default_factory=list)
    total_stock: int


class ProductInfo(BaseModel):
    """get_product_info result: the facts needed to answer description/price questions."""

    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str] = Field(default_factory=list)
    price: float
    available_sizes: list[str] = Field(default_factory=list)
    total_stock: int


class StockResult(BaseModel):
    """check_stock result: stock broken out by size, with out-of-stock made explicit."""

    product_id: str
    name: str
    by_size: list[SizeStock] = Field(default_factory=list)
    in_stock_sizes: list[str] = Field(default_factory=list)
    out_of_stock_sizes: list[str] = Field(default_factory=list)
    total_stock: int
    # Set only when the customer asked about a specific size:
    requested_size: str | None = None
    requested_in_stock: bool | None = None
    requested_quantity: int | None = None


# ---------- Agent dependencies ----------

@dataclass
class CampusDeps:
    """Runtime context passed to the agent and its tools (via RunContext).

    Carries the database path so tools can read the catalogue/inventory, who the
    shopper is (if logged in), what page they're on, and collects any product
    cards a tool wants to show the shopper during a run.
    """

    db_path: Path
    shown_products: list[Product] = None  # type: ignore[assignment]
    customer: CustomerContext | None = None
    page: PageContext | None = None

    def __post_init__(self) -> None:
        if self.shown_products is None:
            self.shown_products = []
