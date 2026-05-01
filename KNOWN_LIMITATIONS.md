# Known Limitations

What the system intentionally does not do, and what is left rough. Stated honestly so a reviewer doesn't have to find these on their own.

## Architectural limitations (chosen, not bugs)

- **No authentication.** Anonymous sessions identified by a UUID stored in `localStorage` (web) and `AsyncStorage` (mobile). Anyone with the UUID can read or mutate that session's draft quote.
- **Web↔mobile sync via 3-second polling, not WebSockets.** Latency is bounded by the polling interval. Acceptable for a draft-quote workflow; not how I'd do live collaboration.
- **One active draft quote per chat session.** Enforced at the DB layer by a partial unique index. There is no UI or API path to juggle multiple in-progress quotes per session.
- **Embeddings generated only at seed time.** Products and knowledge entries created via the REST API have `NULL` embeddings and reach users through FTS until the seed script is re-run. There is no on-write embedding job — that's a deliberate scope cut, not an oversight.
- **LLM history replay is text-only.** Prior `tool_calls` and `tool` messages are not replayed on follow-up turns. The model sees the *result* of each turn's tools through the action SSE event the user just observed; the next turn starts from text-only context. A multi-turn negotiation that requires the model to reason about its earlier tool *invocations* (not just outcomes) won't have access to that detail.
- **Fallback path emits no `action` events by design.** When `OPENAI_API_KEY` is missing or the LLM call fails, the assistant returns a templated, retrieval-grounded response, but it does not perform tool calls. Performing actions without an LLM would require pattern-matching the user's intent — brittle and not worth the complexity. The case requires *at least one real action*; the LLM path provides it.

## Out-of-scope features

- Multi-tenancy, organizations, role-based access.
- Quote finalization, PDF export, sending quotes to customers.
- Editing or deleting products and knowledge entries (create + read only — `PATCH`/`DELETE` not implemented).
- Production deployment configs (TLS termination, k8s, observability stack, secrets management).
- i18n / l10n. Backend prompts and frontend strings are English-only.
- Analytics, audit logs, rate limiting.
- Authorization for the OpenAI key (the key is read directly from `.env`; no per-tenant secret scoping).

## Known issues

- **FTS uses the `english` text-search config.** Non-English queries will be tokenized poorly and may return weak results. Domain-specific stemming (e.g. "GPU" / "graphics processing unit" being treated as related) would also help; we do not configure a custom dictionary.
- **FTS query rewriting is a workaround, not a search-quality answer.** We rewrite `websearch_to_tsquery`'s `&` connectives to `|` so chatty queries don't return zero rows. This trades precision for recall on a small catalog. With a larger catalog, an actual hybrid scorer (BM25 + dense + reciprocal rank fusion) would be a better answer than relaxing connectives.
- **Mobile streaming was verified on the Expo web target only.** The XHR-based SSE consumer is platform-agnostic by design, but iOS Simulator / Android Emulator / physical-device verification was not performed in this environment. The codepaths that differ from web (`AsyncStorage` reads, `KeyboardAvoidingView`, `RefreshControl`, `Platform.select` for fonts) all type-check and bundle clean for the web target.
- **Products and knowledge entries created via the REST API are FTS-only.** They appear in chat retrieval through the FTS path but never the vector path until the seed script is re-run.
- **No retry / circuit-breaker on OpenAI.** A transient OpenAI failure during a turn pivots that turn to the fallback (this is correct, by design — the system stays up). There is no automatic retry, no per-org rate limiting, no quota tracking.
- **`docker compose down -v` wipes the seed.** Without volume backups, every fresh stack needs `alembic upgrade head` + `python -m app.seed.seed` again. Documented in the README's quick start.
- **Tests exercise the seeded development DB.** They are read-only against shared tables and CASCADE-clean their own rows on teardown via the `fresh_session_id` fixture. Acceptable for a 2-day take-home; not isolated enough for parallel CI without a per-job DB.
