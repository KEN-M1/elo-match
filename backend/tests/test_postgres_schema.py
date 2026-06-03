import unittest

from app.db.schema import metadata


class PostgresSchemaTests(unittest.TestCase):
    def test_schema_has_rankkit_domain_tables(self) -> None:
        expected_tables = {
            "users",
            "leagues",
            "league_members",
            "invites",
            "matches",
            "rating_history",
        }

        self.assertEqual(expected_tables, set(metadata.tables))

    def test_match_and_rating_history_tables_preserve_confirmation_rules(self) -> None:
        matches = metadata.tables["matches"]
        rating_history = metadata.tables["rating_history"]

        for column_name in [
            "winner_id",
            "loser_id",
            "reported_by_id",
            "status",
            "confirmed_by_id",
            "disputed_by_id",
            "rating_result",
        ]:
            self.assertIn(column_name, matches.columns)

        for column_name in ["user_id", "league_id", "match_id", "rating", "recorded_at"]:
            self.assertIn(column_name, rating_history.columns)

        self.assertFalse(matches.columns["winner_id"].nullable)
        self.assertFalse(matches.columns["loser_id"].nullable)
        self.assertFalse(matches.columns["reported_by_id"].nullable)
        self.assertFalse(matches.columns["status"].nullable)
        self.assertFalse(rating_history.columns["rating"].nullable)


if __name__ == "__main__":
    unittest.main()
