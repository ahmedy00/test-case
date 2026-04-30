# B2B Sales Assistant

## Project Overview

<!-- Filled in a later phase. -->

AI-powered B2B sales assistant: chat with an LLM that answers grounded product/policy questions and performs real actions on a shared draft quote.

## Architecture

<!-- High-level overview filled in a later phase. Detailed decisions live in CLAUDE.md. -->

See `CLAUDE.md` for the full set of architectural decisions and constraints.

## Tech Stack

- **Backend**: FastAPI, Python 3.11+, SQLAlchemy 2.x, Alembic, Pydantic v2
- **Database**: PostgreSQL 16 with `pgvector`
- **LLM**: OpenAI (`gpt-4o-mini` chat, `text-embedding-3-small` embeddings)
- **Web**: React 18 + Vite + TypeScript
- **Mobile**: Expo (managed workflow) + TypeScript

## Quick Start

Prerequisites: Docker Desktop (with Compose v2), Node 20+ (for mobile only), Expo CLI (only if running the mobile client).

```bash
# 1. Copy the env template and (optionally) add your OpenAI key
cp .env.example .env

# 2. Bring up the stack (db + backend + web)
docker compose up --build

# Services:
#   - Postgres:  localhost:5432
#   - Backend:   http://localhost:8000
#   - Web:       http://localhost:5173

# 3. Mobile (run outside Docker)
cd mobile
npm install
npx expo start
```

Stopping and resetting:

```bash
docker compose down          # stop containers
docker compose down -v       # also wipe the database volume
```

## Environment Variables

All variables and their defaults are documented in `.env.example`. Copy it to `.env` and fill in any secrets (only `OPENAI_API_KEY` is meaningful to set; everything else has working defaults for local Docker).

## Fallback Behavior

<!-- Filled in a later phase. Summary: when OPENAI_API_KEY is missing or the LLM call fails, the assistant returns a retrieval-grounded template response and still emits sources. -->

## Trade-offs and Design Decisions

<!-- Filled in a later phase. -->

## Testing

<!-- Filled in a later phase. -->

## Project Structure

```
.
├── backend/    FastAPI app, SQLAlchemy models, migrations
├── web/        React + Vite admin client
├── mobile/     Expo + React Native client
├── docker-compose.yml
├── .env.example
├── CLAUDE.md   Persistent context for Claude Code
├── AI_USAGE.md
└── KNOWN_LIMITATIONS.md
```
