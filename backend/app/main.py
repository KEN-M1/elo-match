from contextlib import asynccontextmanager
from inspect import isawaitable

from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import settings
from app.runtime import RankKitRuntime, create_runtime


class SyncUserRequest(BaseModel):
    email: str
    name: str | None = None
    image: str | None = None


class CreateLeagueRequest(BaseModel):
    owner_id: str
    name: str
    slug: str
    description: str | None = None
    is_public: bool = True


class CreateInviteRequest(BaseModel):
    admin_id: str


class AcceptInviteRequest(BaseModel):
    user_id: str


class LogMatchRequest(BaseModel):
    reported_by_id: str
    winner_id: str
    loser_id: str


class ActorRequest(BaseModel):
    actor_id: str
    note: str | None = None


def create_app(runtime: RankKitRuntime | None = None) -> FastAPI:
    runtime = runtime or create_runtime()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        close = getattr(runtime.store, "close", None)
        if close is None:
            return
        result = close()
        if isawaitable(result):
            await result

    app = FastAPI(
        title="RankKit API",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in settings.allowed_origins.split(",")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/v1/auth/sync")
    async def sync_user(body: SyncUserRequest) -> dict:
        return await runtime.route_policy.data_response(
            lambda: runtime.store.sync_user(body.email, body.name, body.image)
        )

    @app.get("/v1/auth/me")
    async def me(
        authorization: str | None = Header(default=None),
        x_rankkit_user: str | None = Header(default=None),
    ) -> dict:
        return await runtime.route_policy.auth_response(
            lambda: runtime.auth_session.current_user(runtime.store, authorization, x_rankkit_user)
        )

    @app.post("/v1/leagues")
    async def create_league(body: CreateLeagueRequest) -> dict:
        return await runtime.route_policy.data_response(
            lambda: runtime.store.create_league(
                owner_id=body.owner_id,
                name=body.name,
                slug=body.slug,
                description=body.description,
                is_public=body.is_public,
            )
        )

    @app.get("/v1/leagues")
    async def list_leagues(user_id: str | None = None) -> dict:
        return await runtime.route_policy.data_response(lambda: runtime.store.list_leagues(user_id))

    @app.get("/v1/leagues/{league_id}")
    async def get_league(league_id: str) -> dict:
        return await runtime.route_policy.data_response(lambda: runtime.store.get_league(league_id))

    @app.get("/v1/leagues/{league_id}/leaderboard")
    async def leaderboard(league_id: str) -> dict:
        return await runtime.route_policy.data_response(lambda: runtime.store.leaderboard(league_id))

    @app.get("/v1/leagues/{league_id}/members")
    async def members(league_id: str) -> dict:
        return await runtime.route_policy.data_response(lambda: runtime.store.member_summaries(league_id))

    @app.post("/v1/leagues/{league_id}/invites")
    async def create_invite(league_id: str, body: CreateInviteRequest) -> dict:
        return await runtime.route_policy.data_response(lambda: runtime.store.create_invite(league_id, body.admin_id))

    @app.post("/v1/invites/{token}/accept")
    async def accept_invite(token: str, body: AcceptInviteRequest) -> dict:
        return await runtime.route_policy.data_response(lambda: runtime.store.accept_invite(token, body.user_id))

    @app.post("/v1/leagues/{league_id}/matches")
    async def log_match(league_id: str, body: LogMatchRequest) -> dict:
        return await runtime.route_policy.data_response(
            lambda: runtime.store.log_match(
                league_id=league_id,
                reported_by_id=body.reported_by_id,
                winner_id=body.winner_id,
                loser_id=body.loser_id,
            )
        )

    @app.get("/v1/leagues/{league_id}/matches")
    async def list_matches(league_id: str) -> dict:
        return await runtime.route_policy.data_response(lambda: runtime.store.league_matches(league_id))

    @app.post("/v1/leagues/{league_id}/matches/{match_id}/confirm")
    async def confirm_match(league_id: str, match_id: str, body: ActorRequest) -> dict:
        return await runtime.route_policy.data_response(lambda: runtime.store.confirm_match(match_id, body.actor_id))

    @app.post("/v1/leagues/{league_id}/matches/{match_id}/dispute")
    async def dispute_match(league_id: str, match_id: str, body: ActorRequest) -> dict:
        return await runtime.route_policy.data_response(
            lambda: runtime.store.dispute_match(match_id, body.actor_id, body.note)
        )

    @app.post("/v1/leagues/{league_id}/matches/{match_id}/reject")
    async def reject_match(league_id: str, match_id: str, body: ActorRequest) -> dict:
        return await runtime.route_policy.data_response(lambda: runtime.store.reject_match(match_id, body.actor_id))

    @app.get("/v1/public/leagues/{slug}")
    async def public_league(slug: str) -> dict:
        return await runtime.route_policy.data_response(lambda: runtime.store.public_leaderboard(slug))

    @app.get("/v1/leagues/{league_id}/players/{user_id}/rating-history")
    async def rating_history(league_id: str, user_id: str) -> dict:
        return await runtime.route_policy.data_response(
            lambda: runtime.store.player_rating_history(league_id, user_id)
        )

    return app

app = create_app()
