# ADR 0001: Local-First 1v1 Elo MVP

## Status

Accepted

## Context

The source prompt describes a broad production system with mobile, multiple match formats, AWS infrastructure, background jobs, and integrations. The first implementation needs to produce real user value without turning infrastructure setup into the project.

## Decision

Build a local-first MVP around web, FastAPI, PostgreSQL, and 1v1 Elo leagues. Keep the schema future-ready, but defer mobile, team/FFA/tournament formats, live AWS deployment, Celery, WebSockets, Slack/Discord, and SES delivery.

## Consequences

- The first milestone is demoable locally and can be tested end to end.
- Core product decisions around league membership, match confirmation, rating updates, and public leaderboards are settled early.
- Production deployment and integrations remain explicit follow-up slices rather than hidden requirements.
