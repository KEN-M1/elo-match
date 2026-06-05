from __future__ import annotations

from app.domain import LeagueMember, MemberSummary, User


class LeaderboardProjection:
    """Projects League Members into ranked Leaderboards and Member Summaries."""

    def rank_members(self, members: list[LeagueMember]) -> list[LeagueMember]:
        return sorted(members, key=lambda member: (-member.rating, member.joined_at))

    def member_summaries(
        self,
        members: list[LeagueMember],
        users_by_id: dict[str, User],
    ) -> list[MemberSummary]:
        return [
            MemberSummary(
                league_id=member.league_id,
                user_id=member.user_id,
                email=users_by_id[member.user_id].email,
                name=users_by_id[member.user_id].name,
                role=member.role,
                rating=member.rating,
                wins=member.wins,
                losses=member.losses,
                joined_at=member.joined_at,
            )
            for member in self.rank_members(members)
            if member.user_id in users_by_id
        ]
