import unittest

from app.domain import MatchStatus, RankKitError, RankKitStore


class RankKitWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = RankKitStore()
        self.owner = self.store.sync_user("owner@example.com", "Owner")
        self.player = self.store.sync_user("player@example.com", "Player")
        self.league = self.store.create_league(
            owner_id=self.owner.id,
            name="Friday Ladder",
            slug="friday-ladder",
        )

    def test_owner_can_invite_and_player_can_accept(self) -> None:
        invite = self.store.create_invite(self.league.id, self.owner.id)
        member = self.store.accept_invite(invite.token, self.player.id)

        self.assertEqual(member.league_id, self.league.id)
        self.assertEqual(member.user_id, self.player.id)
        self.assertEqual(member.rating, 1000)

    def test_logged_match_waits_for_confirmation_without_rating_change(self) -> None:
        self._join_player()

        match = self.store.log_match(
            league_id=self.league.id,
            reported_by_id=self.owner.id,
            winner_id=self.owner.id,
            loser_id=self.player.id,
        )
        ratings = {member.user_id: member.rating for member in self.store.leaderboard(self.league.id)}

        self.assertEqual(match.status, MatchStatus.PENDING)
        self.assertEqual(ratings[self.owner.id], 1000)
        self.assertEqual(ratings[self.player.id], 1000)

    def test_opponent_confirmation_updates_ratings_and_history(self) -> None:
        self._join_player()
        match = self.store.log_match(
            league_id=self.league.id,
            reported_by_id=self.owner.id,
            winner_id=self.owner.id,
            loser_id=self.player.id,
        )

        confirmed = self.store.confirm_match(match.id, self.player.id)
        leaderboard = self.store.leaderboard(self.league.id)
        owner_history = self.store.player_rating_history(self.league.id, self.owner.id)

        self.assertEqual(confirmed.status, MatchStatus.COMPLETED)
        self.assertEqual(leaderboard[0].user_id, self.owner.id)
        self.assertEqual(leaderboard[0].rating, 1016)
        self.assertEqual(leaderboard[1].rating, 984)
        self.assertEqual(owner_history[-1].match_id, match.id)
        self.assertEqual(owner_history[-1].rating, 1016)

    def test_reporter_cannot_confirm_own_match(self) -> None:
        self._join_player()
        match = self.store.log_match(
            league_id=self.league.id,
            reported_by_id=self.player.id,
            winner_id=self.player.id,
            loser_id=self.owner.id,
        )

        with self.assertRaisesRegex(RankKitError, "Reporter cannot confirm"):
            self.store.confirm_match(match.id, self.player.id)

    def test_opponent_can_dispute_and_admin_can_reject(self) -> None:
        self._join_player()
        match = self.store.log_match(
            league_id=self.league.id,
            reported_by_id=self.owner.id,
            winner_id=self.owner.id,
            loser_id=self.player.id,
        )

        disputed = self.store.dispute_match(match.id, self.player.id, "Score was wrong")
        rejected = self.store.reject_match(match.id, self.owner.id)

        self.assertEqual(disputed.status, MatchStatus.REJECTED)
        self.assertEqual(rejected.status, MatchStatus.REJECTED)

    def test_public_leaderboard_requires_public_league(self) -> None:
        self._join_player()
        league, members = self.store.public_leaderboard("friday-ladder")

        self.assertEqual(league.id, self.league.id)
        self.assertEqual(len(members), 2)

    def _join_player(self) -> None:
        invite = self.store.create_invite(self.league.id, self.owner.id)
        self.store.accept_invite(invite.token, self.player.id)


if __name__ == "__main__":
    unittest.main()
