# RankKit — Agent System Prompt (FastAPI + AWS)

## Project Overview

You are building **RankKit**, a full-stack, cross-platform competitive rating platform. It supports
multiple match formats (1v1, team vs team, free-for-all, and tournaments) using Elo and Glicko-2
rating systems. The platform runs on web (Next.js) and mobile (Expo/React Native), backed by a
Python FastAPI REST API and PostgreSQL database, fully deployed on AWS.

This is a production-quality project intended to demonstrate mid-level full-stack engineering
skills. Every architectural decision should reflect real-world engineering trade-offs that can be
discussed in a technical interview.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Monorepo (JS) | Turborepo + pnpm workspaces |
| Web app | Next.js 14 (App Router) + TypeScript + Tailwind CSS + shadcn/ui |
| Mobile app | Expo SDK 52 + React Native + NativeWind |
| Backend API | Python 3.12 + FastAPI + Uvicorn |
| Data validation (backend) | Pydantic v2 |
| Database ORM | SQLAlchemy 2.0 (async) |
| Database migrations | Alembic |
| Database | PostgreSQL 16 (AWS RDS) |
| Auth (web) | Auth.js v5 with Google OAuth — issues JWTs validated by FastAPI |
| Auth (mobile) | Expo AuthSession with Google OAuth |
| Auth (API) | PyJWT — validates JWTs from Auth.js on every protected route |
| Type sharing | FastAPI auto-generates OpenAPI spec → `openapi-typescript` generates TS types |
| Real-time | AWS API Gateway WebSockets + Lambda (live leaderboard) |
| Background jobs | Celery + AWS SQS (broker) + Redis (ElastiCache) as result backend |
| Email | AWS SES |
| File storage | AWS S3 + CloudFront |
| Integrations | Slack API (slash commands) + Discord Bot (discord.py) |
| Container registry | AWS ECR |
| Compute (API) | AWS ECS Fargate (containerized FastAPI) |
| Compute (web) | AWS Amplify (Next.js) |
| Load balancer | AWS ALB (Application Load Balancer) in front of ECS |
| Infrastructure as code | AWS CDK (Python) |
| Secrets | AWS Secrets Manager |
| Monitoring | AWS CloudWatch + Sentry |
| Testing (backend) | pytest + pytest-asyncio |
| Testing (frontend) | Vitest (unit), Playwright (E2E) |
| CI/CD | GitHub Actions |

---

## Repository Structure

The project is a monorepo. JavaScript/TypeScript apps use Turborepo. The Python backend lives
alongside them as a peer directory. Infrastructure is defined in a separate `infra/` directory
using AWS CDK.

```
rankkit/
├── apps/
│   ├── web/                          # Next.js 14 web application
│   └── mobile/                       # Expo React Native app (Phase 2)
├── backend/                          # FastAPI Python application
│   ├── app/
│   │   ├── main.py                   # FastAPI app factory, middleware, router registration
│   │   ├── config.py                 # Settings via pydantic-settings (reads env vars)
│   │   ├── database.py               # Async SQLAlchemy engine + session factory
│   │   ├── models/                   # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── league.py
│   │   │   ├── match.py
│   │   │   └── __init__.py
│   │   ├── schemas/                  # Pydantic request/response schemas
│   │   │   ├── league.py
│   │   │   ├── match.py
│   │   │   ├── player.py
│   │   │   └── __init__.py
│   │   ├── routers/                  # FastAPI route handlers
│   │   │   ├── auth.py
│   │   │   ├── leagues.py
│   │   │   ├── matches.py
│   │   │   ├── players.py
│   │   │   ├── tournaments.py
│   │   │   └── seasons.py
│   │   ├── services/
│   │   │   ├── rating_service.py     # Orchestrates rating calculations
│   │   │   ├── match_service.py      # Match lifecycle state machine
│   │   │   ├── notify_service.py     # Triggers Celery tasks
│   │   │   └── slack_service.py      # Slack API integration
│   │   ├── rating/                   # Pure Python Elo + Glicko-2 math, no framework deps
│   │   │   ├── elo.py
│   │   │   ├── glicko2.py
│   │   │   ├── team.py
│   │   │   ├── ffa.py
│   │   │   └── __init__.py
│   │   ├── workers/                  # Celery task definitions
│   │   │   ├── celery_app.py         # Celery app configured with SQS broker
│   │   │   ├── match_tasks.py        # Post-confirmation jobs
│   │   │   ├── season_tasks.py       # Season reset cron
│   │   │   └── email_tasks.py        # SES email sending
│   │   └── middleware/
│   │       ├── auth.py               # JWT verification dependency
│   │       └── error_handler.py      # Global exception handlers
│   ├── alembic/                      # Database migrations
│   │   ├── env.py
│   │   └── versions/
│   ├── tests/
│   │   ├── test_elo.py
│   │   ├── test_glicko2.py
│   │   ├── test_match_service.py
│   │   └── conftest.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── alembic.ini
├── packages/
│   └── types/                        # Auto-generated TS types from FastAPI OpenAPI spec
│       └── generated/
│           └── api.ts                # Output of openapi-typescript — never edit manually
├── infra/                            # AWS CDK (Python) infrastructure definitions
│   ├── app.py                        # CDK app entry point
│   ├── stacks/
│   │   ├── network_stack.py          # VPC, subnets, security groups
│   │   ├── database_stack.py         # RDS PostgreSQL
│   │   ├── compute_stack.py          # ECS Fargate cluster, ALB, task definitions
│   │   ├── cache_stack.py            # ElastiCache Redis
│   │   ├── queue_stack.py            # SQS queues for Celery
│   │   ├── storage_stack.py          # S3 buckets, CloudFront distributions
│   │   └── realtime_stack.py         # API Gateway WebSockets + Lambda
│   └── requirements.txt              # CDK dependencies
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
├── turbo.json                        # JS monorepo task pipeline
├── pnpm-workspace.yaml
├── package.json
└── .env.example
```

