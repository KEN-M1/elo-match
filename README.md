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
- `infra/` contains the CDK app entrypoint and initial AWS network stack.

## Local Backend

```powershell
pnpm run dev:backend
```

The current MVP demo uses a local JSON snapshot at `backend/data/rankkit-local.json` so demo
leagues survive backend restarts. A PostgreSQL adapter is also available behind a smoke command
while runtime traffic remains on the local snapshot store.

## Local Web

```powershell
pnpm run dev:web
```

The web script writes `apps/web/.env.local` with `NEXT_PUBLIC_API_URL=http://localhost:8002`.
If `.env.local` already exists, the script preserves OAuth values and only updates that API URL.
That avoids stale dev servers that may still be listening on older API ports.

## Google OAuth Setup

The product shell supports Google OAuth through NextAuth. For local OAuth sign-in, create
`apps/web/.env.local` with these values before running `pnpm run dev:web`:

```powershell
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
NEXTAUTH_SECRET=generate-a-local-secret
NEXTAUTH_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8002
```

Configure the Google OAuth client with `http://localhost:3000/api/auth/callback/google` as an
authorized redirect URI. The dev web script preserves OAuth values and refreshes only
`NEXT_PUBLIC_API_URL`.

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

Runtime persistence defaults to the local Store Snapshot for demos, but the backend can select a
Runtime Store Backend with `STORE_BACKEND`.
The backend app now builds its Store adapter, Auth Session, and Route Policy through Runtime
Composition, so production wiring can switch runtime dependencies without rewriting route handlers.

Use local snapshot persistence:

```powershell
STORE_BACKEND=local
```

Use Postgres runtime persistence after applying migrations:

```powershell
STORE_BACKEND=postgres
DATABASE_URL=postgresql+asyncpg://rankkit:rankkit@localhost:5432/rankkit
```

## Production Backend Configuration

Local development keeps permissive defaults so the demo remains easy to run. Production runtime
composition validates the deployment configuration before the API starts.

Set these backend environment variables for a production deploy:

```powershell
ENVIRONMENT=production
STORE_BACKEND=postgres
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/rankkit
JWT_SECRET=replace-with-the-same-32-character-or-longer-secret-used-by-nextauth
ALLOWED_ORIGINS=https://your-web-app.example
```

In production, RankKit refuses to start with the local JSON Store Snapshot or the development
JWT secret. `JWT_SECRET` must match `NEXTAUTH_SECRET` from the web app because NextAuth issues the
bearer token that the FastAPI backend verifies.

## Production Runtime Commands

Start the backend without dev reload after the backend virtual environment has dependencies
installed:

```powershell
pnpm run start:backend
```

The backend binds to `0.0.0.0` and uses `PORT` when set, defaulting to `8002`.

Build and start the web app with Next.js production commands:

```powershell
pnpm run build:web
pnpm run start:web
```

## Backend Container Image

The FastAPI backend has a production Dockerfile that installs runtime dependencies only, copies the
API and Alembic migration files, exposes port `8002`, and starts uvicorn without reload.

Build the backend image from the repository root:

```powershell
docker build -t rankkit-api ./backend
```

Run the container with production environment variables and a reachable Postgres `DATABASE_URL`.
Run Alembic migrations before rolling out a new API image.

## AWS CDK Infrastructure

The `infra/` folder contains the CDK app entrypoint, `RankKitNetworkStack`, `RankKitDatabaseStack`,
and `RankKitComputeStack`. The network stack creates a two-AZ VPC, public and private subnets, one
NAT gateway, and security groups for the ALB, ECS tasks, RDS PostgreSQL, and Redis cache. The
database stack creates a private PostgreSQL 16 RDS instance with generated Secrets Manager
credentials, seven-day backups, deletion protection, and retained storage by default. The compute
stack creates the backend ECR repository and ECS cluster foundation.

From `infra/`, install CDK dependencies and synthesize the stack:

```powershell
pip install -r requirements.txt
cdk synth
```

## CI Verification

GitHub Actions runs `.github/workflows/ci.yml` on pull requests and pushes to `main`.

The Windows verification job installs the backend and web dependencies, runs `pnpm test`, builds
the production web app, and runs the Playwright browser smoke test. The backend image job builds the
backend Docker image and smoke-tests its `/health` endpoint. The CDK synth job installs infra
dependencies and runs `cdk synth`. The Postgres smoke job applies Alembic migrations against a fresh
PostgreSQL service and runs the SQLAlchemy adapter smoke path.

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

## Postgres Adapter Smoke

`pnpm run db:smoke` runs the SQLAlchemy adapter through the local RankKit lifecycle inside a
rolled-back transaction:

- sync owner and opponent users
- create a public league
- create and accept an invite
- log a `PENDING` match
- confirm it as `COMPLETED` and verify `1016.0 / 984.0` ratings
- log a second match, move it to `DISPUTED`, then `REJECTED`
- verify rejected matches do not add rating-history rows
- read the public leaderboard and player rating history

## Demo Path

1. In one PowerShell window, run `pnpm run dev:backend`.
2. In a second PowerShell window, run `pnpm run dev:web`.
3. Open `http://localhost:3000/dashboard` for the product flow.
4. Create or reopen a league, add a member, log a match, confirm or dispute it, and open a player profile.
5. Open `http://localhost:3000/demo` for the one-click happy path.

The `/demo` route uses local user sync instead of Google OAuth so the MVP loop is demoable before the production auth slice.

## Demo Readiness Checklist

Before demoing from a fresh checkout, run:

```powershell
pnpm test
pnpm run db:smoke
pnpm run test:e2e
```

Then start the app:

```powershell
pnpm run dev:backend
pnpm run dev:web
```

Use `http://localhost:3000/demo` for a one-click happy path and `http://localhost:3000/dashboard`
for the full local product flow.

## Reset Local Data

```powershell
pnpm run reset:local
```

Run this only when you want a clean local demo. It deletes `backend/data/rankkit-local.json`.

## Deferred

Mobile, team matches, FFA, tournaments, Glicko-2, Celery, WebSockets, Slack, Discord, SES delivery, and live AWS deployment are deferred until after the local MVP works end to end.
