from __future__ import annotations

import asyncio
from dataclasses import dataclass

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.db.postgres_store import PostgresStore
from app.db.schema import league_members, leagues, rating_history


EXPECTED_TABLES = {
    "alembic_version",
    "invites",
    "league_members",
    "leagues",
    "matches",
    "rating_history",
    "users",
}


@dataclass(frozen=True)
class WriteSmokeResult:
    user_id: str
    league_slug: str
    member_count: int
    match_status: str
    confirmed_match_status: str
    winner_rating: float
    loser_rating: float
    rating_history_count: int


async def check_database() -> tuple[str, set[str]]:
    engine = create_async_engine(settings.database_url)
    try:
        async with engine.connect() as connection:
            version = (
                await connection.execute(text("select version_num from alembic_version"))
            ).scalar_one()
            tables = {
                row[0]
                for row in await connection.execute(
                    text(
                        "select table_name "
                        "from information_schema.tables "
                        "where table_schema = 'public'"
                    )
                )
            }
    finally:
        await engine.dispose()

    missing_tables = EXPECTED_TABLES - tables
    if missing_tables:
        names = ", ".join(sorted(missing_tables))
        raise RuntimeError(f"RankKit database is missing tables: {names}")

    return str(version), tables


async def check_write_round_trip(connection) -> WriteSmokeResult:
    smoke_slug = "rankkit-smoke-league"
    store = PostgresStore(connection)

    transaction = await connection.begin()
    try:
        user = await store.sync_user(
            email="rankkit-smoke@example.com",
            name="RankKit Smoke",
        )
        opponent = await store.sync_user(
            email="rankkit-smoke-opponent@example.com",
            name="RankKit Smoke Opponent",
        )
        league = await store.create_league(
            owner_id=user.id,
            name="RankKit Smoke League",
            slug=smoke_slug,
        )
        invite = await store.create_invite(league.id, user.id)
        await store.accept_invite(invite.token, opponent.id)
        match = await store.log_match(
            league_id=league.id,
            reported_by_id=user.id,
            winner_id=user.id,
            loser_id=opponent.id,
        )
        league_matches = await store.league_matches(league.id)
        fetched = await store.get_league(league.id)
        opponent_leagues = await store.list_leagues(opponent.id)
        count = (
            await connection.execute(
                select(func.count()).select_from(leagues).where(leagues.c.slug == smoke_slug)
            )
        ).scalar_one()
        ratings = (
            await connection.execute(
                select(league_members.c.rating).where(league_members.c.league_id == league.id)
            )
        ).scalars().all()
        if (
            count != 1
            or fetched.slug != smoke_slug
            or len(opponent_leagues) != 1
            or len(league_matches) != 1
            or league_matches[0].id != match.id
            or match.status != "PENDING"
            or any(rating != 1000.0 for rating in ratings)
        ):
            raise RuntimeError("RankKit database smoke write could not read back the pending match flow.")
        confirmed = await store.confirm_match(match.id, opponent.id)
        leaderboard = await store.leaderboard(league.id)
        history_count = (
            await connection.execute(
                select(func.count())
                .select_from(rating_history)
                .where(rating_history.c.league_id == league.id)
            )
        ).scalar_one()
        if (
            confirmed.status != "COMPLETED"
            or len(leaderboard) != 2
            or leaderboard[0].user_id != user.id
            or leaderboard[0].rating != 1016.0
            or leaderboard[1].rating != 984.0
            or history_count != 4
        ):
            raise RuntimeError("RankKit database smoke write could not confirm and rate the match.")
        return WriteSmokeResult(
            user_id=user.id,
            league_slug=fetched.slug,
            member_count=len(opponent_leagues) + 1,
            match_status=match.status,
            confirmed_match_status=confirmed.status,
            winner_rating=leaderboard[0].rating,
            loser_rating=leaderboard[1].rating,
            rating_history_count=history_count,
        )
    finally:
        await transaction.rollback()


async def main() -> None:
    version, tables = await check_database()
    print(f"Alembic version: {version}")
    print("Tables:")
    for table in sorted(tables):
        print(f"- {table}")

    engine = create_async_engine(settings.database_url)
    try:
        async with engine.connect() as connection:
            write_result = await check_write_round_trip(connection)
    finally:
        await engine.dispose()
    print(f"Write smoke rolled back: {write_result.league_slug}")
    print(f"Write smoke members: {write_result.member_count}")
    print(f"Write smoke match status: {write_result.match_status}")
    print(f"Write smoke confirmed status: {write_result.confirmed_match_status}")
    print(f"Write smoke ratings: {write_result.winner_rating} / {write_result.loser_rating}")
    print(f"Write smoke rating history rows: {write_result.rating_history_count}")


if __name__ == "__main__":
    asyncio.run(main())
