# Known Limitations

## Architectural Limitations

<!-- Filled in progressively. -->

## Out-of-Scope Features

<!-- Filled in progressively. See CLAUDE.md "Out of Scope" for the locked list. -->

## Known Issues

- Products and knowledge entries created via `POST /products` / `POST /knowledge` are saved with `embedding=NULL`. They are searchable only through the FTS fallback path until the seed script is re-run, which generates embeddings in bulk.
