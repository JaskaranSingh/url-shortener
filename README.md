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
- [x] Core API (create / redirect / delete)
- [x] Analytics (click counts, last-accessed, referrer breakdown)
- [ ] Reliability (rate limiting ❌ / expiry ✅ / structured logging ✅)
- [x] Automated tests (128 passing, 99% coverage as of Phase 8 — grows every phase)
- [x] Setup instructions

**Greenfield core build (Phases 0–8) is complete.** Phase 9 (rate limiting —
the brownfield scenario) and Phase 10 (custom aliases — the ambiguous
scenario) are intentionally deferred for now; see
[`docs/ENGINEERING_SUMMARY.md`](docs/ENGINEERING_SUMMARY.md) for the current
interim state.

Work is tracked as one GitHub issue per phase (Phase 0 → 11, plus a Backlog
milestone for deferred stretch items), each carrying its own task checklist,
FR/NFR traceability, and dependencies. Labels mark which of the three
required engineering scenarios a phase belongs to: `scenario:greenfield`
(core build), `scenario:brownfield` (Phase 9 — rate limiting added to
already-working code), `scenario:ambiguous` (Phase 10 — custom aliases,
deliberately left open in the PRD).

## Documentation

- [`docs/PRD.md`](docs/PRD.md) — functional & non-functional requirements, open questions
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — layers, control flow diagrams, short-code generation strategy, key decisions, scalability path (NFR7)
- [`docs/PLAN.md`](docs/PLAN.md) — phase-by-phase breakdown and GitHub issue/milestone/label structure behind the tracker above
- [`docs/SCHEMA.md`](docs/SCHEMA.md) — `urls`/`clicks` table schema and the design decisions behind it (soft delete, indexing, timestamp format)
- [`docs/DECISIONS.md`](docs/DECISIONS.md) — chronological log of every non-obvious engineering decision, with links to where each was made
- [`docs/ENGINEERING_SUMMARY.md`](docs/ENGINEERING_SUMMARY.md) — plan/rationale, artifacts, validation approach, risks/trade-offs, assumptions, limitations (interim — Phases 0–8)

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
`http://localhost:8000`). Structured JSON request/response/error logs are
written to `urlshortener.log` by default (rotating, 10MB × 5 backups);
override with `URLSHORTENER_LOG_PATH`. Logs never include request or
response bodies.

Run tests:

```bash
pytest --cov=urlshortener --cov-report=term-missing
```
