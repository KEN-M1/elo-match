import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class PostgresMatchPersistenceTests(unittest.TestCase):
    def test_postgres_store_delegates_match_work_to_persistence_module(self) -> None:
        persistence_path = REPO_ROOT / "backend" / "app" / "db" / "match_persistence.py"
        store_path = REPO_ROOT / "backend" / "app" / "db" / "postgres_store.py"

        self.assertTrue(persistence_path.exists())
        persistence_source = persistence_path.read_text(encoding="utf-8")
        store_source = store_path.read_text(encoding="utf-8")

        self.assertIn("class PostgresMatchPersistence", persistence_source)
        for expected in [
            "async def log(",
            "async def list_for_league(",
            "async def confirm(",
            "async def dispute(",
            "async def reject(",
        ]:
            self.assertIn(expected, persistence_source)

        self.assertIn("PostgresMatchPersistence", store_source)
        self.assertIn("self.match_persistence", store_source)
        for expected in [
            "self.match_persistence.log(",
            "self.match_persistence.list_for_league(",
            "self.match_persistence.confirm(",
            "self.match_persistence.dispute(",
            "self.match_persistence.reject(",
        ]:
            self.assertIn(expected, store_source)


if __name__ == "__main__":
    unittest.main()
