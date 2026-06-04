import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class LocalDatabaseToolingTests(unittest.TestCase):
    def test_root_scripts_expose_postgres_start_and_migration_commands(self) -> None:
        package_json = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))
        scripts = package_json["scripts"]

        self.assertEqual(
            "powershell -ExecutionPolicy Bypass -File scripts/dev-db.ps1",
            scripts["dev:db"],
        )
        self.assertEqual(
            "powershell -ExecutionPolicy Bypass -File scripts/migrate-db.ps1",
            scripts["db:migrate"],
        )
        self.assertEqual(
            "powershell -ExecutionPolicy Bypass -File scripts/migration-sql.ps1",
            scripts["db:sql"],
        )

    def test_compose_file_defines_rankkit_postgres(self) -> None:
        compose = (REPO_ROOT / "compose.yaml").read_text(encoding="utf-8")

        self.assertIn("rankkit-postgres", compose)
        self.assertIn("POSTGRES_DB: rankkit", compose)
        self.assertIn("POSTGRES_USER: rankkit", compose)
        self.assertIn("POSTGRES_PASSWORD: rankkit", compose)
        self.assertIn("5432:5432", compose)

    def test_database_scripts_use_backend_alembic(self) -> None:
        migrate_script = (REPO_ROOT / "scripts" / "migrate-db.ps1").read_text(encoding="utf-8")
        sql_script = (REPO_ROOT / "scripts" / "migration-sql.ps1").read_text(encoding="utf-8")

        self.assertIn("-m alembic upgrade head", migrate_script)
        self.assertIn("-m alembic upgrade head --sql", sql_script)

    def test_database_scripts_propagate_native_command_failures(self) -> None:
        for script_name in ["dev-db.ps1", "migrate-db.ps1", "migration-sql.ps1"]:
            script = (REPO_ROOT / "scripts" / script_name).read_text(encoding="utf-8")
            self.assertIn("if ($LASTEXITCODE -ne 0)", script)


if __name__ == "__main__":
    unittest.main()
