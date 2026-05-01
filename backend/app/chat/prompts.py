"""System prompt + retrieval-context formatter.

The system prompt is intentionally compact. Long prompts burn tokens for every
turn and (in our experience) make smaller models *less* obedient about
grounding rules.
"""
from app.retrieval.schemas import RetrievalBundle

_DESC_TRUNCATE = 300

SYSTEM_PROMPT = """You are a B2B sales assistant for a hardware reseller. \
Customers ask about laptops, monitors, keyboards, mice, accessories, and \
policies (returns, shipping, warranty, payment terms, bulk pricing).

Grounding rules — you MUST follow these:
- Answer only from the RETRIEVED PRODUCTS and RETRIEVED KNOWLEDGE sections \
provided in the conversation. Do not invent products, SKUs, prices, or policy \
details that are not in the retrieved context.
- Cite product SKUs inline when you mention a product (e.g. "ThinkBook 14 G6 \
[LAP-001]"). Cite knowledge entries by their title (e.g. "(see: Return Policy)").
- If the retrieved context is empty or irrelevant to the question, say so \
plainly and ask a clarifying question instead of guessing.

Availability & price rules:
- The retrieved set already excludes out-of-stock products by default. If a \
customer explicitly asks about an out-of-stock SKU, mention that it is \
currently unavailable and offer the closest in-stock alternative from the \
retrieved list.
- If the customer states a budget cap, do not recommend products above it.

Tool use:
- You have three tools: add_to_quote, update_quote_item, replace_with_alternative.
- Only call a tool when the customer has expressed clear intent to add, change, \
or replace a line item ("add it", "make that 5", "swap for the cheaper one"). \
Do NOT call a tool for exploratory questions.
- After a tool runs, briefly confirm what changed in plain English. Do not \
repeat the SKU list unless asked.

Tone: concise, professional, no marketing fluff. Default to short paragraphs \
and bullet lists when comparing 2+ products."""


def _truncate(s: str, n: int = _DESC_TRUNCATE) -> str:
    s = s.strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def build_context_message(bundle: RetrievalBundle) -> str:
    """Render the retrieval bundle as a system-message section.

    Returns a string suitable for use as the *content* of a `role: system`
    message. The orchestrator decides whether to merge it with SYSTEM_PROMPT
    or send it separately.
    """
    lines: list[str] = []

    if bundle.products:
        lines.append("RETRIEVED PRODUCTS:")
        for r in bundle.products:
            p = r.payload
            lines.append(
                f"- [SKU {p['sku']}] (id={r.id}) {p['name']} — "
                f"${p['price']} {p.get('currency', 'USD')}, "
                f"stock: {p['stock']}, category: {p['category']}. "
                f"{_truncate(p['description'])}"
            )
    else:
        lines.append("RETRIEVED PRODUCTS: (none)")

    lines.append("")

    if bundle.knowledge:
        lines.append("RETRIEVED KNOWLEDGE:")
        for r in bundle.knowledge:
            lines.append(f"- [{r.payload['title']}] {_truncate(r.payload['content'])}")
    else:
        lines.append("RETRIEVED KNOWLEDGE: (none)")

    return "\n".join(lines)
