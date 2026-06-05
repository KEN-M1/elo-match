import unittest

from app.domain import League, LeagueMember, Match, MatchStatus, RankKitError
from app.match_lifecycle import MatchLifecycleRules, MatchRatingApplication


class MatchLifecycleRulesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rules = MatchLifecycleRules()

    def test_reporter_must_be_a_match_participant(self) -> None:
        with self.assertRaisesRegex(RankKitError, "Reporter must be one of the match participants"):
            self.rules.ensure_loggable(
                reported_by_id="spectator",
                winner_id="winner",
                loser_id="loser",
            )

    def test_reporter_cannot_confirm_without_admin_role(self) -> None:
        match = Match(
            id="match-1",
            league_id="league-1",
            winner_id="winner",
            loser_id="loser",
            reported_by_id="winner",
        )

        with self.assertRaisesRegex(RankKitError, "Reporter cannot confirm"):
            self.rules.ensure_confirmable(match, actor_id="winner", actor_is_admin=False)

    def test_admin_can_confirm_a_disputed_match(self) -> None:
        match = Match(
            id="match-1",
            league_id="league-1",
            winner_id="winner",
            loser_id="loser",
            reported_by_id="winner",
            status=MatchStatus.DISPUTED,
        )

        self.rules.ensure_confirmable(match, actor_id="winner", actor_is_admin=True)


class MatchRatingApplicationTests(unittest.TestCase):
    def test_confirmed_match_applies_ratings_and_history_entries(self) -> None:
        league = League(id="league-1", name="League", slug="league", owner_id="winner")
        winner = LeagueMember(league_id=league.id, user_id="winner")
        loser = LeagueMember(league_id=league.id, user_id="loser")
        match = Match(
            id="match-1",
            league_id=league.id,
            winner_id=winner.user_id,
            loser_id=loser.user_id,
            reported_by_id=winner.user_id,
        )

        history = MatchRatingApplication().apply_confirmed_match(
            league=league,
            match=match,
            winner=winner,
            loser=loser,
            confirmed_by_id=loser.user_id,
        )

        self.assertEqual(MatchStatus.COMPLETED, match.status)
        self.assertEqual(loser.user_id, match.confirmed_by_id)
        self.assertEqual(1016, winner.rating)
        self.assertEqual(984, loser.rating)
        self.assertEqual(1, winner.wins)
        self.assertEqual(1, loser.losses)
        self.assertEqual([winner.user_id, loser.user_id], [entry.user_id for entry in history])
        self.assertEqual(["match-1", "match-1"], [entry.match_id for entry in history])


if __name__ == "__main__":
    unittest.main()
