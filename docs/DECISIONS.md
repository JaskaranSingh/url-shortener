# Engineering Decision Log

A chronological index of every non-obvious engineering decision made across
this project, with a pointer to where it's elaborated. Complements
[`PRD.md`](PRD.md) (requirements), [`ARCHITECTURE.md`](ARCHITECTURE.md)
(system design), and [`SCHEMA.md`](SCHEMA.md) (data model) — this document is
the timeline connecting them to the commits/issues where they were actually
made, including decisions surfaced only once something was actually built
(not all of them were anticipated upfront).

## Requirements & Product

- **No authentication in v1** — keeps the API surface small; direct
  consequence: `DELETE` and `stats` are unscoped. Accepted prototype-scope
  risk. (`PRD.md` §7)
- **SQLite for storage** — embedded, no external dependency to stand up;
  documented trade-off against write-scaling (see NFR7 below). (`PRD.md` §7)
- **302 Found, not 301, for redirects** — a 301 gets cached indefinitely by
  browsers/CDNs, risking a stale destination after a mapping is deleted or
  expires; 302 keeps the server authoritative on every visit. (`PRD.md` FR2)
- **No default expiry, opt-in per URL** — matches common shortener behavior.
  (`PRD.md` FR4)
- **FR5 deletion is soft delete, not hard delete** — preserves an audit
  trail (`SELECT COUNT(*) FROM urls` becomes a meaningful "total codes ever
  generated" metric) and sidesteps a subtle correctness risk where a
  physically deleted row's id could be reused and reassociate old click
  history with an unrelated new code. Decided mid-conversation, before any
  code existed, in response to a direct question about the initial hard-delete
  design. (`PRD.md` FR5, `SCHEMA.md`)
- **FR4 cleanup job dropped entirely** — expiry is fully enforced by a
  read-time check against `expires_at`; a background purge process would be
  a moving part with no behavioral benefit, and would be inconsistent with
  preserving everything for FR5's audit trail. (`PRD.md` FR4)
- **FR6 (custom aliases) deliberately left open** — reserved as the
  ambiguous-requirement scenario rather than resolved during initial
  requirements gathering. (`PRD.md` FR6, §8)

## Architecture

- **Clean Architecture / ports & adapters** — `domain` has zero framework/DB
  imports; `application` depends only on the `UrlRepository` port;
  `adapters` provides the concrete SQLite implementation. (`ARCHITECTURE.md`)
- **`adapters/`, not `infrastructure/`** — reserves `infrastructure/` for
  future IaC/Terraform without a naming clash; names the layer for its
  actual role (port implementations).
- **CSPRNG short codes (`secrets.choice`), not sequential** — with no auth,
  code unguessability is the only access control; sequential/counter-based
  codes are fully enumerable (walking `/1`, `/2`, `/3`...) and leak total
  volume. Base62 alphabet, 7 characters (~3.5 trillion combinations).
- **Bounded retry on collision via a DB unique constraint, not
  SELECT-then-INSERT** — the latter has a TOCTOU race under concurrent
  requests; catching the constraint violation and retrying is correct under
  concurrency, not just in the happy path.
- **Synchronous click recording** — correctness/simplicity over throughput
  at prototype scale; a documented trade-off, not an oversight.
- **Read-through cache and `UrlReader`/`UrlWriter` port split** — both
  designed but deliberately deferred to Backlog (#13, #14), documented, not
  built, since neither solves a load problem this prototype actually has.

## Schema

- **Surrogate `INTEGER` id + a separate named `UNIQUE` index on `code`, not
  `code` as the primary key** — `clicks` holds far more rows than `urls`, so
  its foreign key should be a compact integer, not a 7-character string.
- **No `AUTOINCREMENT`** — its only benefit over plain `INTEGER PRIMARY KEY`
  is preventing id reuse after a delete; moot once soft delete means `urls`
  rows are never physically removed at all.
- **ISO 8601 TEXT timestamps** — SQLite's own recommended convention; parses
  directly into Postgres's native timestamp columns if migrated later.
- **No cascade delete; clicks always preserved** — supports the soft-delete
  decision; there's nothing to cascade from once nothing is ever hard-deleted.
- **No IP address or user-agent columns** — `FR3` doesn't call for them;
  storing IPs would be unrequested PII collection.
- **No `CHECK` constraint on `code` length** — `FR6` (custom aliases) may
  need a different length/character-set rule later; a hard constraint now
  would risk conflicting with a decision not yet made.

## Tech Stack & Tooling

- **Python 3.12, not the system default 3.9.6** — installed via Homebrew
  specifically for this project; 3.9 is too old for the intended stack/typing
  conventions.
- **FastAPI + Pydantic v2, raw `sqlite3` (no ORM)** — two tables and five
  queries doesn't justify SQLAlchemy's overhead, and an ORM's model objects
  create pressure to either leak into `domain`/`application` or duplicate the
  domain entity for no benefit at this scale.
- **ruff for lint + format** (not black/isort/flake8 separately) — one tool,
  one config block.
- **One GitHub issue per phase, not per sub-task** — a finer-grained pass
  would have produced ~39 issues, more bookkeeping overhead than a 2-3 day
  solo build should carry; each phase issue instead carries its own task
  checklist. (`PLAN.md`)
- **Static analysis beyond ruff (SonarQube/SonarLint, bandit)** — explicitly
  skipped for now; no Sonar tooling or Docker available locally, and setting
  up SonarCloud requires an external account this session can't create.
  Revisit if needed.

## Implementation-Time Decisions & Fixes

Surfaced only once each phase was actually built — not all anticipated
upfront, which is itself worth recording:

- **URL validation via an allowlist (http/https only), not the PRD's
  blocklist framing** ("block javascript:, data:, etc.") — an allowlist is
  simpler and strictly safer, since a blocklist can miss scheme variants.
  (Phase 2, #3)
- **`check_same_thread=False`** — a real cross-thread SQLite bug was found
  and fixed during Phase 4: FastAPI runs sync dependencies/endpoints via
  anyio's threadpool, which doesn't guarantee a request's dependency
  resolution and endpoint execution land on the same OS thread. Fixed at the
  root, not worked around in a test. (Phase 4, #5, commit `c6236d4`)
- **ruff `extend-immutable-calls` for `fastapi.Depends`** — a known false
  positive in bugbear's B008 rule; FastAPI's DI pattern, not the
  mutable-default footgun the rule targets. Ruff's own documented fix.
  (Phase 4, #5)
- **`expires_at` normalized to UTC at the API boundary; empty string treated
  as absent** — both found via direct usage/questions after Phase 4 shipped,
  not anticipated upfront. Any timezone offset is accepted from the client,
  but stored as UTC; `""` is treated the same as omitting the field, since
  some clients (HTML forms) serialize "no value" that way. (commits
  `d0e9063`, `a5d9f69`)
- **Deleted checked before expired when both are true** — an arbitrary
  tie-break for a rare case, kept as distinct exceptions so logging can tell
  them apart even though the HTTP response (410) is identical either way.
  (Phase 5, #6)
- **Deleting an already-deleted code returns 410, not 404** — reuses the
  exact "deleted" semantics redirect/stats already use, rather than
  inventing a delete-specific interpretation of the same state; this
  reconsidered an earlier, less-consistent sketch. (Phase 6, #7)
- **Expiry does not block stats; deletion does** — a considered asymmetry,
  not an oversight: expiry only stops the redirect function, while deletion
  reflects the owner's explicit intent to remove/hide something, everywhere.
  (Phase 7, #8)
- **Structured logging built ahead of its sequence position** — a
  middleware-based approach needed to exist *before* more endpoints were
  added for them to get logging automatically; built after Phase 5, before
  Phase 6/7 existed, so those endpoints got request/response/error logging
  for free. (#9, commit `096ff39`)
- **stdlib `logging` + `python-json-logger` + `RotatingFileHandler`**, not
  loguru/structlog — minimal dependency footprint, integrates with uvicorn's
  own logging rather than replacing it. (#9)
- **Logs are metadata-only** (method/path/status/duration/referrer) —
  never request or response bodies, by explicit requirement.
- **Counters periodically logged to the file, no live `/metrics` endpoint**
  — decided against adding an unauthenticated HTTP surface for this
  prototype; revisit if a real observability pipeline is ever wired up.
  (#9, commit `b72dd6c`)

## Deferred / Not Built (explicit, not silent)

- Backlog #13 — read-through cache decorator for redirect lookups.
- Backlog #14 — `UrlReader`/`UrlWriter` port split (interface-level only).
- Static analysis beyond ruff (SonarQube/SonarLint, bandit).
- **Phase 9 (rate limiting, the brownfield scenario)** and **Phase 10
  (custom aliases, the ambiguous scenario)** — intentionally deferred at the
  user's direction as of this document's writing, to be picked up after this
  interim wrap-up pass. See `ENGINEERING_SUMMARY.md` for the current
  project state this implies.