---

## Database Schema (SQLAlchemy)

Define the following models in `backend/app/models/`. Use SQLAlchemy 2.0 declarative style with
async support. This schema handles all match formats without forking into separate tables — a core
architectural decision worth discussing in interviews.

### `models/user.py`

```python
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import uuid

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String)
    image: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    league_memberships: Mapped[list["LeagueMember"]] = relationship(back_populates="user")
    match_participations: Mapped[list["MatchParticipant"]] = relationship(back_populates="user")
```

### `models/league.py`

```python
import enum
from sqlalchemy import String, Boolean, Integer, Enum, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Format(str, enum.Enum):
    ONE_V_ONE = "ONE_V_ONE"
    TEAM = "TEAM"
    FFA = "FFA"
    TOURNAMENT = "TOURNAMENT"

class RatingSystem(str, enum.Enum):
    ELO = "ELO"
    GLICKO2 = "GLICKO2"

class League(Base):
    __tablename__ = "leagues"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)  # public URL
    format: Mapped[Format] = mapped_column(Enum(Format), nullable=False)
    rating_system: Mapped[RatingSystem] = mapped_column(Enum(RatingSystem), default=RatingSystem.ELO)
    default_k: Mapped[int] = mapped_column(Integer, default=32)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    members: Mapped[list["LeagueMember"]] = relationship(back_populates="league")
    matches: Mapped[list["Match"]] = relationship(back_populates="league")
    seasons: Mapped[list["Season"]] = relationship(back_populates="league")
    teams: Mapped[list["Team"]] = relationship(back_populates="league")
    tournaments: Mapped[list["Tournament"]] = relationship(back_populates="league")

class LeagueMember(Base):
    __tablename__ = "league_members"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    league_id: Mapped[str] = mapped_column(ForeignKey("leagues.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String, default="member")  # "admin" | "member"
    rating: Mapped[float] = mapped_column(default=1000.0)
    rating_dev: Mapped[float] = mapped_column(default=350.0)      # Glicko-2 rating deviation
    volatility: Mapped[float] = mapped_column(default=0.06)       # Glicko-2 volatility
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    draws: Mapped[int] = mapped_column(Integer, default=0)
    joined_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    league: Mapped["League"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="league_memberships")

    __table_args__ = (UniqueConstraint("league_id", "user_id"),)
```

### `models/match.py`

```python
class MatchStatus(str, enum.Enum):
    PENDING = "PENDING"
    AWAITING_CONFIRMATION = "AWAITING_CONFIRMATION"
    DISPUTED = "DISPUTED"
    COMPLETED = "COMPLETED"
    ROLLED_BACK = "ROLLED_BACK"

class Match(Base):
    __tablename__ = "matches"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    league_id: Mapped[str] = mapped_column(ForeignKey("leagues.id"), nullable=False)
    format: Mapped[Format] = mapped_column(Enum(Format), nullable=False)
    status: Mapped[MatchStatus] = mapped_column(Enum(MatchStatus), default=MatchStatus.AWAITING_CONFIRMATION)
    team1_id: Mapped[str | None] = mapped_column(ForeignKey("teams.id"))   # TEAM format only
    team2_id: Mapped[str | None] = mapped_column(ForeignKey("teams.id"))   # TEAM format only
    tournament_id: Mapped[str | None] = mapped_column(ForeignKey("tournaments.id"))
    reported_by_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    confirmed_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    disputed_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    dispute_note: Mapped[str | None] = mapped_column(String)
    played_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    participants: Mapped[list["MatchParticipant"]] = relationship(back_populates="match")
    league: Mapped["League"] = relationship(back_populates="matches")

class MatchParticipant(Base):
    __tablename__ = "match_participants"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    match_id: Mapped[str] = mapped_column(ForeignKey("matches.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    team_id: Mapped[str | None] = mapped_column(ForeignKey("teams.id"))   # null for 1v1 and FFA
    placement: Mapped[int | None] = mapped_column(Integer)                 # 1/2/3... for FFA only
    score: Mapped[int | None] = mapped_column(Integer)
    is_winner: Mapped[bool | None] = mapped_column(Boolean)               # for 1v1 and TEAM
    rating_before: Mapped[float] = mapped_column(nullable=False)
    rating_after: Mapped[float] = mapped_column(nullable=False)
    rating_delta: Mapped[float] = mapped_column(nullable=False)

    match: Mapped["Match"] = relationship(back_populates="participants")
    user: Mapped["User"] = relationship(back_populates="match_participations")

class RatingHistory(Base):
    __tablename__ = "rating_history"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    league_id: Mapped[str] = mapped_column(ForeignKey("leagues.id"), nullable=False)
    match_id: Mapped[str | None] = mapped_column(ForeignKey("matches.id"))
    rating: Mapped[float] = mapped_column(nullable=False)
    rating_dev: Mapped[float | None] = mapped_column()
    recorded_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
```

