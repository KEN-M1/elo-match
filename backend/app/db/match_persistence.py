from __future__ import annotations

from datetime import datetime, timezone
from typing import Awaitable, Callable
from uuid import uuid4

from sqlalchemy import insert, select, update

from app.db.schema import league_members, matches, rating_history
from app.domain import League, LeagueMember, Match, MatchStatus, RankKitError
from app.match_lifecycle import MatchLifecycleRules, MatchRatingApplication
from app.rating import EloResult


class PostgresMatchPersistence:
    """Database implementation of Match persistence and rating write ordering."""

    def __init__(
        self,
        connection,
        get_league: Callable[[str], Awaitable[League]],
        require_member: Callable[[str, str], Awaitable[LeagueMember]],
        require_admin: Callable[[str, str], Awaitable[LeagueMember]],
        is_admin: Callable[[str, str], Awaitable[bool]],
        match_rules: MatchLifecycleRules | None = None,
        rating_application: MatchRatingApplication | None = None,
    ) -> None:
        self.connection = connection
        self.get_league = get_league
        self.require_member = require_member
        self.require_admin = require_admin
        self.is_admin = is_admin
        self.match_rules = match_rules or MatchLifecycleRules()
        self.rating_application = rating_application or MatchRatingApplication()

    async def log(
        self,
        league_id: str,
        reported_by_id: str,
        winner_id: str,
        loser_id: str,
        played_at: datetime | None = None,
    ) -> Match:
        await self.get_league(league_id)
        await self.require_member(league_id, winner_id)
        await self.require_member(league_id, loser_id)
        self.match_rules.ensure_loggable(reported_by_id, winner_id, loser_id)
        now = datetime.now(timezone.utc)
        match = Match(
            id=str(uuid4()),
            league_id=league_id,
            winner_id=winner_id,
            loser_id=loser_id,
            reported_by_id=reported_by_id,
            played_at=played_at or now,
            created_at=now,
        )
        await self.connection.execute(
            insert(matches).values(
                id=match.id,
                league_id=match.league_id,
                winner_id=match.winner_id,
                loser_id=match.loser_id,
                reported_by_id=match.reported_by_id,
                status=match.status.value,
                played_at=match.played_at,
                created_at=match.created_at,
            )
        )
        return match

    async def list_for_league(self, league_id: str) -> list[Match]:
        await self.get_league(league_id)
        rows = (
            await self.connection.execute(
                select(matches)
                .where(matches.c.league_id == league_id)
                .order_by(matches.c.created_at.desc())
            )
        ).mappings().all()
        return [_match_from_row(row) for row in rows]

    async def confirm(self, match_id: str, actor_id: str) -> Match:
        match = await self._require_match(match_id)
        self.match_rules.ensure_confirmable(
            match,
            actor_id,
            actor_is_admin=await self.is_admin(match.league_id, actor_id),
        )

        league = await self.get_league(match.league_id)
        winner = await self.require_member(match.league_id, match.winner_id)
        loser = await self.require_member(match.league_id, match.loser_id)
        history_entries = self.rating_application.apply_confirmed_match(
            league=league,
            match=match,
            winner=winner,
            loser=loser,
            confirmed_by_id=actor_id,
        )
        if match.rating_result is None:
            raise RuntimeError("Confirmed match must include a rating result.")
        await self.connection.execute(
            update(league_members)
            .where(
                league_members.c.league_id == match.league_id,
                league_members.c.user_id == match.winner_id,
            )
            .values(rating=winner.rating, wins=winner.wins)
        )
        await self.connection.execute(
            update(league_members)
            .where(
                league_members.c.league_id == match.league_id,
                league_members.c.user_id == match.loser_id,
            )
            .values(rating=loser.rating, losses=loser.losses)
        )
        await self.connection.execute(
            update(matches)
            .where(matches.c.id == match.id)
            .values(
                status=match.status.value,
                confirmed_by_id=match.confirmed_by_id,
                rating_result=_elo_result_to_dict(match.rating_result),
            )
        )
        await self.connection.execute(
            insert(rating_history),
            [
                {
                    "user_id": entry.user_id,
                    "league_id": entry.league_id,
                    "match_id": entry.match_id,
                    "rating": entry.rating,
                    "recorded_at": entry.recorded_at,
                }
                for entry in history_entries
            ],
        )
        return match

    async def dispute(self, match_id: str, actor_id: str, note: str | None = None) -> Match:
        match = await self._require_match(match_id)
        self.match_rules.ensure_disputable(match, actor_id)

        await self.connection.execute(
            update(matches)
            .where(matches.c.id == match.id)
            .values(
                status=MatchStatus.DISPUTED.value,
                disputed_by_id=actor_id,
                dispute_note=note,
            )
        )
        match.status = MatchStatus.DISPUTED
        match.disputed_by_id = actor_id
        match.dispute_note = note
        return match

    async def reject(self, match_id: str, admin_id: str) -> Match:
        match = await self._require_match(match_id)
        await self.require_admin(match.league_id, admin_id)
        self.match_rules.ensure_rejectable(match)

        await self.connection.execute(
            update(matches)
            .where(matches.c.id == match.id)
            .values(status=MatchStatus.REJECTED.value)
        )
        match.status = MatchStatus.REJECTED
        return match

    async def _require_match(self, match_id: str) -> Match:
        row = (
            await self.connection.execute(select(matches).where(matches.c.id == match_id))
        ).mappings().first()
        if row is None:
            raise RankKitError("Match was not found.")
        return _match_from_row(row)


def _match_from_row(row) -> Match:
    return Match(
        id=row["id"],
        league_id=row["league_id"],
        winner_id=row["winner_id"],
        loser_id=row["loser_id"],
        reported_by_id=row["reported_by_id"],
        status=MatchStatus(row["status"]),
        confirmed_by_id=row["confirmed_by_id"],
        disputed_by_id=row["disputed_by_id"],
        dispute_note=row["dispute_note"],
        played_at=row["played_at"],
        created_at=row["created_at"],
        rating_result=_elo_result_from_dict(row["rating_result"]),
    )


def _elo_result_to_dict(result: EloResult) -> dict[str, float]:
    return {
        "winner_rating_before": result.winner_rating_before,
        "loser_rating_before": result.loser_rating_before,
        "winner_rating_after": result.winner_rating_after,
        "loser_rating_after": result.loser_rating_after,
        "winner_delta": result.winner_delta,
        "loser_delta": result.loser_delta,
    }


def _elo_result_from_dict(payload) -> EloResult | None:
    if payload is None:
        return None
    return EloResult(
        winner_rating_before=payload["winner_rating_before"],
        loser_rating_before=payload["loser_rating_before"],
        winner_rating_after=payload["winner_rating_after"],
        loser_rating_after=payload["loser_rating_after"],
        winner_delta=payload["winner_delta"],
        loser_delta=payload["loser_delta"],
    )
