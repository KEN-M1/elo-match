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
        self.assertEqual(
            "powershell -ExecutionPolicy Bypass -File scripts/verify-db.ps1",
            scripts["db:verify"],
        )

    def test_root_scripts_expose_production_runtime_commands(self) -> None:
        package_json = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))
        scripts = package_json["scripts"]

        self.assertEqual(
            "powershell -ExecutionPolicy Bypass -File scripts/start-backend.ps1",
            scripts["start:backend"],
        )
        self.assertEqual("pnpm --filter @rankkit/web build", scripts["build:web"])
        self.assertEqual("pnpm --filter @rankkit/web start", scripts["start:web"])

        web_package_json = json.loads((REPO_ROOT / "apps" / "web" / "package.json").read_text(encoding="utf-8"))
        self.assertEqual("next build", web_package_json["scripts"]["build"])
        self.assertEqual("next start", web_package_json["scripts"]["start"])

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
        for script_name in ["dev-db.ps1", "migrate-db.ps1", "migration-sql.ps1", "verify-db.ps1"]:
            script = (REPO_ROOT / "scripts" / script_name).read_text(encoding="utf-8")
            self.assertIn("if ($LASTEXITCODE -ne 0)", script)

    def test_backend_start_script_runs_uvicorn_without_reload(self) -> None:
        script = (REPO_ROOT / "scripts" / "start-backend.ps1").read_text(encoding="utf-8")

        self.assertIn("app.main:app", script)
        self.assertIn("--host 0.0.0.0", script)
        self.assertIn("--port $Port", script)
        self.assertNotIn("--reload", script)

    def test_ci_workflow_verifies_app_build_and_postgres_smoke(self) -> None:
        workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

        for expected in [
            "windows-latest",
            "ubuntu-latest",
            "postgres:16-alpine",
            "pnpm test",
            "pnpm run build:web",
            "pnpm run test:e2e",
            "python -m alembic upgrade head",
            "python -m app.db.smoke",
        ]:
            self.assertIn(expected, workflow)

    def test_verify_db_script_checks_alembic_version_and_tables(self) -> None:
        script = (REPO_ROOT / "scripts" / "verify-db.ps1").read_text(encoding="utf-8")

        self.assertIn("select version_num from alembic_version", script)
        self.assertIn("information_schema.tables", script)


if __name__ == "__main__":
    unittest.main()
