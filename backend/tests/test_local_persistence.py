import tempfile
import unittest
from pathlib import Path

from app.domain import MatchStatus, RankKitStore


class LocalPersistenceTests(unittest.TestCase):
    def test_store_hydrates_league_match_and_rating_history_from_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rankkit.json"

            first_store = RankKitStore(path)
            owner = first_store.sync_user("owner@example.com", "Owner")
            opponent = first_store.sync_user("opponent@example.com", "Opponent")
            league = first_store.create_league(owner.id, "Friday Ladder", "friday-ladder")
            invite = first_store.create_invite(league.id, owner.id)
            first_store.accept_invite(invite.token, opponent.id)
            match = first_store.log_match(league.id, owner.id, owner.id, opponent.id)
            first_store.confirm_match(match.id, opponent.id)

            hydrated_store = RankKitStore(path)
            hydrated_league = hydrated_store.get_league(league.id)
            hydrated_match = hydrated_store._require_match(match.id)
            leaderboard = hydrated_store.leaderboard(league.id)
            owner_history = hydrated_store.player_rating_history(league.id, owner.id)

            self.assertEqual(hydrated_league.slug, "friday-ladder")
            self.assertEqual(hydrated_match.status, MatchStatus.COMPLETED)
            self.assertEqual(leaderboard[0].user_id, owner.id)
            self.assertEqual(leaderboard[0].rating, 1016)
            self.assertEqual(owner_history[-1].match_id, match.id)


if __name__ == "__main__":
    unittest.main()
