from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4

from app.domain import Match, MatchStatus, RatingHistoryEntry, RankKitError
from app.rating import calculate_elo


class MatchLifecycleState(Protocol):
    matches: dict[str, Match]
    rating_history: list[RatingHistoryEntry]

    def _require_league(self, league_id: str): ...

    def _require_match(self, match_id: str) -> Match: ...

    def _require_member(self, league_id: str, user_id: str): ...

    def _require_admin(self, league_id: str, user_id: str): ...

    def _is_admin(self, league_id: str, user_id: str) -> bool: ...


class MatchLifecycle:
    """Deep module for RankKit match state changes and rating effects."""

    def __init__(self, state: MatchLifecycleState) -> None:
        self.state = state

    def log(
        self,
        league_id: str,
        reported_by_id: str,
        winner_id: str,
        loser_id: str,
        played_at: datetime | None = None,
    ) -> Match:
        self.state._require_member(league_id, reported_by_id)
        self.state._require_member(league_id, winner_id)
        self.state._require_member(league_id, loser_id)
        if winner_id == loser_id:
            raise RankKitError("A match requires two different players.")
        if reported_by_id not in {winner_id, loser_id}:
            raise RankKitError("Reporter must be one of the match participants.")

        match = Match(
            id=str(uuid4()),
            league_id=league_id,
            winner_id=winner_id,
            loser_id=loser_id,
            reported_by_id=reported_by_id,
            played_at=played_at or datetime.now(timezone.utc),
        )
        self.state.matches[match.id] = match
        return match

    def confirm(self, match_id: str, actor_id: str) -> Match:
        match = self.state._require_match(match_id)
        self._ensure_confirmable(match, actor_id)

        league = self.state._require_league(match.league_id)
        winner = self.state._require_member(match.league_id, match.winner_id)
        loser = self.state._require_member(match.league_id, match.loser_id)
        result = calculate_elo(
            winner_rating=winner.rating,
            loser_rating=loser.rating,
            k_factor=league.default_k,
            rating_floor=league.rating_floor,
        )

        winner.rating = result.winner_rating_after
        winner.wins += 1
        loser.rating = result.loser_rating_after
        loser.losses += 1
        match.status = MatchStatus.COMPLETED
        match.confirmed_by_id = actor_id
        match.rating_result = result
        self.state.rating_history.extend(
            [
                RatingHistoryEntry(match.winner_id, match.league_id, match.id, winner.rating),
                RatingHistoryEntry(match.loser_id, match.league_id, match.id, loser.rating),
            ]
        )
        return match

    def dispute(self, match_id: str, actor_id: str, note: str | None = None) -> Match:
        match = self.state._require_match(match_id)
        if match.status != MatchStatus.PENDING:
            raise RankKitError("Only pending matches can be disputed.")
        if actor_id == match.reported_by_id:
            raise RankKitError("Reporter cannot dispute their own match.")
        if actor_id not in {match.winner_id, match.loser_id}:
            raise RankKitError("Only a participant can dispute this match.")

        match.status = MatchStatus.DISPUTED
        match.disputed_by_id = actor_id
        match.dispute_note = note
        return match

    def reject(self, match_id: str, admin_id: str) -> Match:
        match = self.state._require_match(match_id)
        self.state._require_admin(match.league_id, admin_id)
        if match.status != MatchStatus.DISPUTED:
            raise RankKitError("Only disputed matches can be rejected.")
        match.status = MatchStatus.REJECTED
        return match

    def _ensure_confirmable(self, match: Match, actor_id: str) -> None:
        if match.status not in {MatchStatus.PENDING, MatchStatus.DISPUTED}:
            raise RankKitError("Only pending or disputed matches can be confirmed.")
        if actor_id == match.reported_by_id and not self.state._is_admin(match.league_id, actor_id):
            raise RankKitError("Reporter cannot confirm their own match.")
        if actor_id not in {match.winner_id, match.loser_id} and not self.state._is_admin(
            match.league_id, actor_id
        ):
            raise RankKitError("Only a participant or admin can confirm this match.")
