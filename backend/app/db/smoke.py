from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.db.schema import league_members, leagues, rating_history, users


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
    smoke_user_id = "rankkit-smoke-user"
    smoke_league_id = "rankkit-smoke-league"
    smoke_slug = "rankkit-smoke-league"
    now = datetime.now(timezone.utc)

    transaction = await connection.begin()
    try:
        await connection.execute(
            users.insert().values(
                id=smoke_user_id,
                email="rankkit-smoke@example.com",
                name="RankKit Smoke",
            )
        )
        await connection.execute(
            leagues.insert().values(
                id=smoke_league_id,
                name="RankKit Smoke League",
                slug=smoke_slug,
                owner_id=smoke_user_id,
                is_public=True,
                default_k=32,
                initial_rating=1000,
                rating_floor=100,
            )
        )
        await connection.execute(
            league_members.insert().values(
                league_id=smoke_league_id,
                user_id=smoke_user_id,
                role="admin",
                rating=1000,
                wins=0,
                losses=0,
                joined_at=now,
            )
        )
        await connection.execute(
            rating_history.insert().values(
                user_id=smoke_user_id,
                league_id=smoke_league_id,
                match_id=None,
                rating=1000,
                recorded_at=now,
            )
        )
        count = (
            await connection.execute(
                select(func.count()).select_from(leagues).where(leagues.c.slug == smoke_slug)
            )
        ).scalar_one()
        if count != 1:
            raise RuntimeError("RankKit database smoke write could not read back the League.")
        return WriteSmokeResult(user_id=smoke_user_id, league_slug=smoke_slug)
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


if __name__ == "__main__":
    asyncio.run(main())
