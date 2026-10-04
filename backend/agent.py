"""Campus Customs shopping assistant: a PydanticAI agent on gpt-5.6-luna via Portkey.

The agent is loaded from two things:
  1. its instructions, read from prompts/prompt.md (CC voice + safety), and
  2. its model, gpt-5.6-luna, reached through the Portkey gateway using
     PORTKEY_API_KEY from the course-root .env.

Product-lookup, stock, and alternative-suggestion tools (tools.py) are registered via
TOOLS. Every run is appended to output/audit_trail.json (audit.py).
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from dotenv import load_dotenv  # noqa: E402
from openai import AsyncOpenAI  # noqa: E402
from pydantic_ai import Agent, RunContext  # noqa: E402
from pydantic_ai.messages import (  # noqa: E402
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)
from pydantic_ai.models.openai import OpenAIResponsesModel  # noqa: E402
from pydantic_ai.providers.openai import OpenAIProvider  # noqa: E402
from pydantic_ai.usage import UsageLimits  # noqa: E402

import audit
from models import AgentResult, CampusDeps, CustomerContext, PageContext
from tools import DB_PATH, TOOLS

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
# Load .env from hw4/, then the course root (05. MGT 409) where PORTKEY_API_KEY lives.
load_dotenv(ROOT / ".env")
load_dotenv(ROOT.parent.parent / ".env")

MODEL_NAME = "gpt-5.6-luna"
PORTKEY_BASE_URL = os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1").rstrip("/")
PROMPT_PATH = HERE / "prompts" / "prompt.md"
MAX_MODEL_REQUESTS = 8  # a few tool rounds are plenty for a shopping question


def _build_agent() -> Agent[CampusDeps, str]:
    # The API key stays server-side: read from the environment, sent only to the
    # Portkey gateway as a header. It is never returned to the browser.
    api_key = os.getenv("PORTKEY_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("PORTKEY_API_KEY is not set (add it to the course-root .env).")
    client = AsyncOpenAI(
        api_key=api_key,
        base_url=PORTKEY_BASE_URL,
        default_headers={"x-portkey-api-key": api_key, "x-portkey-provider": "openai"},
    )
    model = OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))
    agent = Agent(
        model,
        deps_type=CampusDeps,
        instructions=PROMPT_PATH.read_text(encoding="utf-8"),
        tools=TOOLS,
    )

    # Dynamic instructions: tell the agent who it's talking to and what page they're
    # on, pulled from deps at run time. This is how "do you have this in pink" works.
    @agent.instructions
    def who_and_where(ctx: RunContext[CampusDeps]) -> str:
        lines: list[str] = []
        cust = ctx.deps.customer
        if cust is not None:
            lines.append(
                f"You are chatting with a logged-in customer: {cust.first_name} "
                f"{cust.last_name} (email: {cust.email}). Greet them by first name "
                "when it feels natural, and you may refer to earlier messages in this "
                "conversation."
            )
        else:
            lines.append("You are chatting with a guest (not logged in).")

        page = ctx.deps.page
        if page is not None and page.product_id:
            label = page.product_name or page.product_id
            lines.append(
                f'The shopper is currently on the product page for "{label}" '
                f'(product_id: "{page.product_id}"). If they say "this", "it", '
                '"this one", or ask about its colors/sizes/price without naming a '
                "product, they mean this item — call get_product_info or check_stock "
                f'with product_id "{page.product_id}".'
            )
        return "\n".join(lines)

    return agent


def _to_message_history(pairs: list[tuple[str, str]]) -> list[ModelMessage]:
    """Turn stored (role, content) rows into PydanticAI message history to replay."""
    history: list[ModelMessage] = []
    for role, content in pairs:
        if role == "user":
            history.append(ModelRequest(parts=[UserPromptPart(content=content)]))
        else:
            history.append(ModelResponse(parts=[TextPart(content=content)]))
    return history


def run_agent(
    message: str,
    customer: CustomerContext | None = None,
    page: PageContext | None = None,
    history: list[tuple[str, str]] | None = None,
) -> AgentResult:
    """Run one turn and return the agent's reply plus any product cards it surfaced.

    `customer` and `page` populate the agent's context (who's chatting / what page).
    `history` is prior (role, content) pairs for logged-in users, replayed so the
    agent remembers the conversation.
    """
    deps = CampusDeps(db_path=DB_PATH, customer=customer, page=page)
    who = customer.email if customer is not None else "guest"
    try:
        run = _build_agent().run_sync(
            message,
            deps=deps,
            message_history=_to_message_history(history) if history else None,
            usage_limits=UsageLimits(request_limit=MAX_MODEL_REQUESTS),
        )
    except Exception as exc:  # keep the chat alive even if the model call fails
        detail = f"{type(exc).__name__}: {exc}"[:300]
        reply = (
            "Sorry, our shop assistant hit a snag and couldn't answer just now. "
            "Please try again in a moment."
        )
        audit.record(
            user_message=message, model=MODEL_NAME, who=who,
            tool_calls=[], stopped=f"error: {detail}", reply=reply,
        )
        return AgentResult(reply=reply, tools_used=[f"error: {detail}"])

    tool_calls, stopped = audit.summarize_run(run.new_messages())
    audit.record(
        user_message=message, model=MODEL_NAME, who=who,
        tool_calls=tool_calls, stopped=stopped, reply=run.output,
    )
    tools_used = list(dict.fromkeys(c["tool"] for c in tool_calls))
    return AgentResult(reply=run.output, products=list(deps.shown_products), tools_used=tools_used)
