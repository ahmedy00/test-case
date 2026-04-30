# Backend

FastAPI service for the B2B sales assistant. See the [root README](../README.md) for setup and the [project context](../CLAUDE.md) for architectural decisions.

## Run tests

Tests hit a live database (no test-DB isolation in this phase), so the `db` service must be up:

```bash
docker compose up -d db
docker compose run --rm backend pytest
```
