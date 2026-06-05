from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4

from app.domain import League, LeagueMember, Match, MatchStatus, RatingHistoryEntry, RankKitError
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

    def __init__(
        self,
        state: MatchLifecycleState,
        rules: MatchLifecycleRules | None = None,
        rating_application: MatchRatingApplication | None = None,
    ) -> None:
        self.state = state
        self.rules = rules or MatchLifecycleRules()
        self.rating_application = rating_application or MatchRatingApplication()

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
        self.rules.ensure_loggable(reported_by_id, winner_id, loser_id)

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
        self.rules.ensure_confirmable(
            match,
            actor_id,
            actor_is_admin=self.state._is_admin(match.league_id, actor_id),
        )

        league = self.state._require_league(match.league_id)
        winner = self.state._require_member(match.league_id, match.winner_id)
        loser = self.state._require_member(match.league_id, match.loser_id)
        self.state.rating_history.extend(
            self.rating_application.apply_confirmed_match(
                league=league,
                match=match,
                winner=winner,
                loser=loser,
                confirmed_by_id=actor_id,
            )
        )
        return match

    def dispute(self, match_id: str, actor_id: str, note: str | None = None) -> Match:
        match = self.state._require_match(match_id)
        self.rules.ensure_disputable(match, actor_id)

        match.status = MatchStatus.DISPUTED
        match.disputed_by_id = actor_id
        match.dispute_note = note
        return match

    def reject(self, match_id: str, admin_id: str) -> Match:
        match = self.state._require_match(match_id)
        self.state._require_admin(match.league_id, admin_id)
        self.rules.ensure_rejectable(match)
        match.status = MatchStatus.REJECTED
        return match


class MatchLifecycleRules:
    """Shared rules for Match state transitions across Store adapters."""

    def ensure_loggable(self, reported_by_id: str, winner_id: str, loser_id: str) -> None:
        if winner_id == loser_id:
            raise RankKitError("A match requires two different players.")
        if reported_by_id not in {winner_id, loser_id}:
            raise RankKitError("Reporter must be one of the match participants.")

    def ensure_confirmable(self, match: Match, actor_id: str, actor_is_admin: bool) -> None:
        if match.status not in {MatchStatus.PENDING, MatchStatus.DISPUTED}:
            raise RankKitError("Only pending or disputed matches can be confirmed.")
        if actor_id == match.reported_by_id and not actor_is_admin:
            raise RankKitError("Reporter cannot confirm their own match.")
        if actor_id not in {match.winner_id, match.loser_id} and not actor_is_admin:
            raise RankKitError("Only a participant or admin can confirm this match.")

    def ensure_disputable(self, match: Match, actor_id: str) -> None:
        if match.status != MatchStatus.PENDING:
            raise RankKitError("Only pending matches can be disputed.")
        if actor_id == match.reported_by_id:
            raise RankKitError("Reporter cannot dispute their own match.")
        if actor_id not in {match.winner_id, match.loser_id}:
            raise RankKitError("Only a participant can dispute this match.")

    def ensure_rejectable(self, match: Match) -> None:
        if match.status != MatchStatus.DISPUTED:
            raise RankKitError("Only disputed matches can be rejected.")


class MatchRatingApplication:
    """Applies confirmed Match rating effects to participants and history."""

    def apply_confirmed_match(
        self,
        league: League,
        match: Match,
        winner: LeagueMember,
        loser: LeagueMember,
        confirmed_by_id: str,
        recorded_at: datetime | None = None,
    ) -> list[RatingHistoryEntry]:
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
        match.confirmed_by_id = confirmed_by_id
        match.rating_result = result
        recorded = recorded_at or datetime.now(timezone.utc)
        return [
            RatingHistoryEntry(match.winner_id, match.league_id, match.id, winner.rating, recorded),
            RatingHistoryEntry(match.loser_id, match.league_id, match.id, loser.rating, recorded),
        ]
