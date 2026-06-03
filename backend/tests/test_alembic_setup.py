import configparser
import re
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]


class AlembicSetupTests(unittest.TestCase):
    def test_alembic_config_points_to_backend_migrations(self) -> None:
        config = configparser.ConfigParser()
        config.read(BACKEND_ROOT / "alembic.ini")

        self.assertEqual("alembic", config.get("alembic", "script_location"))
        self.assertEqual(
            "postgresql+asyncpg://rankkit:rankkit@localhost:5432/rankkit",
            config.get("alembic", "sqlalchemy.url"),
        )

    def test_alembic_env_uses_rankkit_schema_metadata(self) -> None:
        env_py = (BACKEND_ROOT / "alembic" / "env.py").read_text(encoding="utf-8")

        self.assertIn("from app.db.schema import metadata", env_py)
        self.assertIn("target_metadata = metadata", env_py)

    def test_initial_revision_creates_domain_tables(self) -> None:
        migration = (
            BACKEND_ROOT / "alembic" / "versions" / "0001_initial_rankkit_schema.py"
        ).read_text(encoding="utf-8")

        self.assertIn('revision = "0001"', migration)
        self.assertIn("down_revision = None", migration)
        for table_name in [
            "users",
            "leagues",
            "league_members",
            "invites",
            "matches",
            "rating_history",
        ]:
            self.assertRegex(migration, rf'op\.create_table\(\s*"{table_name}"')


if __name__ == "__main__":
    unittest.main()
