# RankKit

RankKit is a local-first competitive rating MVP for small groups. The first slice supports Google-authenticated web users, 1v1 Elo leagues, invite links, opponent-confirmed matches, admin dispute resolution, rating history, and public read-only leaderboards.

## Current Scope

The repository implements the PRD-first workflow requested for RankKit:

- `docs/PRD.md` captures the product requirements.
- `docs/issues/` breaks the work into tracer-bullet issues.
- `CONTEXT.md` records domain language for tests and architecture review.
- `docs/adr/` records durable architecture decisions.
- `backend/` contains the FastAPI app shape and pure rating module.
- `apps/web/` contains the Next.js app shell and typed client surface.
- `infra/` contains CDK placeholders for later AWS work.

## Local Backend

```powershell
pnpm run dev:backend
```

The current MVP demo uses a local JSON snapshot at `backend/data/rankkit-local.json` so demo
leagues survive backend restarts. PostgreSQL is documented for the planned production persistence
slice.

## Local Web

```powershell
pnpm run dev:web
```

The web script writes `apps/web/.env.local` with `NEXT_PUBLIC_API_URL=http://localhost:8002`.
If `.env.local` already exists, the script preserves OAuth values and only updates that API URL.
That avoids stale dev servers that may still be listening on older API ports.

## Tests

```powershell
pnpm test
```

When dependencies are installed, use `pytest` for the full backend suite.

Run the browser demo smoke test with:

```powershell
pnpm run test:e2e
```

If Playwright browsers are missing, install Chromium once:

```powershell
pnpm exec playwright install chromium
```

## Database Migrations

Runtime persistence still uses the local Store Snapshot for the MVP, but the future Postgres schema
is tracked with Alembic.

Start a local Postgres container:

```powershell
pnpm run dev:db
```

Render the migration SQL without a running database:

```powershell
pnpm run db:sql
```

Apply migrations to a configured Postgres database:

```powershell
pnpm run db:migrate
```

Verify the local database migration version and tables:

```powershell
pnpm run db:verify
```

Run the backend SQLAlchemy smoke check against the migrated database:

```powershell
pnpm run db:smoke
```

## Demo Path

1. In one PowerShell window, run `pnpm run dev:backend`.
2. In a second PowerShell window, run `pnpm run dev:web`.
3. Open `http://localhost:3000/dashboard` for the product flow.
4. Create or reopen a league, add a member, log a match, confirm or dispute it, and open a player profile.
5. Open `http://localhost:3000/demo` for the one-click happy path.

The `/demo` route uses local user sync instead of Google OAuth so the MVP loop is demoable before the production auth slice.

## Reset Local Data

```powershell
pnpm run reset:local
```

Run this only when you want a clean local demo. It deletes `backend/data/rankkit-local.json`.

## Deferred

Mobile, team matches, FFA, tournaments, Glicko-2, Celery, WebSockets, Slack, Discord, SES delivery, and live AWS deployment are deferred until after the local MVP works end to end.
