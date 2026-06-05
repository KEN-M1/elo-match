import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class ReadmeDocsTests(unittest.TestCase):
    def test_readme_documents_local_demo_and_database_smoke_paths(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        for expected in [
            "## Demo Readiness Checklist",
            "http://localhost:3000/demo",
            "pnpm run test:e2e",
            "## Google OAuth Setup",
            "## Postgres Adapter Smoke",
            "pnpm run db:smoke",
            "DISPUTED",
            "REJECTED",
        ]:
            self.assertIn(expected, readme)

    def test_env_example_documents_local_and_production_runtime_settings(self) -> None:
        env_example = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")

        for expected in [
            "ENVIRONMENT=local",
            "STORE_BACKEND=local",
            "NEXT_PUBLIC_API_URL=http://localhost:8002",
            "AUTH_REQUIRED=false",
            "ENVIRONMENT=production",
            "STORE_BACKEND=postgres",
            "ALLOWED_ORIGINS=https://your-web-app.example",
            "JWT_SECRET=replace-with-the-same-32-character-or-longer-secret-used-by-nextauth",
            "NEXTAUTH_SECRET=replace-with-the-same-32-character-or-longer-secret-used-by-backend",
            "AUTH_REQUIRED=true",
        ]:
            self.assertIn(expected, env_example)


if __name__ == "__main__":
    unittest.main()
