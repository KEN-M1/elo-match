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


if __name__ == "__main__":
    unittest.main()
