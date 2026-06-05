from __future__ import annotations

from datetime import datetime, timezone

from app.domain import Invite, League, LeagueMember, RatingHistoryEntry


class MembershipApplication:
    """Applies League Membership creation and initial Rating History effects."""

    def create_owner_membership(
        self,
        league: League,
        joined_at: datetime | None = None,
    ) -> tuple[LeagueMember, RatingHistoryEntry]:
        joined = joined_at or datetime.now(timezone.utc)
        member = LeagueMember(
            league_id=league.id,
            user_id=league.owner_id,
            role="admin",
            rating=league.initial_rating,
            joined_at=joined,
        )
        return member, self._initial_history(member)

    def accept_invite(
        self,
        invite: Invite,
        league: League,
        user_id: str,
        accepted_at: datetime | None = None,
    ) -> tuple[LeagueMember, RatingHistoryEntry]:
        accepted = accepted_at or datetime.now(timezone.utc)
        member = LeagueMember(
            league_id=league.id,
            user_id=user_id,
            rating=league.initial_rating,
            joined_at=accepted,
        )
        invite.accepted_by_id = user_id
        invite.accepted_at = accepted
        return member, self._initial_history(member)

    def _initial_history(self, member: LeagueMember) -> RatingHistoryEntry:
        return RatingHistoryEntry(
            user_id=member.user_id,
            league_id=member.league_id,
            match_id=None,
            rating=member.rating,
            recorded_at=member.joined_at,
        )
