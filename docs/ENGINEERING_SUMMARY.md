# Engineering Summary

> **Status: interim.** This covers the greenfield core build (Phases 0–8,
> all closed). Phase 9 (rate limiting — the brownfield scenario) and Phase
> 10 (custom aliases — the ambiguous scenario) are intentionally deferred as
> of this writing, at explicit direction, and are not yet reflected below
> except as noted limitations. This document will be revised once they land.

## 1. Objective & Approach

Build a URL shortener prototype demonstrating disciplined, AI-assisted
engineering: a written requirement (`PRD.md`) → an explicit system design
(`ARCHITECTURE.md`, `SCHEMA.md`) → a dependency-ordered task breakdown
(`PLAN.md`) → execution tracked as one GitHub issue per phase, each closed
only with checked tasks, a change-summary comment, and test evidence. The
engineer directed every design decision; AI assistance executed within that
direction — see `DECISIONS.md` for the specific calls made and why.

## 2. Plan & Rationale

Full detail lives in `PLAN.md`; in short: twelve phases (0–11) plus a
backlog milestone, sequenced so that expiry/deletion are folded into the
core build (the redirect flow's `410` branch depends on expiry existing
regardless), and the brownfield/ambiguous scenarios are deliberately
sequenced *after* a working create/redirect endpoint exists — because that
precondition is the entire point of each scenario.

## 3. Scenarios (assignment requirement)

- **Greenfield** — Phases 0–8, the core build. **Done.**
- **Brownfield** — Phase 9, rate limiting added onto the already-working
  `POST /urls` endpoint from Phase 4. **Deferred**, not yet started.
- **Ambiguous** — Phase 10, resolving `FR6` (custom aliases), left
  deliberately open in `PRD.md` §8 since the PRD was first written.
  **Deferred**, not yet started.

## 4. Artifacts Produced

**Documentation**: `PRD.md`, `ARCHITECTURE.md`, `SCHEMA.md`, `PLAN.md`,
`DECISIONS.md`, this summary, `README.md`.

**Code** (`src/urlshortener/`): `domain/` (entities, exceptions, the
`UrlRepository` port), `application/` (`CreateShortUrlService`,
`RedirectService`, `DeleteUrlService`, `StatsService`,
`ShortCodeGenerator`), `adapters/` (`SqliteUrlRepository`, structured JSON
logging, in-memory request counters), `api/` (routers, schemas, DI wiring,
error handlers, logging middleware), `main.py` (composition root).

**Tests** (`tests/`): unit tests against a fake in-memory repository, plus
integration tests against real temp SQLite files and FastAPI's `TestClient`
— 128 passing, 99% coverage (one documented, deliberately-defensive
unreachable branch, not a real gap — see `logging_middleware.py`).

**CI/tooling**: GitHub Actions (lint + format + test on every push),
pre-commit hooks, ruff.

**Tracking**: 14 GitHub issues (one per phase + 2 backlog), 13 milestones,
10 labels (`scenario:greenfield/brownfield/ambiguous`, `area:*`, `backlog`).
Every closed issue carries a change-summary comment with commit links and
test evidence.

## 5. Validation Approach

- **Automated**: unit tests isolate `domain`/`application` logic against a
  fake repository (no I/O); integration tests exercise the real SQLite
  adapter and the full HTTP stack via `TestClient`. Every phase's commit
  message and issue comment records the exact pass count and coverage at
  that point.
- **Manual**: after every phase, the actual server was started with
  `uvicorn` and exercised by hand — not just via automated tests — with
  results pasted into the corresponding issue comment. This caught at least
  one real bug automated tests alone hadn't (see §6).
- **CI gate**: every push runs lint + format check + full test suite;
  nothing was merged to `main` without it passing.
- **Concurrency**: click recording was specifically verified under real
  concurrent load (20 requests across 10 threads through the actual
  per-request dependency chain, not a shared/mocked one) rather than assumed
  safe because it's append-only.

## 6. Risks & Trade-offs

- **No authentication** (`PRD.md` §7) — `DELETE` and `stats` are unscoped.
  Accepted for prototype scope; would need addressing before any real
  deployment.
- **Single-instance SQLite** — write throughput and horizontal scaling are
  both bounded by this; full path to scale documented in `ARCHITECTURE.md`'s
  NFR7 section, not built (correctly, for a validated-scope prototype).
- **A real cross-thread SQLite bug was caught and fixed during Phase 4**
  (`check_same_thread=False`, see `DECISIONS.md`) — evidence the
  test-then-verify discipline caught something automated tests alone,
  written a certain way, would have hidden (the bug only surfaced once a
  test exercised the *real*, non-overridden dependency chain).
- **In-memory rate limiter and counters are per-process** — not an issue at
  single-instance scale; would need a shared store (Redis or similar) before
  any multi-instance deployment. Documented, not yet a live problem.
- **Static analysis is ruff only** — no SonarQube/bandit; explicitly
  deferred rather than silently skipped (no tooling available locally
  without installing Docker or creating an external account).

## 7. Assumptions

- 2–3 day prototype scope, evaluated by a single reviewer running it
  locally — not a production system under real concurrent multi-user load.
- No requirement for user accounts, multi-tenant isolation, or audit-grade
  access control beyond what soft-delete already provides.
- SQLite's single-writer model is acceptable at this scale; no evidence of
  write contention was expected or observed.

## 8. Limitations (as of this interim summary)

- **Phase 9 (rate limiting, brownfield scenario) not yet implemented.**
- **Phase 10 (custom aliases, ambiguous scenario) not yet implemented** —
  `FR6` remains open exactly as `PRD.md` §8 describes.
- Read-through cache and the `UrlReader`/`UrlWriter` port split remain
  backlog-only, documented, not built (Backlog #13, #14).
- No static analysis beyond `ruff` (no SonarQube/bandit).
- No live metrics endpoint — counters are periodically logged to file only,
  a deliberate scope decision, not an oversight.
