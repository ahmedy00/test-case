# B2B Sales Assistant

## What this is

An AI-powered B2B sales assistant for a generic hardware catalog (laptops, monitors, peripherals, accessories). Two surfaces — a React admin panel and an Expo mobile client — chat with an LLM that answers product and policy questions using grounded retrieval (every cited source comes from the database) and performs real DB-mutating actions on a shared draft quote (e.g. *"add two ThinkBooks"*). The system is designed to keep working without an OpenAI key: a templated fallback path serves retrieval-grounded responses over the same SSE event stream.

## Quick start

Prerequisites: Docker Desktop (Compose v2), Node 20+ for the mobile target.

```bash
cp .env.example .env                                    # add OPENAI_API_KEY if you have one
docker compose up -d --build                            # db + backend + web
docker compose exec backend alembic upgrade head        # run migrations
docker compose exec backend python -m app.seed.seed     # seed products + knowledge
# Web:    http://localhost:5173
# Backend http://localhost:8000  (OpenAPI docs at /docs)
# DB:     localhost:5433  (mapped from container 5432)
cd mobile && npm install && npx expo start              # press `w` for web at :8081
```

## OpenAI key

If `OPENAI_API_KEY` is set in `.env`, the assistant uses `gpt-4o-mini` for chat with native function calling and `text-embedding-3-small` for retrieval. If it is unset, the assistant falls back to a **templated** response built from FTS-retrieved products and knowledge entries. Both paths emit the same SSE event types (`session`, `sources`, `chunk`, `action`, `done`, `error`). The fallback path emits **no** `action` events by design — performing real tool calls without an LLM would require pattern-matching the user's intent, which is brittle. This is deliberate, not a bug. The fallback's role is to keep retrieval and citations working when the LLM is unavailable.

## Architecture overview

```
.
├── backend/        FastAPI + SQLAlchemy 2.x + Alembic
│   └── app/
│       ├── api/         REST routers (chat, search, quotes, products, knowledge, health)
│       ├── chat/        Orchestrator, fallback, tool handlers, prompts
│       ├── retrieval/   pgvector + FTS hybrid, embedding client
│       ├── models/      ORM models (sessions, messages, products, knowledge, quotes)
│       ├── seed/        Idempotent seed data (catalog + knowledge)
│       └── alembic/     Migrations
├── web/            React 18 + Vite + TypeScript
│   └── src/{api,components,hooks,pages,session.ts}
├── mobile/         Expo + React Native + TypeScript (XHR-based SSE)
│   └── src/{api,components,hooks,screens,session.ts}
├── docker-compose.yml
├── CLAUDE.md       Locked architectural decisions
├── AI_USAGE.md     How AI tooling was used while building this
└── KNOWN_LIMITATIONS.md
```

`CLAUDE.md` is the authoritative source for locked decisions (tech stack, polling cadence, fallback contract, out-of-scope list).

## Streaming protocol

`POST /chat/stream` returns `text/event-stream`. Event types and their payload shapes:

| Event     | When                                              | Payload                                                                                  |
|-----------|---------------------------------------------------|------------------------------------------------------------------------------------------|
| `session` | Only when the request omits `session_id`          | `{"session_id": "<uuid>"}`                                                               |
| `sources` | Once per turn, before any chunks                  | `{"products": [...], "knowledge": [...], "method_used": "vector"\|"fts"\|"mixed"}`       |
| `chunk`   | Streamed text deltas (LLM or fallback)            | `{"delta": "..."}`                                                                       |
| `action`  | Each successful or failed tool call (LLM path)    | `{"tool", "args", "result", "status": "success"\|"error", "message"}`                    |
| `done`    | Once at end of stream                             | `{"message_id": <int>}`                                                                  |
| `error`   | Non-recoverable failure                           | `{"code": "...", "message": "..."}`                                                      |

Each event is a standard SSE frame (`event: <name>\ndata: <json>\n\n`).

## Tools (LLM function calls)

| Tool                       | Purpose                                                                  |
|----------------------------|--------------------------------------------------------------------------|
| `add_to_quote`             | Add a product to the active draft quote, or increment quantity if present. |
| `update_quote_item`        | Set a new quantity on an existing quote line.                            |
| `replace_with_alternative` | Swap a quote line's product for a different SKU, preserving quantity.    |

## Business rules supported

- **Price limit**: `max_price` filters products before the LLM ever sees them.
- **Stock**: out-of-stock products are excluded from retrieval by default. The `add_to_quote` tool still allows adding OOS items but returns a warning in the action message — the LLM can choose to surface it.
- **Policy questions**: routed through the knowledge base. The LLM is instructed to cite knowledge entries; the fallback path also surfaces them.
- **Duplicate adds**: enforced at the DB layer via `INSERT ... ON CONFLICT (quote_id, product_id) DO UPDATE SET quantity = quote_items.quantity + EXCLUDED.quantity`. Two identical `add_to_quote` calls produce one row with summed quantity, not two rows.

## Testing

```bash
docker compose exec backend pytest -v
```

30 tests covering retrieval (vector + FTS, price/stock filters, business rules), tool execution and idempotency, fallback grounding (response text actually mentions retrieved products), and the public REST API.

## Trade-offs and design decisions

- **Polling, not WebSockets, for web↔mobile sync.** The Quote view polls `/quotes/active` every 3 seconds. Bounded latency, no socket lifecycle, no auth-token refresh on the wire. Fine for a 2-day take-home; not how I'd build it for live ops.
- **One active draft quote per session, enforced by a partial unique index.** No application-level locking. Adding a second draft is a DB error, not a race.
- **pgvector + FTS hybrid; FTS is also the keyless fallback path.** No separate "no-key" branch in retrieval — the same FTS code serves both unavailable embeddings and a vector miss.
- **FTS uses `websearch_to_tsquery` rewritten to OR semantics.** `plainto_tsquery` and `websearch_to_tsquery` both AND unquoted terms, which makes natural-language queries return zero rows on a small catalog. We round-trip the parsed tsquery through `replace(... ' & ', ' | ')` and `to_tsquery`. Phrase and negation operators are preserved. See `backend/app/retrieval/queries.py` for the full rationale.
- **History replay limited to user/assistant text.** The orchestrator does not replay prior `tool_calls` or `tool` messages on follow-up turns. Maintaining `tool_call_id` referential integrity across persisted messages is brittle and OpenAI rejects malformed history loudly. The model sees the *result* of each turn's tools through the `action` event the user just observed; the next turn starts from text-only context.
- **Embeddings generated only at seed time.** Products created via the UI have `NULL` embeddings and reach users through FTS until the seed script is re-run.
- **Anonymous sessions only.** UUID stored in `localStorage` (web) and `AsyncStorage` (mobile). No auth.
- **Mobile SSE via XHR instead of `react-native-sse`.** `react-native-sse` is GET-only; our endpoint is POST. XHR's `onreadystatechange` (LOADING) reliably exposes `responseText` incrementally on iOS/Android/web. Avoids both a backend GET wrapper and a polyfill stack.

## Pointers

- [`CLAUDE.md`](./CLAUDE.md) — locked architectural decisions, phase tracker, conventions.
- [`AI_USAGE.md`](./AI_USAGE.md) — how AI tooling was used to build this and what was reviewed manually.
- [`KNOWN_LIMITATIONS.md`](./KNOWN_LIMITATIONS.md) — chosen limitations, out-of-scope items, known issues.
- [`mobile/README.md`](./mobile/README.md) — Expo target matrix and CORS notes.