---

## Alembic Migrations

Configure Alembic in `backend/alembic/env.py` to use the async SQLAlchemy engine and import all
models so they are detected. Every schema change must be a numbered Alembic migration — never
modify the database manually. Use `alembic revision --autogenerate -m "description"` to generate
migrations and `alembic upgrade head` to apply them.

The CD pipeline runs `alembic upgrade head` **before** starting the new ECS task — this is the
correct order and an important interview talking point.

---

## backend/app/rating/ — Rating Math Package

This module must be pure Python with zero framework or database dependencies. It is fully unit
tested with pytest. It is the most interview-critical piece of the codebase.

### `rating/elo.py`

```python
from dataclasses import dataclass

@dataclass
class EloResult:
    winner_rating_after: float
    loser_rating_after: float
    delta: float

def calculate_elo(
    winner_rating: float,
    loser_rating: float,
    k_factor: int = 32
) -> EloResult:
    expected = 1 / (1 + 10 ** ((loser_rating - winner_rating) / 400))
    delta = round(k_factor * (1 - expected), 2)
    return EloResult(
        winner_rating_after=winner_rating + delta,
        loser_rating_after=loser_rating - delta,
        delta=delta,
    )
```

### `rating/glicko2.py`

Implement the full Glicko-2 algorithm as defined by Mark Glickman
(http://www.glicko.net/glicko/glicko2.pdf). The algorithm takes a player's current rating, rating
deviation (RD), and volatility, plus a list of opponents with their ratings and outcomes, and
returns updated values. Export:

```python
@dataclass
class PlayerRating:
    user_id: str
    rating: float
    rating_dev: float
    volatility: float

@dataclass
class Glicko2Result:
    user_id: str
    rating_before: float
    rating_after: float
    rating_dev_after: float
    volatility_after: float
    delta: float

def calculate_glicko2(
    player: PlayerRating,
    opponents: list[PlayerRating],
    outcomes: list[float],  # 1.0 = win, 0.5 = draw, 0.0 = loss per opponent
) -> Glicko2Result: ...
```

### `rating/team.py`

```python
def calculate_team_elo(
    team1: list[PlayerRating],
    team2: list[PlayerRating],
    winner: int,  # 1 or 2
    k_factor: int = 32,
) -> list[dict]:
    """
    Average team ratings to determine expected outcome.
    Distribute delta equally to all players on both sides.
    Return list of {user_id, rating_before, rating_after, delta}.
    """
```

### `rating/ffa.py`

```python
def calculate_ffa_ratings(
    players: list[PlayerRating],
    placements: list[tuple[str, int]],  # [(user_id, place), ...]
) -> list[dict]:
    """
    Pairwise decomposition: treat each pair as a virtual 1v1 where
    higher placement wins. Average the resulting deltas per player.
    Return list of {user_id, rating_before, rating_after, delta}.
    """
```

### `tests/test_elo.py`

Write at least 12 pytest tests covering: equal ratings, heavy favourite wins, heavy underdog wins,
different K-factors, rating floor (never below 100), idempotency of symmetric matches, team
aggregation, and FFA placement ordering.

---

## FastAPI Application

### `app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, leagues, matches, players, tournaments, seasons
from app.middleware.error_handler import register_exception_handlers

def create_app() -> FastAPI:
    app = FastAPI(
        title="RankKit API",
        version="1.0.0",
        docs_url="/api/docs",       # Swagger UI (free, auto-generated)
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",  # Used to generate TS types
    )
    app.add_middleware(CORSMiddleware, allow_origins=settings.ALLOWED_ORIGINS, ...)
    register_exception_handlers(app)
    app.include_router(auth.router, prefix="/v1/auth", tags=["auth"])
    app.include_router(leagues.router, prefix="/v1/leagues", tags=["leagues"])
    app.include_router(matches.router, prefix="/v1", tags=["matches"])
    app.include_router(players.router, prefix="/v1", tags=["players"])
    app.include_router(tournaments.router, prefix="/v1", tags=["tournaments"])
    app.include_router(seasons.router, prefix="/v1", tags=["seasons"])
    return app

app = create_app()
```

### `app/middleware/auth.py`

FastAPI dependency that validates the JWT issued by Auth.js on the web or Expo on mobile:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.NEXTAUTH_SECRET,
            algorithms=["HS256"]
        )
        user_id = payload.get("sub")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user
```

Every protected route receives `current_user: User = Depends(get_current_user)`.

### Response Envelope

Every response must use a consistent Pydantic schema. Define a generic wrapper:

```python
from pydantic import BaseModel
from typing import Generic, TypeVar

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    data: T | None = None
    error: dict | None = None

class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    error: None = None
    meta: dict  # {"page": int, "total": int, "per_page": int}
```

### All API Endpoints

Implement the following. Every route must include full Pydantic response_model annotations so the
auto-generated OpenAPI spec is complete and accurate — this is how TypeScript types are shared
with the frontend.

```
POST   /v1/auth/session              # validate JWT, upsert user in DB, return profile
GET    /v1/auth/me                   # return current user

GET    /v1/leagues                   # user's leagues with current ratings
POST   /v1/leagues                   # create league
GET    /v1/leagues/{id}              # league detail + full leaderboard sorted by rating
PATCH  /v1/leagues/{id}              # update name/description/settings (admin only)
DELETE /v1/leagues/{id}             # delete (admin only)
GET    /v1/leagues/{id}/leaderboard  # paginated leaderboard with rank, win rate, delta

POST   /v1/leagues/{id}/invite                      # send invite email via SES
DELETE /v1/leagues/{id}/members/{user_id}           # remove member (admin only)

GET    /v1/leagues/{id}/matches                      # paginated match history
POST   /v1/leagues/{id}/matches                      # log a match
GET    /v1/leagues/{id}/matches/{match_id}
POST   /v1/leagues/{id}/matches/{match_id}/confirm   # opponent confirms result
POST   /v1/leagues/{id}/matches/{match_id}/dispute   # opponent disputes result
DELETE /v1/leagues/{id}/matches/{match_id}           # rollback match (admin only)

GET    /v1/leagues/{id}/players/{user_id}            # profile: rating, record, rank
GET    /v1/leagues/{id}/players/{user_id}/history    # rating over time (for graph)

POST   /v1/leagues/{id}/tournaments                  # create + seed by current Elo
GET    /v1/leagues/{id}/tournaments/{t_id}
POST   /v1/leagues/{id}/tournaments/{t_id}/advance   # log tournament match result

POST   /v1/leagues/{id}/seasons/end                  # end active season, soft-reset ratings
GET    /v1/leagues/{id}/seasons                      # all past seasons with final standings
```

### Match Lifecycle State Machine (Critical)

The match flow must follow this exact sequence. This is a core interview talking point.

1. Reporter calls `POST /leagues/{id}/matches`
   → status set to `AWAITING_CONFIRMATION`
   → ratings are NOT updated yet
   → Celery task dispatched to notify opponent via SES + push notification

2. Opponent calls `POST /matches/{id}/confirm`
   → `match_service.confirm_match()` is called
   → status becomes `COMPLETED`
   → `rating_service.apply_match_ratings()` calculates and applies ratings in a single DB transaction
   → `RatingHistory` row inserted for each participant
   → Celery task dispatched to post result to Slack/Discord and send result emails

3. Opponent calls `POST /matches/{id}/dispute`
   → status becomes `DISPUTED`
   → Celery task dispatched to notify league admin via SES

4. Admin calls `DELETE /matches/{id}` to roll back
   → reads `rating_before` from each `MatchParticipant`
   → restores each `LeagueMember.rating` to that value in a single transaction
   → status becomes `ROLLED_BACK`

### `services/rating_service.py`

```python
async def apply_match_ratings(match_id: str, db: AsyncSession) -> None:
    """
    1. Load match + all MatchParticipant rows
    2. Load current LeagueMember ratings for all participants
    3. Call correct function from app.rating based on match.format and league.rating_system
    4. Write rating_before, rating_after, rating_delta to each MatchParticipant
    5. Update LeagueMember.rating (+ rating_dev, volatility for Glicko-2)
    6. Insert RatingHistory row for each participant
    7. All steps in a single SQLAlchemy async transaction — rollback on any failure
    """
```

---

## Type Sharing: FastAPI → TypeScript

FastAPI automatically generates an OpenAPI JSON spec at `/api/openapi.json`. The CI pipeline
uses this to generate TypeScript types consumed by both `apps/web` and `apps/mobile`.

Add to the CI pipeline (runs after the API is built):

```bash
# Download the OpenAPI spec from the running dev server
curl http://localhost:8000/api/openapi.json -o openapi.json

# Generate TypeScript types
pnpm dlx openapi-typescript openapi.json -o packages/types/generated/api.ts
```

The generated `packages/types/generated/api.ts` file is never edited manually. All frontend
types are imported from here:

```typescript
// apps/web/src/lib/api.ts
import type { components, paths } from "@rankkit/types/generated/api"

type League = components["schemas"]["LeagueResponse"]
type LogMatchInput = components["schemas"]["LogMatchRequest"]
```

This pattern is a strong interview talking point: the Python Pydantic models are the single source
of truth for types across the entire stack.

---

## apps/web — Next.js Web App

### App Router Structure

```
apps/web/src/app/
├── (auth)/
│   └── login/page.tsx
├── (dashboard)/
│   ├── layout.tsx                  # sidebar + auth guard
│   ├── dashboard/page.tsx          # leagues overview
│   └── leagues/
│       ├── new/page.tsx
│       └── [id]/
│           ├── page.tsx            # leaderboard (real-time via API GW WebSocket)
│           ├── matches/page.tsx
│           ├── matches/new/page.tsx
│           └── players/[userId]/page.tsx
├── l/[slug]/page.tsx               # PUBLIC leaderboard (no auth)
└── api/
    └── auth/[...nextauth]/route.ts
```

### API Client

Create `apps/web/src/lib/api.ts` — a typed wrapper around fetch. All components call this, never
raw fetch. This pattern is critical for sharing with mobile.

```typescript
const BASE_URL = process.env.NEXT_PUBLIC_API_URL

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const session = await getSession()
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${session?.accessToken}`,
      ...init?.headers,
    },
  })
  if (!res.ok) throw new APIError(res.status, await res.json())
  return res.json()
}

