# RankKit MVP PRD

## Problem Statement

Competitive groups often track wins, losses, and ratings in spreadsheets or chat threads. That makes match history hard to verify, leaderboards easy to dispute, and rating changes difficult to explain. RankKit needs a first release that lets a small real group create a league, invite players, log 1v1 matches, confirm results, and share a trustworthy leaderboard from a local-first full-stack app.

## Solution

RankKit will provide a web MVP backed by FastAPI and PostgreSQL. A league owner signs in with Google, creates a 1v1 Elo league, invites members with copyable links, logs a match, and waits for the opponent to confirm. Ratings update only after confirmation, with an admin dispute path and public read-only leaderboard pages.

## User Stories

1. As a league owner, I want to sign in with Google, so that I can manage leagues without creating another password.
2. As a league owner, I want to create a league with a name, slug, and visibility setting, so that my group has a leaderboard home.
3. As a league owner, I want new leagues to use sensible Elo defaults, so that I do not need to understand rating math before starting.
4. As a league owner, I want to invite players with a link, so that I can onboard people before email delivery exists.
5. As an invited player, I want to accept an invite after signing in, so that I can join the right league.
6. As a league member, I want to see the league leaderboard, so that I know current standings.
7. As a league member, I want to log a 1v1 match result, so that the match can be confirmed.
8. As an opponent, I want to confirm a reported match, so that ratings update only after both sides agree.
9. As an opponent, I want to dispute a reported match, so that incorrect results do not change ratings.
10. As a league admin, I want to resolve disputed matches, so that the league can recover from incorrect reports.
11. As a league member, I want to see rating deltas after confirmation, so that rating movement is explainable.
12. As a player, I want to view my rating history, so that I can understand progress over time.
13. As a visitor, I want to view a public league leaderboard by slug, so that shared standings do not require auth.
14. As a developer, I want generated TypeScript types from OpenAPI, so that web and backend contracts stay aligned.
15. As a developer, I want tests at public seams, so that refactors do not break behavior.
16. As a future maintainer, I want domain terms recorded in context and ADRs, so that architecture reviews use stable language.

## Implementation Decisions

- Build the MVP as a monorepo with a FastAPI backend, Next.js web app, generated TypeScript package, and CDK infra skeleton.
- Keep the schema future-ready for multiple formats, but expose only 1v1 Elo behavior in the MVP.
- Use Google OAuth on the web and JWT validation at the backend seam.
- Use copyable invite tokens for MVP; defer SES email sending.
- Rating defaults are initial rating `1000`, K-factor `32`, rating floor `100`, and win/loss outcomes only.
- Matches update ratings only after opponent confirmation.
- Admins can resolve disputes, but automatic rollback and advanced moderation are deferred.
- Public leaderboards use `/l/[slug]` and an `is_public` flag.
- WebSocket updates, Celery jobs, Slack/Discord, mobile, tournaments, team formats, and FFA are deferred.

## Testing Decisions

- Use TDD per vertical slice: one failing behavior test, minimal implementation, then refactor when green.
- Unit-test pure Elo behavior through the rating module interface.
- Test match lifecycle through the API seam rather than through private helpers.
- Test public leaderboard behavior through a read-only route.
- Mock only external seams such as Google auth, email delivery, time/randomness, and external APIs.
- Add a browser smoke test once the web app can run locally.

## Out of Scope

Mobile, team matches, FFA, tournaments, Glicko-2, Celery, SQS, Redis, WebSockets, Slack, Discord, SES delivery, live AWS deployment, and production observability are outside the first MVP.

## Further Notes

The first done milestone is a fresh local end-to-end demo. Issue tracker setup is not present, so this PRD is stored locally and should be published later with the `ready-for-agent` label.
