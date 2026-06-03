from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from secrets import token_urlsafe
from uuid import uuid4

from app.rating import EloResult


class RankKitError(ValueError):
    pass


class MatchStatus(StrEnum):
    PENDING = "PENDING"
    DISPUTED = "DISPUTED"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


@dataclass
class User:
    id: str
    email: str
    name: str | None = None
    image: str | None = None


@dataclass
class League:
    id: str
    name: str
    slug: str
    owner_id: str
    description: str | None = None
    is_public: bool = True
    default_k: int = 32
    initial_rating: float = 1000.0
    rating_floor: float = 100.0


@dataclass
class LeagueMember:
    league_id: str
    user_id: str
    role: str = "member"
    rating: float = 1000.0
    wins: int = 0
    losses: int = 0
    joined_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Invite:
    token: str
    league_id: str
    created_by_id: str
    accepted_by_id: str | None = None
    accepted_at: datetime | None = None


@dataclass
class Match:
    id: str
    league_id: str
    winner_id: str
    loser_id: str
    reported_by_id: str
    status: MatchStatus = MatchStatus.PENDING
    confirmed_by_id: str | None = None
    disputed_by_id: str | None = None
    dispute_note: str | None = None
    played_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    rating_result: EloResult | None = None


@dataclass
class RatingHistoryEntry:
    user_id: str
    league_id: str
    match_id: str | None
    rating: float
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class MemberSummary:
    league_id: str
    user_id: str
    email: str
    name: str | None
    role: str
    rating: float
    wins: int
    losses: int
    joined_at: datetime


