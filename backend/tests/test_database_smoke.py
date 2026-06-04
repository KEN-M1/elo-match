import json
import unittest
from pathlib import Path

from app.db.smoke import EXPECTED_TABLES, check_write_round_trip


REPO_ROOT = Path(__file__).resolve().parents[2]


class DatabaseSmokeTests(unittest.TestCase):
    def test_expected_tables_match_rankkit_schema(self) -> None:
        self.assertEqual(
            {
                "alembic_version",
                "invites",
                "league_members",
                "leagues",
                "matches",
                "rating_history",
                "users",
            },
            EXPECTED_TABLES,
        )

    def test_root_script_exposes_database_smoke_check(self) -> None:
        package_json = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))

        self.assertEqual(
            "powershell -ExecutionPolicy Bypass -File scripts/smoke-db.ps1",
            package_json["scripts"]["db:smoke"],
        )

    def test_smoke_script_runs_backend_module(self) -> None:
        script = (REPO_ROOT / "scripts" / "smoke-db.ps1").read_text(encoding="utf-8")

        self.assertIn("-m app.db.smoke", script)
        self.assertIn("if ($LASTEXITCODE -ne 0)", script)

    def test_write_round_trip_rolls_back_smoke_data(self) -> None:
        connection = FakeConnection(count=1)

        result = run(check_write_round_trip(connection))

        self.assertEqual("rankkit-smoke-user", result.user_id)
        self.assertEqual("rankkit-smoke-league", result.league_slug)
        self.assertEqual(5, len(connection.executed_statements))
        self.assertTrue(connection.transaction.rolled_back)


def run(coroutine):
    import asyncio

    return asyncio.run(coroutine)


class FakeResult:
    def __init__(self, count: int) -> None:
        self.count = count

    def scalar_one(self) -> int:
        return self.count


class FakeTransaction:
    def __init__(self) -> None:
        self.rolled_back = False

    async def rollback(self) -> None:
        self.rolled_back = True


class FakeConnection:
    def __init__(self, count: int) -> None:
        self.count = count
        self.transaction = FakeTransaction()
        self.executed_statements = []

    async def begin(self) -> FakeTransaction:
        return self.transaction

    async def execute(self, statement) -> FakeResult:
        self.executed_statements.append(statement)
        return FakeResult(self.count)


if __name__ == "__main__":
    unittest.main()
