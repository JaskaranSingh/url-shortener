# PRD: URL Shortener Service

## 1. Overview

Build a URL shortener service that accepts long URLs, returns short codes, redirects
visitors from short codes to their original destination, and tracks usage analytics.
Delivered as a prototype demonstrating core API design, reliability practices, and
engineering judgment — not a hardened multi-region production system.

## 2. Goals

- Reliably shorten a long URL into a short, unique code.
- Redirect a short code to its original URL with correct HTTP semantics.
- Capture usage analytics per short code (click counts, timestamps, referrer).
- Demonstrate at least one reliability control (rate limiting) and safe expiry handling.

## 3. Non-Goals

- No distributed/horizontally-scaled deployment — single-instance prototype.
- No user accounts or auth system in v1 (decided — see Section 7).
- No frontend/UI — API-first service only.

## 4. Users & Use Cases

| Actor | Use Case |
|---|---|
| API consumer | Submits a long URL, receives a short code + short URL |
| End user | Clicks/visits a short URL, gets redirected to the original destination |
| API consumer / owner | Retrieves analytics for a short code (clicks, last accessed) |

## 5. Functional Requirements

**FR1 — Create Short URL**
- `POST /urls` accepts a long URL, returns a generated short code and full short URL.
- Reject malformed URLs (missing scheme/host) with `400`.

**FR2 — Redirect**
- `GET /{code}` resolves the code and issues an HTTP redirect to the original URL.
- Returns `404` for unknown codes, `410 Gone` for expired codes.
- Uses `302 Found` (decided). A `301` is cache-friendly but browsers/CDNs cache it
  indefinitely, which risks serving a stale destination after a mapping is deleted or
  expires; `302` keeps the server authoritative on every visit.

**FR3 — Analytics**
- Each successful redirect is recorded (timestamp, referrer if present).
- `GET /urls/{code}/stats` returns total clicks, last-accessed time, and a referrer
  breakdown.

**FR4 — Expiry**
- A short URL may have an optional expiry, set at creation time. Default is **no
  expiry** (decided) — matches common shortener behavior (e.g. bit.ly) and keeps the
  default case simple; expiry is opt-in per URL, not a global TTL.
- Expired codes resolve to `410` and are eligible for periodic cleanup.

**FR5 — Deletion**
- `DELETE /urls/{code}` removes a mapping. Since v1 has no auth, this is **unscoped**
  — anyone holding a valid code can delete it. Accepted as a prototype-scope risk (see
  Section 7); revisit if auth is ever added.

**FR6 — Custom Aliases (OPEN — intentionally unresolved)**
- Ability to request a custom short code instead of an auto-generated one.
- Deliberately left unspecified pending: collision handling with existing/auto-generated
  codes, allowed character set/length, and whether it requires ownership/auth.
- This gap is intentional — it is the requirement used to demonstrate ambiguity
  resolution as a separate, dated engineering decision rather than being pre-resolved here.

## 6. Non-Functional Requirements

**NFR1 — Reliability**: Redirect (read) path must degrade gracefully under load; creation
endpoint is rate-limited to prevent abuse.

**NFR2 — Performance**: Redirect lookup is the hot path and should stay low-latency
(prototype target, not a contractual SLA).

**NFR3 — Data Integrity**: Short-code generation must be collision-free — no two active
codes resolve to different destination URLs.

**NFR4 — Security**:
- Validate destination URL scheme to prevent open-redirect abuse (block `javascript:`,
  `data:`, etc.).
- Sanitize all inputs.
- Rate-limit creation and lookup to reduce code-enumeration/brute-force risk.

**NFR5 — Observability**: Structured logging for create/redirect/error events; basic
counters for request volume, error rate, and redirect latency.

**NFR6 — Maintainability**: Layered structure (API layer / business logic / storage)
so storage or generation strategy can change without touching handlers; core flows
covered by automated tests.

**NFR7 — Scalability (documented, not necessarily built)**: Note a credible path to
scale (stateless API instances + external managed DB/cache) even though the prototype
uses SQLite, an embedded, single-file store (decided — see Section 7).

## 7. Constraints & Assumptions

- Prototype scope, built over 2-3 days.
- **Storage: SQLite** (decided) — embedded, file-based, durable across restarts, no
  external dependency to stand up. Trade-off: single-writer semantics are fine at
  prototype load but would need to migrate to a managed DB (e.g. Postgres) to scale
  writes horizontally — noted in NFR7.
- Single-instance deployment assumed.
- **No authentication in v1** (decided) — keeps the API surface small and matches the
  non-goal in Section 3. Direct consequence: `DELETE` (FR5) and `stats` (FR3) are
  unscoped/unauthenticated; accepted as a prototype-scope risk, not something to harden
  further here.

## 8. Open Questions (deliberately unresolved here)

- FR6: custom alias behavior (collisions, constraints, ownership) — this is the one
  requirement intentionally left open, to be resolved as its own dated engineering
  decision (the ambiguous-requirement scenario) rather than guessed here.

## 9. Success Criteria

- A submitted long URL can be shortened and successfully redirects end-to-end.
- Analytics accurately reflect real click activity for a given code.
- Rate limiting demonstrably blocks abusive request patterns in a test.
- Core flows (create, redirect, stats, expiry) are covered by automated tests.
