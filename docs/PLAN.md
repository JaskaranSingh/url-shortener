# Phase-by-Phase Plan & GitHub Issues — URL Shortener

> Status: executed. This is the planning artifact that produced the live
> [Issues](https://github.com/JaskaranSingh/url-shortener/issues) and
> [Milestones](https://github.com/JaskaranSingh/url-shortener/milestones) —
> kept here for traceability of the decomposition reasoning. For current
> progress, the GitHub tracker is the source of truth, not this file.

## Context

`docs/PRD.md` and `docs/ARCHITECTURE.md` are complete and locked (repo:
https://github.com/JaskaranSingh/url-shortener, currently doc-only, clean
working tree, 4 commits). What's missing is the bridge from those documents to
actual execution: a dependency-ordered task breakdown, and a GitHub issue
structure a reviewer can read to see decomposition, sequencing, and
traceability — directly satisfying the assignment's "Task Decomposition" and
"Controlled Oversight" requirements.

Two decisions this plan locks in that weren't settled yet:
- **Dev tooling**: pytest (already assumed by `ARCHITECTURE.md`'s test-layer
  split), **ruff** for both linting and formatting (one tool/config instead of
  black+isort+flake8 separately), pre-commit hooks, and a minimal GitHub
  Actions workflow (lint + test) — all set up in Phase 0. The CI workflow
  matters specifically because it's the regression gate the brownfield phase
  (rate limiting) leans on.
- **Issue granularity**: **one issue per phase** (not one issue per
  sub-task). A finer-grained pass would produce ~39 issues, which is more
  bookkeeping overhead than a 2-3 day solo build should carry. Each phase issue
  instead carries an internal checklist of its sub-tasks, FR/NFR traceability,
  and explicit "Depends on" links — same decomposition visible, far less
  process overhead.

Expiry (FR4) and deletion (FR5) are folded into the core build (not deferred),
since the redirect flow's `410` branch depends on expiry existing, and
deletion is basic CRUD. Rate limiting (Phase 9) and custom aliases (Phase 10)
are reserved as the brownfield and ambiguous-requirement scenarios
respectively — both are sequenced after a working create/redirect endpoint
already exists, since that precondition is the whole point of each scenario.

## Phase Breakdown (each phase = one GitHub issue = one milestone)

**Phase 0 — Project Scaffolding & Dev Tooling** *(scenario:greenfield, area:tooling)*
`src/urlshortener/{domain,application,adapters,api}` package skeleton per
`ARCHITECTURE.md`; `pyproject.toml` (fastapi, uvicorn, pydantic, pytest, ruff);
`tests/{unit,integration}` skeleton; ruff config; pre-commit config; GitHub
Actions workflow (lint + test). Depends on: nothing.

**Phase 1 — Domain Layer** *(scenario:greenfield, area:domain)*
`ShortUrl` entity; domain exceptions (`UrlNotFoundError`, `UrlExpiredError`,
`CollisionError`, `InvalidUrlError`); `UrlRepository` port (single combined
read+write interface — read/write split is Backlog, not core). Depends on:
Phase 0.

**Phase 2 — Application: Code Generation + Create Service** *(scenario:greenfield, area:application)*
`ShortCodeGenerator` (`secrets.choice`, base62, 7 chars) + unit tests proving
CSPRNG usage; `CreateShortUrlService` (URL-scheme validation, bounded retry on
collision); fake in-memory repository reused by all later unit tests. Depends
on: Phase 1.

**Phase 3 — Adapters: SQLite Repository & Schema** *(scenario:greenfield, area:adapters)*
`urls` + `clicks` table schema (clicks table now, even though Stats lands
later, since FR3 needs per-referrer breakdown not just a counter);
`SqliteUrlRepository` (save w/ unique constraint + collision surfacing,
get_by_code, delete, record_click, get_stats); integration tests against a
temp SQLite file. Depends on: Phase 1, Phase 2.

**Phase 4 — API: Create Endpoint** *(scenario:greenfield, area:api)*
FastAPI app skeleton + `main.py` composition root (DI via `Depends`);
`POST /urls` schemas + router, including optional `expires_at`;
`api/error_handlers.py` (400 mapping); integration tests (happy path +
malformed URL). Depends on: Phase 2, Phase 3. **This is the point a working
create endpoint exists — the brownfield precondition.**

**Phase 5 — API: Redirect + Expiry** *(scenario:greenfield, area:api)*
`RedirectService` (get_by_code → 404 if missing → 410 if expired → else
synchronous `record_click` → 302); `GET /{code}` router + error_handlers
additions; unit tests (fake repo) + integration tests (302/404/410). Depends
on: Phase 3, Phase 4.

**Phase 6 — API: Deletion** *(scenario:greenfield, area:api)*
`DeleteUrlService`; `DELETE /urls/{code}` (204/404); tests. Depends on: Phase
4, Phase 5.

**Phase 7 — API: Analytics/Stats** *(scenario:greenfield, area:api)*
`StatsService` (clicks aggregation, referrer breakdown); `GET
/urls/{code}/stats` + schema; tests. Depends on: Phase 3 (hard — clicks table
must exist); Phase 5 (soft — real click data needs redirect wired first).

**Phase 8 — Observability** *(scenario:greenfield, area:adapters)*
`adapters/logging.py` structured (JSON) logger; wired into
create/redirect/delete/error paths; basic counters (request volume, error
rate, redirect latency). Depends on: Phase 4, 5, 6.

**Phase 9 — Reliability: Rate Limiting [BROWNFIELD SCENARIO]** *(scenario:brownfield, area:adapters)*
Design note (token bucket, per-IP, in-memory, explicit non-distributed-safe
caveat); `adapters/rate_limiter.py`; wired into `POST /urls` as a FastAPI
dependency **without regressing existing create tests**; tests for 429 +
full-suite regression pass. Depends on: Phase 4 (working create endpoint —
the literal brownfield precondition: modifying already-merged, working code),
Phase 8 (reuses the logging adapter). Issue body must explicitly narrate that
this modifies existing code, for reviewer legibility.

**Phase 10 — Custom Aliases (FR6) [AMBIGUOUS-REQUIREMENT SCENARIO]** *(scenario:ambiguous, area:application)*
In order: (1) a dated decision doc (`docs/decisions/YYYY-MM-DD-custom-aliases.md`)
resolving collision handling, allowed character set/length, and ownership
stance — written *before* any code, explicitly resolving PRD §8; (2) extend
`CreateShortUrlService` with optional `custom_code`, skipping
`ShortCodeGenerator` when present, 409 on collision; (3) extend `POST /urls`
schema/router; (4) tests (happy path, 409 collision, 400 invalid format).
Depends on: Phase 4. Deliberately sequenced last among feature phases —
embodies the PRD's own framing that this gets resolved later, not guessed
early.

**Phase 11 — Documentation & Wrap-up** *(no scenario label)*
README update (setup/run instructions, status checklist fully checked); NFR7
scalability write-up (documented path only, not built); final decision-log
indexing every dated decision made across phases with issue links; final
Engineering Summary doc (plan/rationale, artifacts, risks/trade-offs/
validation, assumptions, limitations — the assignment's own required
deliverable). Depends on: Phases 4–10 substantially complete.

**Backlog (stretch, separate milestone, not part of core sequence)**
- Read-through cache decorator around the read port, explicit invalidation on
  delete/expiry (not TTL-only). Depends on: Phase 5.
- Split `UrlRepository` into `UrlReader`/`UrlWriter` ports (interface-level
  only). Depends on: Phase 3.

## GitHub Structure

**Milestones** (13 total, one per phase + Backlog), created in phase order so
milestone IDs sort the same way:
`Phase 0` … `Phase 11`, `Backlog`.

**Labels:**
- Scenario (the three the assignment requires): `scenario:greenfield`,
  `scenario:brownfield`, `scenario:ambiguous`. Phase 11 gets none (or
  greenfield, since wrap-up is still core work — use none to avoid diluting
  the signal).
- Area (mirrors `ARCHITECTURE.md` layers): `area:domain`, `area:application`,
  `area:adapters`, `area:api`, `area:tooling`, `area:docs`.
- `backlog` for the two deferred-enhancement issues.
- No per-FR/NFR labels — traceability lives as a "Satisfies: FRx, NFRy" line
  in each issue body instead; 13 extra labels would be noise at this scale.

**Each issue body** follows this template:
```
## Delivers
<what this phase produces>

## Satisfies
FRx, NFRy (from docs/PRD.md)

## Depends on
#<issue-number> (or "nothing — first phase")

## Tasks
- [ ] sub-task 1
- [ ] sub-task 2
...
```

**Creation order**: create issues in phase order (0 → 11, then the 2 backlog
issues) so issue numbers ascend with dependency order, making "Depends on
#N" always point backward to an already-visible lower number.

## Execution Steps

1. Create the 13 milestones via `gh api repos/JaskaranSingh/url-shortener/milestones -f title=...` (no native `gh milestone create` command exists).
2. Create the 8 labels via `gh label create`.
3. Create the 14 issues via `gh issue create --title ... --body ... --label ... --milestone ...`, in phase order, filling in real issue numbers for "Depends on" as each subsequent issue is created.
4. Print the final `gh issue list --all` output for a sanity check that all 14 issues, labels, and milestones landed correctly.

## Verification

- `gh issue list --milestone "Phase 0"` (and so on per phase) returns exactly
  one issue each.
- `gh label list` shows all 8 labels.
- Spot-check 2–3 issue bodies via `gh issue view <n>` to confirm the
  Delivers/Satisfies/Depends on/Tasks template rendered correctly and
  "Depends on" numbers are correct (not placeholder text).
- Confirm milestone order in the repo's Issues tab matches phase order.
