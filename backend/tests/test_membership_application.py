import unittest

from app.domain import Invite, League
from app.membership import MembershipApplication


class MembershipApplicationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.application = MembershipApplication()
        self.league = League(id="league-1", name="League", slug="league", owner_id="owner")

    def test_creates_owner_membership_with_initial_rating_history(self) -> None:
        member, history = self.application.create_owner_membership(self.league)

        self.assertEqual("owner", member.user_id)
        self.assertEqual("admin", member.role)
        self.assertEqual(1000, member.rating)
        self.assertEqual("owner", history.user_id)
        self.assertEqual("league-1", history.league_id)
        self.assertIsNone(history.match_id)
        self.assertEqual(1000, history.rating)
        self.assertEqual(member.joined_at, history.recorded_at)

    def test_accepts_invite_and_creates_member_history_pair(self) -> None:
        invite = Invite(token="token", league_id=self.league.id, created_by_id="owner")

        member, history = self.application.accept_invite(invite, self.league, "player")

        self.assertEqual("player", member.user_id)
        self.assertEqual("member", member.role)
        self.assertEqual(1000, member.rating)
        self.assertEqual("player", invite.accepted_by_id)
        self.assertEqual(member.joined_at, invite.accepted_at)
        self.assertEqual(member.joined_at, history.recorded_at)


if __name__ == "__main__":
    unittest.main()
