from __future__ import annotations

import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings


EXPECTED_TABLES = {
    "alembic_version",
    "invites",
    "league_members",
    "leagues",
    "matches",
    "rating_history",
    "users",
}


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


async def main() -> None:
    version, tables = await check_database()
    print(f"Alembic version: {version}")
    print("Tables:")
    for table in sorted(tables):
        print(f"- {table}")


if __name__ == "__main__":
    asyncio.run(main())
