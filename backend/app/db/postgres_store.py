from __future__ import annotations

from datetime import datetime
from secrets import token_urlsafe
from uuid import uuid4

from sqlalchemy import insert, select, update

from app.db.match_persistence import PostgresMatchPersistence
from app.db.schema import invites, league_members, leagues, rating_history, users
from app.domain import (
    Invite,
    League,
    LeagueMember,
    Match,
    MemberSummary,
    RankKitError,
    RatingHistoryEntry,
    User,
)
from app.leaderboard import LeaderboardProjection
from app.match_lifecycle import MatchLifecycleRules, MatchRatingApplication
from app.membership import MembershipApplication


class PostgresStore:
    """First Postgres adapter slice for RankKit user and League persistence."""

    def __init__(
        self,
        connection,
        match_rules: MatchLifecycleRules | None = None,
        rating_application: MatchRatingApplication | None = None,
        membership_application: MembershipApplication | None = None,
        leaderboard_projection: LeaderboardProjection | None = None,
    ) -> None:
        self.connection = connection
        self.match_rules = match_rules or MatchLifecycleRules()
        self.rating_application = rating_application or MatchRatingApplication()
        self.membership_application = membership_application or MembershipApplication()
        self.leaderboard_projection = leaderboard_projection or LeaderboardProjection()
        self.match_persistence = PostgresMatchPersistence(
            connection,
            get_league=self.get_league,
            require_member=self._require_member,
            require_admin=self._require_admin,
            is_admin=self._is_admin,
            match_rules=self.match_rules,
            rating_application=self.rating_application,
        )

    async def sync_user(self, email: str, name: str | None = None, image: str | None = None) -> User:
        existing = (
            await self.connection.execute(select(users).where(users.c.email == email))
        ).mappings().first()
        if existing is not None:
            user = _user_from_row(existing)
            next_name = name or user.name
            next_image = image or user.image
            if next_name != user.name or next_image != user.image:
                await self.connection.execute(
                    update(users)
                    .where(users.c.id == user.id)
                    .values(name=next_name, image=next_image)
                )
                return User(id=user.id, email=user.email, name=next_name, image=next_image)
            return user

        user = User(id=str(uuid4()), email=email, name=name, image=image)
        await self.connection.execute(
            insert(users).values(id=user.id, email=user.email, name=user.name, image=user.image)
        )
        return user

    async def get_user(self, user_id: str) -> User:
        row = (
            await self.connection.execute(select(users).where(users.c.id == user_id))
        ).mappings().first()
        if row is None:
            raise RankKitError("User was not found.")
        return _user_from_row(row)

    async def create_league(
        self,
        owner_id: str,
        name: str,
        slug: str,
        description: str | None = None,
        is_public: bool = True,
    ) -> League:
        owner = (
            await self.connection.execute(select(users.c.id).where(users.c.id == owner_id))
        ).scalar_one_or_none()
        if owner is None:
            raise RankKitError("User was not found.")

        existing_slug = (
            await self.connection.execute(select(leagues.c.id).where(leagues.c.slug == slug))
        ).scalar_one_or_none()
        if existing_slug is not None:
            raise RankKitError("League slug is already taken.")

        league = League(
            id=str(uuid4()),
            name=name,
            slug=slug,
            owner_id=owner_id,
            description=description,
            is_public=is_public,
        )
        await self.connection.execute(
            insert(leagues).values(
                id=league.id,
                name=league.name,
                slug=league.slug,
                owner_id=league.owner_id,
                description=league.description,
                is_public=league.is_public,
                default_k=league.default_k,
                initial_rating=league.initial_rating,
                rating_floor=league.rating_floor,
            )
        )
        member, history = self.membership_application.create_owner_membership(league)
        await self.connection.execute(
            insert(league_members).values(
                league_id=member.league_id,
                user_id=member.user_id,
                role=member.role,
                rating=member.rating,
                wins=member.wins,
                losses=member.losses,
                joined_at=member.joined_at,
            )
        )
        await self.connection.execute(
            insert(rating_history).values(
                user_id=history.user_id,
                league_id=history.league_id,
                match_id=history.match_id,
                rating=history.rating,
                recorded_at=history.recorded_at,
            )
        )
        return league

    async def create_invite(self, league_id: str, admin_id: str) -> Invite:
        admin = await self._require_admin(league_id, admin_id)
        token = token_urlsafe(18)
        invite = Invite(token=token, league_id=admin.league_id, created_by_id=admin_id)
        await self.connection.execute(
            insert(invites).values(
                token=invite.token,
                league_id=invite.league_id,
                created_by_id=invite.created_by_id,
            )
        )
        return invite

    async def accept_invite(self, token: str, user_id: str) -> LeagueMember:
        user = (
            await self.connection.execute(select(users.c.id).where(users.c.id == user_id))
        ).scalar_one_or_none()
        if user is None:
            raise RankKitError("User was not found.")

        invite_row = (
            await self.connection.execute(select(invites).where(invites.c.token == token))
        ).mappings().first()
        if invite_row is None:
            raise RankKitError("Invite token was not found.")
        if invite_row["accepted_by_id"] is not None:
            raise RankKitError("Invite token has already been accepted.")

        league = await self.get_league(invite_row["league_id"])
        invite = _invite_from_row(invite_row)
        member, history = self.membership_application.accept_invite(invite, league, user_id)
        await self.connection.execute(
            insert(league_members).values(
                league_id=member.league_id,
                user_id=member.user_id,
                role=member.role,
                rating=member.rating,
                wins=member.wins,
                losses=member.losses,
                joined_at=member.joined_at,
            )
        )
        await self.connection.execute(
            update(invites)
            .where(invites.c.token == token)
            .values(accepted_by_id=invite.accepted_by_id, accepted_at=invite.accepted_at)
        )
        await self.connection.execute(
            insert(rating_history).values(
                user_id=history.user_id,
                league_id=history.league_id,
                match_id=history.match_id,
                rating=history.rating,
                recorded_at=history.recorded_at,
            )
        )
        return member

    async def get_league(self, league_id: str) -> League:
        row = (
            await self.connection.execute(select(leagues).where(leagues.c.id == league_id))
        ).mappings().first()
        if row is None:
            raise RankKitError("League was not found.")
        return _league_from_row(row)

    async def list_leagues(self, user_id: str | None = None) -> list[League]:
        statement = select(leagues)
        if user_id is not None:
            statement = statement.join(
                league_members,
                league_members.c.league_id == leagues.c.id,
            ).where(league_members.c.user_id == user_id)
        rows = (await self.connection.execute(statement)).mappings().all()
        return sorted([_league_from_row(row) for row in rows], key=lambda league: league.name.lower())

    async def log_match(
        self,
        league_id: str,
        reported_by_id: str,
        winner_id: str,
        loser_id: str,
        played_at: datetime | None = None,
    ) -> Match:
        return await self.match_persistence.log(
            league_id=league_id,
            reported_by_id=reported_by_id,
            winner_id=winner_id,
            loser_id=loser_id,
            played_at=played_at,
        )

    async def league_matches(self, league_id: str) -> list[Match]:
        return await self.match_persistence.list_for_league(league_id)

    async def confirm_match(self, match_id: str, actor_id: str) -> Match:
        return await self.match_persistence.confirm(match_id, actor_id)

    async def dispute_match(self, match_id: str, actor_id: str, note: str | None = None) -> Match:
        return await self.match_persistence.dispute(match_id, actor_id, note)

    async def reject_match(self, match_id: str, admin_id: str) -> Match:
        return await self.match_persistence.reject(match_id, admin_id)

    async def leaderboard(self, league_id: str) -> list[LeagueMember]:
        await self.get_league(league_id)
        rows = (
            await self.connection.execute(
                select(league_members)
                .where(league_members.c.league_id == league_id)
            )
        ).mappings().all()
        return self.leaderboard_projection.rank_members([_league_member_from_row(row) for row in rows])

    async def member_summaries(self, league_id: str) -> list[MemberSummary]:
        await self.get_league(league_id)
        members = await self.leaderboard(league_id)
        user_ids = [member.user_id for member in members]
        if not user_ids:
            return []

        user_rows = (
            await self.connection.execute(
                select(users).where(users.c.id.in_(user_ids))
            )
        ).mappings().all()
        hydrated_users = [_user_from_row(row) for row in user_rows]
        users_by_id = {user.id: user for user in hydrated_users}
        return self.leaderboard_projection.member_summaries(members, users_by_id)

    async def public_leaderboard(self, slug: str) -> tuple[League, list[MemberSummary]]:
        row = (
            await self.connection.execute(
                select(leagues).where(
                    leagues.c.slug == slug,
                    leagues.c.is_public.is_(True),
                )
            )
        ).mappings().first()
        if row is None:
            raise RankKitError("Public league was not found.")
        league = _league_from_row(row)
        return league, await self.member_summaries(league.id)

    async def player_rating_history(self, league_id: str, user_id: str) -> list[RatingHistoryEntry]:
        await self._require_member(league_id, user_id)
        rows = (
            await self.connection.execute(
                select(rating_history)
                .where(
                    rating_history.c.league_id == league_id,
                    rating_history.c.user_id == user_id,
                )
                .order_by(rating_history.c.recorded_at.asc(), rating_history.c.id.asc())
            )
        ).mappings().all()
        return [_rating_history_entry_from_row(row) for row in rows]

    async def _require_member(self, league_id: str, user_id: str) -> LeagueMember:
        row = (
            await self.connection.execute(
                select(league_members).where(
                    league_members.c.league_id == league_id,
                    league_members.c.user_id == user_id,
                )
            )
        ).mappings().first()
        if row is None:
            raise RankKitError("League member was not found.")
        return _league_member_from_row(row)

    async def _require_admin(self, league_id: str, user_id: str) -> LeagueMember:
        member = await self._require_member(league_id, user_id)
        if member.role != "admin":
            raise RankKitError("League admin permissions are required.")
        return member

    async def _is_admin(self, league_id: str, user_id: str) -> bool:
        row = (
            await self.connection.execute(
                select(league_members.c.role).where(
                    league_members.c.league_id == league_id,
                    league_members.c.user_id == user_id,
                )
            )
        ).scalar_one_or_none()
        return row == "admin"


