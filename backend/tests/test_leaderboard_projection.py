import unittest
from datetime import datetime, timezone

from app.domain import LeagueMember, User
from app.leaderboard import LeaderboardProjection


class LeaderboardProjectionTests(unittest.TestCase):
    def test_ranks_members_by_rating_then_join_time(self) -> None:
        first_joined = datetime(2026, 1, 1, tzinfo=timezone.utc)
        second_joined = datetime(2026, 1, 2, tzinfo=timezone.utc)
        lower_rated = LeagueMember("league", "lower", rating=900, joined_at=first_joined)
        early_high = LeagueMember("league", "early", rating=1000, joined_at=first_joined)
        late_high = LeagueMember("league", "late", rating=1000, joined_at=second_joined)

        ranked = LeaderboardProjection().rank_members([late_high, lower_rated, early_high])

        self.assertEqual(["early", "late", "lower"], [member.user_id for member in ranked])

    def test_builds_member_summaries_from_ranked_members(self) -> None:
        projection = LeaderboardProjection()
        members = [
            LeagueMember("league", "winner", rating=1016, wins=1),
            LeagueMember("league", "loser", rating=984, losses=1),
        ]
        users = {
            "winner": User(id="winner", email="winner@example.com", name="Winner"),
            "loser": User(id="loser", email="loser@example.com", name="Loser"),
        }

        summaries = projection.member_summaries(members, users)

        self.assertEqual(["winner@example.com", "loser@example.com"], [item.email for item in summaries])
        self.assertEqual([1016, 984], [item.rating for item in summaries])


if __name__ == "__main__":
    unittest.main()
