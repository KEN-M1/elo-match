from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.auth import verify_bearer_token
from app.config import settings
from app.domain import RankKitError, RankKitStore

store = RankKitStore(settings.local_data_path)


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


def create_app() -> FastAPI:
    app = FastAPI(
        title="RankKit API",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
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
    def sync_user(body: SyncUserRequest) -> dict:
        return {"data": store.sync_user(body.email, body.name, body.image)}

    @app.get("/v1/auth/me")
    def me(
        authorization: str | None = Header(default=None),
        x_rankkit_user: str | None = Header(default=None),
    ) -> dict:
        principal = _response(lambda: verify_bearer_token(authorization))["data"]
        if principal is not None:
            return {
                "data": store.sync_user(
                    email=principal.email,
                    name=principal.name,
                    image=principal.image,
                )
            }
        if not x_rankkit_user:
            raise HTTPException(status_code=401, detail="Missing user header for local MVP.")
        user = store.users.get(x_rankkit_user)
        if user is None:
            raise HTTPException(status_code=404, detail="User was not found.")
        return {"data": user}

    @app.post("/v1/leagues")
    def create_league(body: CreateLeagueRequest) -> dict:
        return _response(
            lambda: store.create_league(
                owner_id=body.owner_id,
                name=body.name,
                slug=body.slug,
                description=body.description,
                is_public=body.is_public,
            )
        )

    @app.get("/v1/leagues")
    def list_leagues(user_id: str | None = None) -> dict:
        return _response(lambda: store.list_leagues(user_id))

    @app.get("/v1/leagues/{league_id}")
    def get_league(league_id: str) -> dict:
        return _response(lambda: store.get_league(league_id))

    @app.get("/v1/leagues/{league_id}/leaderboard")
    def leaderboard(league_id: str) -> dict:
        return _response(lambda: store.leaderboard(league_id))

    @app.get("/v1/leagues/{league_id}/members")
    def members(league_id: str) -> dict:
        return _response(lambda: store.member_summaries(league_id))

    @app.post("/v1/leagues/{league_id}/invites")
    def create_invite(league_id: str, body: CreateInviteRequest) -> dict:
        return _response(lambda: store.create_invite(league_id, body.admin_id))

    @app.post("/v1/invites/{token}/accept")
    def accept_invite(token: str, body: AcceptInviteRequest) -> dict:
        return _response(lambda: store.accept_invite(token, body.user_id))

    @app.post("/v1/leagues/{league_id}/matches")
    def log_match(league_id: str, body: LogMatchRequest) -> dict:
        return _response(
            lambda: store.log_match(
                league_id=league_id,
                reported_by_id=body.reported_by_id,
                winner_id=body.winner_id,
                loser_id=body.loser_id,
            )
        )

    @app.get("/v1/leagues/{league_id}/matches")
    def list_matches(league_id: str) -> dict:
        return _response(lambda: store.league_matches(league_id))

    @app.post("/v1/leagues/{league_id}/matches/{match_id}/confirm")
    def confirm_match(league_id: str, match_id: str, body: ActorRequest) -> dict:
        return _response(lambda: store.confirm_match(match_id, body.actor_id))

    @app.post("/v1/leagues/{league_id}/matches/{match_id}/dispute")
    def dispute_match(league_id: str, match_id: str, body: ActorRequest) -> dict:
        return _response(lambda: store.dispute_match(match_id, body.actor_id, body.note))

    @app.post("/v1/leagues/{league_id}/matches/{match_id}/reject")
    def reject_match(league_id: str, match_id: str, body: ActorRequest) -> dict:
        return _response(lambda: store.reject_match(match_id, body.actor_id))

    @app.get("/v1/public/leagues/{slug}")
    def public_league(slug: str) -> dict:
        return _response(lambda: store.public_leaderboard(slug))

    @app.get("/v1/leagues/{league_id}/players/{user_id}/rating-history")
    def rating_history(league_id: str, user_id: str) -> dict:
        return _response(lambda: store.player_rating_history(league_id, user_id))

    return app


def _response(callback):
    try:
        return {"data": callback()}
    except RankKitError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


app = create_app()
