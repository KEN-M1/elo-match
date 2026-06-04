import json
import unittest
from pathlib import Path

from app.db.smoke import EXPECTED_TABLES


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


if __name__ == "__main__":
    unittest.main()
