# ADR 0002: Match Lifecycle Module

## Status

Accepted

## Context

The match flow owns the highest-risk RankKit rule: ratings move only after a valid confirmation. Logging, confirmation, disputes, rating calculation, participant records, and rating history must change together or the leaderboard can become inconsistent.

## Decision

Keep `RankKitStore` as the app-facing interface, but deepen match behavior behind a dedicated MatchLifecycle module. The module owns match logging, confirmation, dispute, rejection, rating application, and rating-history append ordering.

## Consequences

- Route handlers and future persistence adapters call one stable match interface.
- Match workflow tests keep exercising observable behavior through the store seam.
- Rating update ordering has better locality and can later move behind a transaction without changing callers.
