from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.auth_session import AuthSession
from app.config import Settings, settings
from app.db.postgres_store import PostgresStore
from app.domain import RankKitStore
from app.route_policy import RoutePolicy


@dataclass(frozen=True)
class RankKitRuntime:
    store: object
    auth_session: AuthSession
    route_policy: RoutePolicy


def create_runtime(app_settings: Settings = settings) -> RankKitRuntime:
    store = create_store(app_settings)
    return RankKitRuntime(
        store=store,
        auth_session=AuthSession(),
        route_policy=RoutePolicy(),
    )


def create_store(app_settings: Settings):
    if app_settings.store_backend == "local":
        return RankKitStore(app_settings.local_data_path)
    if app_settings.store_backend == "postgres":
        return PostgresRuntimeStore(app_settings.database_url)
    raise ValueError("STORE_BACKEND must be 'local' or 'postgres'.")


class PostgresRuntimeStore:
    """Runtime Store adapter that opens a Postgres connection for each operation."""

    def __init__(self, database_url: str, engine: AsyncEngine | None = None) -> None:
        self.database_url = database_url
        self.engine = engine or create_async_engine(database_url)

    async def close(self) -> None:
        await self.engine.dispose()

    async def _run(self, operation):
        async with self.engine.begin() as connection:
            store = PostgresStore(connection)
            return await operation(store)

    async def sync_user(self, email: str, name: str | None = None, image: str | None = None):
        return await self._run(lambda store: store.sync_user(email, name, image))

    async def get_user(self, user_id: str):
        return await self._run(lambda store: store.get_user(user_id))

    async def create_league(
        self,
        owner_id: str,
        name: str,
        slug: str,
        description: str | None = None,
        is_public: bool = True,
    ):
        return await self._run(
            lambda store: store.create_league(owner_id, name, slug, description, is_public)
        )

    async def list_leagues(self, user_id: str | None = None):
        return await self._run(lambda store: store.list_leagues(user_id))

    async def get_league(self, league_id: str):
        return await self._run(lambda store: store.get_league(league_id))

    async def leaderboard(self, league_id: str):
        return await self._run(lambda store: store.leaderboard(league_id))

    async def member_summaries(self, league_id: str):
        return await self._run(lambda store: store.member_summaries(league_id))

    async def create_invite(self, league_id: str, admin_id: str):
        return await self._run(lambda store: store.create_invite(league_id, admin_id))

    async def accept_invite(self, token: str, user_id: str):
        return await self._run(lambda store: store.accept_invite(token, user_id))

    async def log_match(
        self,
        league_id: str,
        reported_by_id: str,
        winner_id: str,
        loser_id: str,
        played_at=None,
    ):
        return await self._run(
            lambda store: store.log_match(league_id, reported_by_id, winner_id, loser_id, played_at)
        )

    async def league_matches(self, league_id: str):
        return await self._run(lambda store: store.league_matches(league_id))

    async def confirm_match(self, match_id: str, actor_id: str):
        return await self._run(lambda store: store.confirm_match(match_id, actor_id))

    async def dispute_match(self, match_id: str, actor_id: str, note: str | None = None):
        return await self._run(lambda store: store.dispute_match(match_id, actor_id, note))

    async def reject_match(self, match_id: str, admin_id: str):
        return await self._run(lambda store: store.reject_match(match_id, admin_id))

    async def public_leaderboard(self, slug: str):
        return await self._run(lambda store: store.public_leaderboard(slug))

    async def player_rating_history(self, league_id: str, user_id: str):
        return await self._run(lambda store: store.player_rating_history(league_id, user_id))