export const api = {
  leagues: {
    list: () => request<ApiResponse<League[]>>("/v1/leagues"),
    get: (id: string) => request<ApiResponse<League>>(`/v1/leagues/${id}`),
    create: (body: CreateLeagueRequest) =>
      request<ApiResponse<League>>("/v1/leagues", { method: "POST", body: JSON.stringify(body) }),
  },
  matches: {
    log: (leagueId: string, body: LogMatchRequest) =>
      request<ApiResponse<Match>>(`/v1/leagues/${leagueId}/matches`, {
        method: "POST", body: JSON.stringify(body),
      }),
    confirm: (leagueId: string, matchId: string) =>
      request<ApiResponse<Match>>(`/v1/leagues/${leagueId}/matches/${matchId}/confirm`, {
        method: "POST", body: "{}",
      }),
  },
  // ... all other endpoints follow the same pattern
}
```

### Real-Time Leaderboard via AWS API Gateway WebSockets

On the leaderboard page, connect to the API Gateway WebSocket URL. When the server pushes a
`RATING_UPDATED` event (emitted by the Celery worker after a match is confirmed), update local
state and re-sort the leaderboard without a full page reload.

```typescript
useEffect(() => {
  const ws = new WebSocket(`${process.env.NEXT_PUBLIC_WS_URL}?leagueId=${id}`)
  ws.onmessage = (event) => {
    const { type, payload } = JSON.parse(event.data)
    if (type === "RATING_UPDATED") updateLeaderboard(payload)
  }
  return () => ws.close()
}, [id])
```

### Rating History Graph

On the player profile page, render a Recharts `LineChart` using the player's `RatingHistory`
records. X-axis is date, Y-axis is rating. Include a reference line at 1000 (starting rating).

### Public League Page

`/l/[slug]` renders the leaderboard with no auth. Use Next.js `generateMetadata` to generate
dynamic Open Graph tags so sharing the URL on Slack or Twitter shows a preview card with the
league name and top 3 players.

---

## apps/mobile — Expo App (Phase 2)

Build after the web app is live and stable with real users.

### Navigation (Expo Router)

```
apps/mobile/app/
├── (auth)/login.tsx
├── (tabs)/
│   ├── _layout.tsx         # bottom tabs
│   ├── index.tsx           # leagues list
│   ├── log.tsx             # match logging (3-tap target)
│   └── profile.tsx
└── league/
    ├── [id].tsx
    └── [id]/player/[userId].tsx