class RankKitStore:
    """In-memory implementation of the RankKit MVP interface."""

    def __init__(self, persistence_path: str | Path | None = None) -> None:
        self.users: dict[str, User] = {}
        self.leagues: dict[str, League] = {}
        self.members: dict[tuple[str, str], LeagueMember] = {}
        self.invites: dict[str, Invite] = {}
        self.matches: dict[str, Match] = {}
        self.rating_history: list[RatingHistoryEntry] = []
        self._local_snapshot = self._create_local_snapshot(persistence_path)
        self._load()
        from app.match_lifecycle import MatchLifecycle

        self.match_lifecycle = MatchLifecycle(self)

    def sync_user(self, email: str, name: str | None = None, image: str | None = None) -> User:
        for user in self.users.values():
            if user.email == email:
                user.name = name or user.name
                user.image = image or user.image
                self._save()
                return user

        user = User(id=str(uuid4()), email=email, name=name, image=image)
        self.users[user.id] = user
        self._save()
        return user

    def create_league(
        self,
        owner_id: str,
        name: str,
        slug: str,
        description: str | None = None,
        is_public: bool = True,
    ) -> League:
        self._require_user(owner_id)
        if any(league.slug == slug for league in self.leagues.values()):
            raise RankKitError("League slug is already taken.")

        league = League(
            id=str(uuid4()),
            name=name,
            slug=slug,
            owner_id=owner_id,
            description=description,
            is_public=is_public,
        )
        self.leagues[league.id] = league
        self.members[(league.id, owner_id)] = LeagueMember(
            league_id=league.id,
            user_id=owner_id,
            role="admin",
            rating=league.initial_rating,
        )
        self.rating_history.append(
            RatingHistoryEntry(
                user_id=owner_id,
                league_id=league.id,
                match_id=None,
                rating=league.initial_rating,
            )
        )
        self._save()
        return league

    def create_invite(self, league_id: str, admin_id: str) -> Invite:
        self._require_admin(league_id, admin_id)
        invite = Invite(token=token_urlsafe(18), league_id=league_id, created_by_id=admin_id)
        self.invites[invite.token] = invite
        self._save()
        return invite

    def accept_invite(self, token: str, user_id: str) -> LeagueMember:
        self._require_user(user_id)
        invite = self.invites.get(token)
        if invite is None:
            raise RankKitError("Invite token was not found.")
        if invite.accepted_by_id is not None:
            raise RankKitError("Invite token has already been accepted.")

        league = self._require_league(invite.league_id)
        member = LeagueMember(
            league_id=league.id,
            user_id=user_id,
            rating=league.initial_rating,
        )
        self.members[(league.id, user_id)] = member
        invite.accepted_by_id = user_id
        invite.accepted_at = datetime.now(timezone.utc)
        self.rating_history.append(
            RatingHistoryEntry(
                user_id=user_id,
                league_id=league.id,
                match_id=None,
                rating=league.initial_rating,
            )
        )
        self._save()
        return member

    def leaderboard(self, league_id: str) -> list[LeagueMember]:
        self._require_league(league_id)
        members = [member for member in self.members.values() if member.league_id == league_id]
        return sorted(members, key=lambda member: (-member.rating, member.joined_at))

    def member_summaries(self, league_id: str) -> list[MemberSummary]:
        return [
            MemberSummary(
                league_id=member.league_id,
                user_id=member.user_id,
                email=self.users[member.user_id].email,
                name=self.users[member.user_id].name,
                role=member.role,
                rating=member.rating,
                wins=member.wins,
                losses=member.losses,
                joined_at=member.joined_at,
            )
            for member in self.leaderboard(league_id)
            if member.user_id in self.users
        ]

    def list_leagues(self, user_id: str | None = None) -> list[League]:
        if user_id is None:
            leagues = list(self.leagues.values())
        else:
            leagues = [
                self.leagues[member.league_id]
                for member in self.members.values()
                if member.user_id == user_id and member.league_id in self.leagues
            ]
        return sorted(leagues, key=lambda league: league.name.lower())

    def public_leaderboard(self, slug: str) -> tuple[League, list[MemberSummary]]:
        league = next((candidate for candidate in self.leagues.values() if candidate.slug == slug), None)
        if league is None or not league.is_public:
            raise RankKitError("Public league was not found.")
        return league, self.member_summaries(league.id)

    def league_matches(self, league_id: str) -> list[Match]:
        self._require_league(league_id)
        matches = [match for match in self.matches.values() if match.league_id == league_id]
        return sorted(matches, key=lambda match: match.created_at, reverse=True)

    def log_match(
        self,
        league_id: str,
        reported_by_id: str,
        winner_id: str,
        loser_id: str,
        played_at: datetime | None = None,
    ) -> Match:
        match = self.match_lifecycle.log(
            league_id=league_id,
            reported_by_id=reported_by_id,
            winner_id=winner_id,
            loser_id=loser_id,
            played_at=played_at,
        )
        self._save()
        return match

    def confirm_match(self, match_id: str, actor_id: str) -> Match:
        match = self.match_lifecycle.confirm(match_id, actor_id)
        self._save()
        return match

    def dispute_match(self, match_id: str, actor_id: str, note: str | None = None) -> Match:
        match = self.match_lifecycle.dispute(match_id, actor_id, note)
        self._save()
        return match

    def reject_match(self, match_id: str, admin_id: str) -> Match:
        match = self.match_lifecycle.reject(match_id, admin_id)
        self._save()
        return match

    def player_rating_history(self, league_id: str, user_id: str) -> list[RatingHistoryEntry]:
        self._require_member(league_id, user_id)
        return [
            entry
            for entry in self.rating_history
            if entry.league_id == league_id and entry.user_id == user_id
        ]

    def _require_user(self, user_id: str) -> User:
        user = self.users.get(user_id)
        if user is None:
            raise RankKitError("User was not found.")
        return user

    def _require_league(self, league_id: str) -> League:
        league = self.leagues.get(league_id)
        if league is None:
            raise RankKitError("League was not found.")
        return league

    def _require_match(self, match_id: str) -> Match:
        match = self.matches.get(match_id)
        if match is None:
            raise RankKitError("Match was not found.")
        return match

    def _require_member(self, league_id: str, user_id: str) -> LeagueMember:
        member = self.members.get((league_id, user_id))
        if member is None:
            raise RankKitError("League member was not found.")
        return member

    def _require_admin(self, league_id: str, user_id: str) -> LeagueMember:
        member = self._require_member(league_id, user_id)
        if member.role != "admin":
            raise RankKitError("League admin permissions are required.")
        return member

    def _is_admin(self, league_id: str, user_id: str) -> bool:
        member = self.members.get((league_id, user_id))
        return member is not None and member.role == "admin"

    def _create_local_snapshot(self, persistence_path: str | Path | None):
        if persistence_path is None:
            return None

        from app.local_snapshot import LocalJsonSnapshot

        return LocalJsonSnapshot(persistence_path)

    def _save(self) -> None:
        if self._local_snapshot is None:
            return

        self._local_snapshot.save(self._snapshot())

    def _load(self) -> None:
        if self._local_snapshot is None:
            return

        snapshot = self._local_snapshot.load()
        if snapshot is None:
            return

        self.users = snapshot.users
        self.leagues = snapshot.leagues
        self.members = snapshot.members
        self.invites = snapshot.invites
        self.matches = snapshot.matches
        self.rating_history = snapshot.rating_history

    def _snapshot(self):
        from app.local_snapshot import StoreSnapshot

        return StoreSnapshot(
            users=self.users,
            leagues=self.leagues,
            members=self.members,
            invites=self.invites,
            matches=self.matches,
            rating_history=self.rating_history,
        )
