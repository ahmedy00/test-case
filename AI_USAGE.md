# AI Usage

Account of how AI tooling was used to build this project. Written from my (Ahmet's) perspective, with no marketing language.

## Tools used

- **Claude (Anthropic)** for high-level planning, prompt drafting, architectural reasoning, and reviewing diffs across all eight phases.
- **Claude Code** as the implementation agent — it ran each phase end-to-end against prompts I authored, executing real tool calls (Read, Edit, Bash, etc.) inside the project working tree.
- No GitHub Copilot, no ChatGPT, no Cursor.

## Where AI was used

I worked the project as a phase-by-phase sequence. Each phase had a written brief (visible in the conversation history); the agent implemented the brief, I reviewed and corrected.

- **Phase 0 — scaffolding.** Docker Compose, base FastAPI app, package.json files, CLAUDE.md skeleton, repo hygiene (.gitignore, .env.example). Almost entirely AI-written; I checked secrets discipline and the directory layout.
- **Phase 1 — backend skeleton.** Settings module, structured logging, DB connection, health route. AI proposed the layout; I confirmed Pydantic v2 and SQLAlchemy 2.x style would be enforced project-wide.
- **Phase 2 — schema and seed.** ORM models for `chat_sessions`, `chat_messages`, `products`, `knowledge_entries`, `quotes`, `quote_items`. The Alembic migration was AI-authored; I read every CHECK constraint, FK action (CASCADE vs RESTRICT), and index definition before applying it. Seed data is hand-tuned to make the rubric's business rules testable (one OOS laptop, multiple price tiers, knowledge entries spanning return/shipping/warranty/payment).
- **Phase 3 — retrieval.** pgvector cosine + FTS `tsvector` fallback. AI proposed the dual-path service; I made specific calls about safe SQL binding (string literal cast to `vector` rather than relying on the psycopg adapter; `CAST(:max_price AS NUMERIC)` to fix `AmbiguousParameter` from psycopg).
- **Phase 4 — chat orchestrator.** Tool calling with OpenAI's native function-calling protocol; SSE streaming; templated fallback path. The most AI-heavy phase. I reviewed the tool-loop logic in detail because that's where bugs hide (loop cap enforcement, ordering of tool messages in history, tool errors not aborting the stream).
- **Phase 5 — web client.** React + Vite. State machine for the chat hook (idle/streaming/done/error), 3s polling for the quote view, SSE parser. AI wrote nearly all the UI; I shaped the state machine and split the SSE parser out as a generator.
- **Phase 6 — mobile client.** Expo with TypeScript. Different SSE strategy (XHR + `responseText`-slicing) because `fetch().body` is not reliable on RN. Same component vocabulary as web.
- **Phase 7 — tests, polish, docs.** This file, the README, the FTS fix (see "Suggestions rejected"), and three additional tests targeting the rubric's business-rules and grounding requirements.

## Suggestions accepted

- **HNSW index on `products.embedding` instead of IVFFlat.** Our pgvector image (≥ 0.5) supports HNSW; recall is meaningfully better at small scale and we don't have a write throughput concern that would push back the other way.
- **`INSERT ... ON CONFLICT (quote_id, product_id) DO UPDATE SET quantity = quote_items.quantity + EXCLUDED.quantity`** for `add_to_quote`. Single statement, atomic, no read-modify-write race. Much better than the Python-side "fetch, decide, insert/update" pattern the agent first sketched.
- **Partial unique index `(session_id) WHERE status = 'draft'`** on `quotes`. Enforces "one active draft per session" at the DB layer rather than as an application invariant. Two parallel requests can't both create a draft for the same session — Postgres will reject the second.
- **XHR + `onreadystatechange` for SSE on React Native.** Avoids `react-native-sse` (GET-only, would force a backend change) and avoids polyfilling `fetch`'s ReadableStream support per platform. Two callbacks (`LOADING` for incremental `responseText`, `DONE` for final flush) plus a 30-LOC parser.
- **Surfacing the final assistant message + tool-action transcript in the `done` event.** The web/mobile UI render the assistant message and per-turn action chips from a single state object that the SSE stream pushes; no second round trip to fetch chat history.

## Suggestions rejected

- **`ON CONFLICT ON CONSTRAINT uq_active_draft_quote`** for the partial unique index on `quotes`. Rejected: Postgres does not allow `ON CONFLICT ON CONSTRAINT` to reference partial unique indexes — only full constraints. Switched to inference form `ON CONFLICT (session_id) WHERE status = 'draft'`.
- **Replaying full conversation history (including `tool_calls` rows) on every LLM turn.** Rejected: `tool_call_id` referential integrity across rehydrated history is fragile — OpenAI rejects malformed sequences with a hard error, and the persistence layer would need to model the message graph carefully. For a 2-day project the cost of getting it wrong outweighs the benefit. Limited replay to user/assistant text only.
- **`plainto_tsquery` for FTS.** Rejected on review of Phase 5 verification output: a query like *"What laptops do you offer?"* tokenized to `'laptop' & 'offer'`, requiring every stem to match — and no seeded product description contains the word "offer", so FTS returned zero rows on natural-language input. **Also rejected `websearch_to_tsquery`** as a drop-in replacement: it ANDs unquoted terms too (Google-style). Settled on roundtripping `websearch_to_tsquery`'s output through `replace(... ' & ', ' | ')` + `to_tsquery`, which preserves the safe parser's sanitization, preserves negation and phrase operators, and relaxes only the AND-of-everything default. Verified empty stopword inputs round-trip to the empty tsquery (no rows, no error).
- **`react-router-dom` for the web client.** Rejected: a 60-line `useState`-driven view switcher handles four pages without an extra dependency. Routing is genuinely useful when you have shareable URLs and history; this client has neither.
- **`@react-navigation` on mobile.** Same rationale — two screens, a `useState<"chat"|"quote">`, done.

## What I checked manually

- **The Alembic migration.** Read every CHECK constraint, FK action, partial-index predicate, and trigger before applying it. Specifically verified the `tsvector` triggers fire on UPDATE-of relevant columns and that the unique partial index works as intended (created a draft, tried inserting a second — rejected as expected).
- **The orchestrator's tool loop.** Walked through the loop cap, the order of `assistant`/`tool` messages appended to history, and the behavior when a tool handler raises — that case must not abort the SSE stream; the action event should report `status: "error"` and the next iteration should continue.
- **The SSE parser on both web and mobile.** Boundary handling for events split across reads is a classic source of off-by-one bugs. Verified by hand against synthetic inputs that split mid-event and at every position around `\n\n`.
- **The fallback grounding test.** Wrote the assertion myself rather than letting the agent generate one — the test must prove the assistant text actually mentions a retrieved SKU/name, not just that it produces text. Generic "I'm sorry" responses must fail.
- **`.env.example`, `.gitignore`, and what gets staged.** Secrets discipline is non-negotiable. Confirmed `.env` is gitignored, that `OPENAI_API_KEY=` is empty in `.env.example`, and ran `git status` after each phase to make sure nothing surprising was staged.
- **The seed script's idempotency.** Re-ran `python -m app.seed.seed` multiple times; verified `ON CONFLICT (sku) DO UPDATE` and `ON CONFLICT (title) DO UPDATE` paths preserve embeddings and don't double-insert.
