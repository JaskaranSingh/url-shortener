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
deliberately left open, live in [`docs/PRD.md`](docs/PRD.md).

## Status

- [x] Requirements (PRD)
- [ ] Implementation plan
- [ ] Core API (create / redirect / delete)
- [ ] Analytics
- [ ] Reliability (rate limiting, expiry)
- [ ] Automated tests
- [ ] Setup instructions

## Documentation

- [`docs/PRD.md`](docs/PRD.md) — functional & non-functional requirements, open questions

## Setup

Not yet available — added once the initial implementation lands.