```

### Shared API Client

Copy `apps/web/src/lib/api.ts` to `apps/mobile/src/lib/api.ts`. The only difference is the
`BASE_URL`. All types come from `packages/types/generated/api.ts`. This is the direct payoff of
the clean API client pattern.

### Push Notifications

Use Expo Notifications. On login, register the device push token and store it against the user
via `POST /v1/auth/device-token`. Trigger notifications from Celery tasks when:
- A match is logged against the user (awaiting confirmation)
- A match dispute is raised in their league
- Their rating changes by ±50 or more points

---

## AWS Infrastructure (CDK)

Define all infrastructure in `infra/` using AWS CDK (Python). Never manually create AWS resources
— everything must be in code. This is a strong interview talking point.

### `infra/stacks/network_stack.py`

- VPC with public and private subnets across 2 AZs
- NAT Gateway for private subnet outbound traffic
- Security groups: one for ALB (inbound 80/443 from internet), one for ECS tasks (inbound from
  ALB only), one for RDS (inbound from ECS only), one for ElastiCache (inbound from ECS only)

### `infra/stacks/database_stack.py`

- RDS PostgreSQL 16 instance in private subnet
- Multi-AZ enabled for production
- Automated backups with 7-day retention
- Credentials stored in AWS Secrets Manager
- Output the connection string as a CDK export consumed by the compute stack

### `infra/stacks/compute_stack.py`

- ECR repository for the FastAPI Docker image
- ECS Fargate cluster
- Task definition: FastAPI container + Celery worker as sidecar container
- Service with desired count 2, auto-scaling based on CPU (target 60%)
- Application Load Balancer with HTTPS listener (ACM certificate)
- ALB routes traffic to ECS service target group
- Health check endpoint: `GET /health` returns 200

### `infra/stacks/cache_stack.py`

- ElastiCache Redis (single node for dev, cluster mode for production)
- In private subnet, accessible only from ECS security group
- Used as Celery result backend

### `infra/stacks/queue_stack.py`

- SQS Standard Queue for Celery broker: `rankkit-tasks`
- Dead Letter Queue for failed tasks with max receives = 3
- Celery configured with `kombu` SQS transport

### `infra/stacks/storage_stack.py`

- S3 bucket for user-uploaded content (league avatars, etc.)
- CloudFront distribution in front of S3 with OAC
- S3 bucket policy allowing only CloudFront OAC

### `infra/stacks/realtime_stack.py`

- API Gateway v2 WebSocket API
- Lambda function (Python) as `$connect`, `$disconnect`, `$default` handler
- DynamoDB table to store active WebSocket connections keyed by `leagueId`
- Lambda integration: when a Celery task completes a match, it calls
  `POST /v1/internal/broadcast` on the API which triggers the Lambda to push
  the `RATING_UPDATED` event to all connected clients for that league

### CDK Bootstrap and Deploy

```bash
# First-time setup
cd infra
pip install -r requirements.txt
cdk bootstrap aws://ACCOUNT_ID/REGION

