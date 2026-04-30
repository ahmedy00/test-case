# CLAUDE.md

Persistent context for Claude Code. Read this at the start of every session.

## Project Goal

AI-powered B2B sales assistant. Users chat with an LLM that answers product/policy questions using grounded retrieval (cited sources from the database) and performs real actions like adding products to a draft quote. The system serves a web admin panel and an Expo mobile client; both surfaces share quote state.

## Tech Stack

- **Backend**: FastAPI, Python 3.11+, SQLAlchemy 2.x, Alembic, Pydantic v2
- **Database**: PostgreSQL 16 with `pgvector` extension (image: `pgvector/pgvector:pg16`)
- **LLM**: OpenAI — `gpt-4o-mini` (chat with function calling), `text-embedding-3-small` (embeddings)
- **Web**: React 18 + Vite + TypeScript
- **Mobile**: Expo (managed workflow), TypeScript
- **Local env**: Docker Compose for `db`, `backend`, `web`. Mobile (Expo) runs locally outside Docker.

## Architectural Decisions

1. **Retrieval**: pgvector + OpenAI embeddings as primary; PostgreSQL FTS (`tsvector` + `ts_rank`) as fallback when no API key is present or embeddings fail.
2. **Tool calling**: OpenAI native function calling. Tools: `add_to_quote`, `update_quote_item`, `replace_with_alternative`.
3. **Streaming**: Server-Sent Events (SSE). Event types: `chunk`, `sources`, `action`, `done`, `error`.
4. **Auth**: None. Anonymous session via UUID stored in `localStorage` (web) and `AsyncStorage` (mobile).
5. **Web↔Mobile sync**: Polling every 3 seconds on the quote view. No WebSockets.
6. **Session-Quote relationship**: One active draft quote per chat session.
7. **Duplicate behavior**: Adding the same product again increments quantity on the existing line item.
8. **Domain**: Generic B2B — laptops, monitors, keyboards, accessories. Knowledge entries cover return policy, shipping, warranty, payment terms.
9. **Fallback behavior**: When `OPENAI_API_KEY` is missing or the LLM call fails, return a retrieval-grounded template response. Sources are still emitted via the SSE `sources` event. The system must never fully break.

## Project Structure

```
.
├── README.md
├── CLAUDE.md
├── AI_USAGE.md
├── KNOWN_LIMITATIONS.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── README.md
│   └── app/
│       └── __init__.py
├── web/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       └── main.tsx
└── mobile/
    ├── package.json
    ├── tsconfig.json
    ├── app.json
    └── App.tsx
```

## Code Conventions

### Python
- Type hints on all function signatures and class attributes.
- Pydantic v2 models for request/response I/O.
- SQLAlchemy 2.x style: `Mapped[...]`, `mapped_column(...)`. No legacy `Column = Column(...)` declarations.
- Async endpoints whenever I/O is involved (DB, HTTP, OpenAI).
- Structured logging via the stdlib `logging` module. No `print` in committed code.

### TypeScript
- `strict: true`. No `any`.
- Functional React components. Explicit prop types for every component.

### File Naming
- Python: `snake_case.py`.
- TS/TSX: `camelCase.ts` for modules, `PascalCase.tsx` for components.

## Critical Constraints

- The system **must** work without `OPENAI_API_KEY` (fallback to retrieval-grounded template responses).
- Never commit secrets. `.env` is gitignored; only `.env.example` is tracked.
- Scope is tight — this is a 2-day take-home, not a product. Prefer the simplest option that meets the requirement.

## Out of Scope (do NOT implement)

- Authentication / user accounts
- WebSocket-based live sync
- Multiple concurrent draft quotes per session
- Production deployment configs (k8s, nginx, TLS termination, etc.)
- i18n / l10n

## Phase Tracker

- [x] **Phase 0** — Project scaffolding, Docker Compose, CLAUDE.md
- [x] **Phase 1** — Backend skeleton (FastAPI app, settings, DB connection, health check)
- [x] **Phase 2** — Database models, migrations, seed data
- [ ] **Phase 3** — Retrieval (pgvector + FTS fallback)
- [ ] **Phase 4** — LLM chat with tool calling and SSE streaming
- [ ] **Phase 5** — Web client (chat UI, quote panel)
- [ ] **Phase 6** — Mobile client (Expo)
- [ ] **Phase 7** — Tests, polish, documentation
