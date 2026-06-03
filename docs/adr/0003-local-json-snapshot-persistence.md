# ADR 0003: Local JSON Snapshot Persistence

## Status

Accepted

## Context

The local-first MVP needs durable demo data, but the architecture review found that JSON serialization, datetime parsing, and rating-result hydration were reducing locality inside `RankKitStore`.

## Decision

Deepen local persistence as a local JSON Store Snapshot module only. Keep `RankKitStore` as the app-facing interface and move Store Snapshot JSON load/save behavior into `backend/app/local_snapshot.py`.

Do not introduce a Postgres adapter seam in this pass. Postgres remains a later persistence decision.

## Consequences

- Store Snapshot bugs now concentrate in one module.
- The local MVP keeps the same `RankKitStore()` and `RankKitStore(path)` interface.
- Future Postgres work can revisit the persistence seam with a fresh decision once the adapter is real.