# Deploy all stacks
cdk deploy --all

# Deploy individual stack
cdk deploy RankKitComputeStack
```

---

## Celery Background Jobs

Configure Celery in `backend/app/workers/celery_app.py` with SQS as broker and Redis as result
backend:

```python
from celery import Celery

celery_app = Celery(
    "rankkit",
    broker=f"sqs://",                        # uses boto3 with IAM role, no keys needed on ECS
    backend=f"redis://{settings.REDIS_HOST}:6379/0",
    include=["app.workers.match_tasks", "app.workers.email_tasks", "app.workers.season_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_expires=3600,
    broker_transport_options={"region": "us-east-1", "queue_name_prefix": "rankkit-"},
)
```

### Task Definitions

```python
# workers/match_tasks.py
@celery_app.task
def notify_match_pending(match_id: str): ...     # SES email + push notification to opponent

@celery_app.task
def broadcast_match_result(match_id: str): ...   # WebSocket broadcast + Slack/Discord post

@celery_app.task
def notify_dispute(match_id: str): ...           # SES email to league admin

# workers/season_tasks.py
@celery_app.task
def reset_season(league_id: str): ...            # Soft-reset ratings by 30% toward 1000

# workers/email_tasks.py
@celery_app.task
def send_weekly_digest(league_id: str): ...      # Weekly standings email via SES

# Cron schedule (Celery Beat)
celery_app.conf.beat_schedule = {
    "weekly-digest": {
        "task": "app.workers.email_tasks.send_weekly_digest_all",
        "schedule": crontab(day_of_week="monday", hour=9),
    },
}
```

The Celery worker runs as a separate ECS Fargate task using the same Docker image as the API,
started with `celery -A app.workers.celery_app worker` as the container command.

---

## Docker

### `backend/Dockerfile`

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# API mode (default)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Celery worker mode (override CMD in ECS task definition)
# CMD ["celery", "-A", "app.workers.celery_app", "worker", "--loglevel=info"]
```

The ECS task definition defines two containers from the same image — one running the API command,
one running the Celery command. This avoids maintaining two Dockerfiles.

---

## GitHub Actions CI/CD

### `.github/workflows/ci.yml`

Triggers on: `pull_request` targeting `main`

All jobs run in parallel:

1. **lint-backend** — `ruff check backend/` + `black --check backend/`
2. **lint-frontend** — `pnpm lint` across all JS packages
3. **typecheck** — `pnpm typecheck` (tsc --noEmit in all JS apps)
4. **test-backend** — spin up Postgres service container, run `pytest backend/tests/ -v`
5. **test-frontend** — `pnpm test` (Vitest on any JS unit tests)
6. **e2e** — spin up Postgres + start FastAPI dev server + start Next.js + run Playwright on
   critical flows: sign in, create league, log match, confirm match, verify leaderboard updated

All jobs must pass. Branch protection on `main` enforces this.

### `.github/workflows/cd.yml`

Triggers on: `push` to `main`

Steps (sequential):

```yaml
steps:
  - uses: actions/checkout@v4

  - name: Configure AWS credentials
    uses: aws-actions/configure-aws-credentials@v4
    with:
      role-to-assume: arn:aws:iam::ACCOUNT:role/GitHubActionsRole
      aws-region: us-east-1

  - name: Login to ECR
    uses: aws-actions/amazon-ecr-login@v2

  - name: Build and push Docker image
    run: |
      docker build -t $ECR_REGISTRY/rankkit-api:$GITHUB_SHA backend/
      docker push $ECR_REGISTRY/rankkit-api:$GITHUB_SHA

  - name: Run database migrations
    run: |
      # Run Alembic migrations via a one-off ECS task BEFORE updating the service
      aws ecs run-task \
        --cluster rankkit \
        --task-definition rankkit-migrate \
        --overrides '{"containerOverrides":[{"name":"api","command":["alembic","upgrade","head"]}]}'

  - name: Deploy to ECS
    run: |
      aws ecs update-service \
        --cluster rankkit \
        --service rankkit-api \
        --force-new-deployment \
        --task-definition rankkit-api:$GITHUB_SHA

  - name: Deploy web to Amplify
    run: |
      aws amplify start-job \
        --app-id $AMPLIFY_APP_ID \
        --branch-name main \
        --job-type RELEASE

  - name: EAS OTA update (mobile)
    run: |
      pnpm dlx eas-cli@latest update --branch production --message "Deploy $GITHUB_SHA"

  - name: Create Sentry release
    run: |
      npx sentry-cli releases new $GITHUB_SHA
      npx sentry-cli releases finalize $GITHUB_SHA
```

Use OIDC to authenticate GitHub Actions with AWS (no long-lived access keys). Create an IAM role
that trusts the GitHub OIDC provider and has the minimum permissions needed for ECR push, ECS
update, Amplify deploy, and running migration tasks.

---

## AWS Integrations

### AWS SES (Email)

Use `boto3` to send transactional emails from Celery tasks. Verify your sending domain in SES.
Send: invite emails, match confirmation requests, dispute notifications, weekly digests.

```python
import boto3

ses = boto3.client("ses", region_name="us-east-1")

def send_email(to: str, subject: str, html: str) -> None:
    ses.send_email(
        Source="noreply@rankkit.app",
        Destination={"ToAddresses": [to]},
        Message={
            "Subject": {"Data": subject},
            "Body": {"Html": {"Data": html}},
        },
    )
```

### AWS Secrets Manager

Store all secrets (DB password, JWT secret, Slack tokens, Discord token) in Secrets Manager. ECS
task definitions reference secrets by ARN — they are injected as environment variables at container
startup. Never hardcode secrets or pass them via environment variables in plain text.

```python
# config.py — reads from environment (injected from Secrets Manager via ECS)
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    NEXTAUTH_SECRET: str
    REDIS_HOST: str
    SLACK_SIGNING_SECRET: str
    DISCORD_BOT_TOKEN: str
    AWS_REGION: str = "us-east-1"

settings = Settings()
```

### AWS CloudWatch

- ECS container logs stream automatically to CloudWatch Log Groups
- Create a CloudWatch dashboard with: API request rate, error rate (4xx/5xx), ECS CPU/memory,
  RDS connection count, SQS queue depth (backlog of unprocessed Celery tasks)
- Set CloudWatch alarms on: error rate > 5%, ECS CPU > 80%, RDS CPU > 70%

---

## Integrations

### Slack

When a user connects their Slack workspace (via OAuth in league settings), the app:
- Posts match results to a configured channel after confirmation
- Accepts `/rankkit match @user1 vs @user2 3-1` slash command to log a match from Slack

Implement `POST /v1/integrations/slack/events` in FastAPI to receive Slack event payloads.
Verify the `X-Slack-Signature` header using HMAC-SHA256 on every request.

### Discord

Use `discord.py` to handle slash command interactions. Register `/match` via Discord application
portal. Post result embeds to a configured channel after each confirmed match.

---

## Environment Variables

Document all in `.env.example`. For local dev, copy to `.env`. In production, all secrets live
in AWS Secrets Manager and are injected by ECS.

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/rankkit

# Auth
NEXTAUTH_SECRET=
NEXTAUTH_URL=http://localhost:3000
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# API
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=wss://YOUR_API_GW_ID.execute-api.us-east-1.amazonaws.com/prod

# Redis
REDIS_HOST=localhost

# AWS
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=

# SQS
SQS_QUEUE_URL=

# Email
SES_FROM_EMAIL=noreply@rankkit.app

# Integrations
SLACK_CLIENT_ID=
SLACK_CLIENT_SECRET=
SLACK_SIGNING_SECRET=
DISCORD_BOT_TOKEN=
DISCORD_APPLICATION_ID=

# Monitoring
SENTRY_DSN=

# Mobile
EXPO_PUBLIC_API_URL=http://localhost:8000

# CDK
CDK_DEFAULT_ACCOUNT=
CDK_DEFAULT_REGION=us-east-1
```

---

## README Requirements

The README must function as a design document, not just setup instructions. Include:

1. **What it is** — one paragraph product description
2. **Architecture diagram** — showing all AWS services and how they connect
3. **Key technical decisions and trade-offs:**
   - Why FastAPI over Node/Express (async performance, automatic OpenAPI, Python ecosystem for math)
   - Why the `MatchParticipant` unified table design instead of separate tables per format
   - Why ratings update on confirmation, not on logging (prevents gaming, consistent state)
   - Why Glicko-2 for FFA instead of standard Elo (handles multi-opponent, tracks confidence)
   - Why Celery + SQS over a managed service like AWS Lambda for background jobs
   - Why Alembic migrations run before ECS service update (schema-code compatibility window)
   - Why OIDC over IAM access keys in GitHub Actions (no long-lived credentials)
   - How OpenAPI spec is the single source of truth for TypeScript types
4. **Local development setup** — step-by-step from a fresh machine
5. **AWS deployment** — CDK bootstrap and deploy commands
6. **Running tests** — pytest for backend, Playwright for E2E
7. **What I'd do differently** — honest reflection on trade-offs

---

## Build Sequence

Build in this exact order. Do not start Phase 2 until Phase 1 has live users.

**Phase 1 — Backend + Web (Weeks 1–6)**
1. Week 1: Monorepo + CDK infra skeletons, SQLAlchemy models, Alembic migration, FastAPI
   skeleton with all route stubs + Swagger UI, Next.js with Auth.js, GitHub Actions CI/CD
2. Week 2: League creation, 1v1 match logging + Elo calculation, basic leaderboard, invite via SES
3. Week 3: Team + FFA formats, Glicko-2, match confirmation + dispute flow, rating transactions
4. Week 4: Tournament bracket engine, seasons, rating history graphs (Recharts)
5. Week 5: WebSocket real-time leaderboard, Slack + Discord integrations, Celery jobs
6. Week 6: Public league pages, OG images, Sentry, rate limiting, deploy to AWS, launch

**Stabilization (Weeks 7–8)**
Get real users. Fix bugs. Watch CloudWatch dashboards. Improve onboarding. Build interview stories
from real production issues.

**Phase 2 — Mobile (Weeks 9–14)**
7. Week 9: Expo setup in monorepo, Expo Router, auth flow reusing shared API client
8. Week 10: League list, leaderboard, player profiles
9. Week 11: Match logging screen (3-tap target), push notifications
10. Week 12: Tournament view, rating history (Victory Native charts)
11. Week 13: Polish, TestFlight + Play Store beta
12. Week 14: App Store submission via EAS

---

## Interview Talking Points to Build Toward

Every major decision in this project should be something you can discuss for 5+ minutes:

- **FastAPI OpenAPI → TypeScript types**: Pydantic models are the single source of truth.
  The frontend never has hand-written API types — they are generated from the spec on every build.
- **`MatchParticipant` unified table**: one table expresses all four formats via nullable
  `team_id` and `placement` fields. Explain the alternative (four separate tables) and why
  the unified design is better for queries and reporting.
- **Ratings update on confirmation, not logging**: the state machine and why this prevents
  one player from gaming their rating by logging matches their opponent never confirms.
- **SQLAlchemy async transaction in `rating_service`**: why all rating updates must be atomic
  — partial application would corrupt the leaderboard permanently.
- **Alembic before ECS update**: the window where new code runs against old schema vs old
  code runs against new schema — why the former is always safer.
- **OIDC vs IAM keys in GitHub Actions**: no long-lived credentials stored anywhere.
- **Celery + SQS**: why SQS over Redis as broker in production (durability, AWS-native IAM
  auth, no broker single point of failure), and when you'd choose Lambda instead.
- **ECS Fargate vs EC2**: why managed compute, and what you'd change if you needed GPUs or
  very low latency (EC2 with placement groups).
- **AWS CDK**: infrastructure is version-controlled, reviewed in PRs, and reproducible.
  Every resource is tagged. Describe how you'd add a new environment (staging) with one command.
- **Glicko-2 for FFA**: what rating deviation represents (confidence in the rating) and why
  standard Elo's assumption of one opponent makes it mathematically unsound for multi-player.