def _user_from_row(row) -> User:
    return User(
        id=row["id"],
        email=row["email"],
        name=row["name"],
        image=row["image"],
    )


def _league_from_row(row) -> League:
    return League(
        id=row["id"],
        name=row["name"],
        slug=row["slug"],
        owner_id=row["owner_id"],
        description=row["description"],
        is_public=row["is_public"],
        default_k=row["default_k"],
        initial_rating=row["initial_rating"],
        rating_floor=row["rating_floor"],
    )


def _league_member_from_row(row) -> LeagueMember:
    return LeagueMember(
        league_id=row["league_id"],
        user_id=row["user_id"],
        role=row["role"],
        rating=row["rating"],
        wins=row["wins"],
        losses=row["losses"],
        joined_at=row["joined_at"],
    )


def _invite_from_row(row) -> Invite:
    return Invite(
        token=row["token"],
        league_id=row["league_id"],
        created_by_id=row["created_by_id"],
        accepted_by_id=row["accepted_by_id"],
        accepted_at=row["accepted_at"],
    )


def _rating_history_entry_from_row(row) -> RatingHistoryEntry:
    return RatingHistoryEntry(
        user_id=row["user_id"],
        league_id=row["league_id"],
        match_id=row["match_id"],
        rating=row["rating"],
        recorded_at=row["recorded_at"],
    )
