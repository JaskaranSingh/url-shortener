# URL Shortener

A URL shortener service built as a prototype demonstrating disciplined,
AI-assisted engineering practice: requirement analysis, task decomposition,
incremental implementation, and validation. This README will be kept in sync
as the project progresses.

## Scope

- **Core API**: create a short URL, redirect a short code to its destination,
  delete a mapping.
- **Analytics**: per-code click counts, last-accessed time, referrer breakdown.
- **Reliability**: rate limiting on creation, optional per-URL expiry.
- **Storage**: SQLite (embedded, file-based).
- **No authentication** in v1 — see the PRD for the reasoning and the
  accepted trade-offs this implies.

Full functional and non-functional requirements, including decisions still
deliberately left open, live in [`docs/PRD.md`](docs/PRD.md). The system
design — layers, control flow, and key decisions — lives in
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

**Stack**: Python 3.12 + FastAPI, SQLite for storage.

## Status

- [x] Requirements (PRD)
- [x] Architecture (layers, control flow, key decisions)
- [x] Implementation plan ([Issues](https://github.com/JaskaranSingh/url-shortener/issues) · [Milestones](https://github.com/JaskaranSingh/url-shortener/milestones))
- [ ] Core API (create ✅ / redirect / delete)
- [ ] Analytics
- [ ] Reliability (rate limiting, expiry)
- [x] Automated tests (69 passing, 100% coverage as of Phase 4 — grows every phase)
- [x] Setup instructions

Work is tracked as one GitHub issue per phase (Phase 0 → 11, plus a Backlog
milestone for deferred stretch items), each carrying its own task checklist,
FR/NFR traceability, and dependencies. Labels mark which of the three
required engineering scenarios a phase belongs to: `scenario:greenfield`
(core build), `scenario:brownfield` (Phase 9 — rate limiting added to
already-working code), `scenario:ambiguous` (Phase 10 — custom aliases,
deliberately left open in the PRD).

## Documentation

- [`docs/PRD.md`](docs/PRD.md) — functional & non-functional requirements, open questions
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — layers, control flow diagrams, short-code generation strategy, key decisions
- [`docs/PLAN.md`](docs/PLAN.md) — phase-by-phase breakdown and GitHub issue/milestone/label structure behind the tracker above
- [`docs/SCHEMA.md`](docs/SCHEMA.md) — `urls`/`clicks` table schema and the design decisions behind it (soft delete, indexing, timestamp format)

## Setup

Requires Python 3.12+.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# run the server
uvicorn urlshortener.main:app --reload
```

Then open http://127.0.0.1:8000/docs for interactive Swagger UI (generated
automatically by FastAPI — no manual integration needed).

By default the app uses a `urlshortener.db` SQLite file in the working
directory; override with the `URLSHORTENER_DB_PATH` env var. `BASE_URL` for
generated short URLs is configurable via `URLSHORTENER_BASE_URL` (defaults to
`http://localhost:8000`).

Run tests:

```bash
pytest --cov=urlshortener --cov-report=term-missing
```
