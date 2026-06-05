import unittest

from app.db.postgres_store import PostgresStore
from app.domain import RankKitStore


class PostgresStoreTests(unittest.TestCase):
    def test_store_exposes_first_persistence_slice_interface(self) -> None:
        expected_methods = {
            "accept_invite",
            "confirm_match",
            "create_invite",
            "create_league",
            "dispute_match",
            "get_league",
            "league_matches",
            "leaderboard",
            "list_leagues",
            "log_match",
            "member_summaries",
            "player_rating_history",
            "public_leaderboard",
            "reject_match",
            "sync_user",
        }

        self.assertTrue(expected_methods.issubset(set(dir(PostgresStore))))
        self.assertTrue(expected_methods.issubset(set(dir(RankKitStore))))


if __name__ == "__main__":
    unittest.main()
