from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from app.domain import Invite, League, LeagueMember, Match, MatchStatus, RatingHistoryEntry, User
from app.rating import EloResult


@dataclass
class StoreSnapshot:
    users: dict[str, User] = field(default_factory=dict)
    leagues: dict[str, League] = field(default_factory=dict)
    members: dict[tuple[str, str], LeagueMember] = field(default_factory=dict)
    invites: dict[str, Invite] = field(default_factory=dict)
    matches: dict[str, Match] = field(default_factory=dict)
    rating_history: list[RatingHistoryEntry] = field(default_factory=list)


class LocalJsonSnapshot:
    """Persists the local-first RankKit store as a JSON snapshot."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> StoreSnapshot | None:
        if not self.path.exists():
            return None

        data = json.loads(self.path.read_text(encoding="utf-8"))
        return StoreSnapshot(
            users={item["id"]: User(**item) for item in data.get("users", [])},
            leagues={item["id"]: League(**item) for item in data.get("leagues", [])},
            members={
                (item["league_id"], item["user_id"]): LeagueMember(
                    **{**item, "joined_at": _parse_datetime(item["joined_at"])}
                )
                for item in data.get("members", [])
            },
            invites={
                item["token"]: Invite(
                    **{
                        **item,
                        "accepted_at": _parse_optional_datetime(item.get("accepted_at")),
                    }
                )
                for item in data.get("invites", [])
            },
            matches={
                item["id"]: Match(
                    **{
                        **item,
                        "status": MatchStatus(item["status"]),
                        "played_at": _parse_datetime(item["played_at"]),
                        "created_at": _parse_datetime(item["created_at"]),
                        "rating_result": _parse_elo_result(item.get("rating_result")),
                    }
                )
                for item in data.get("matches", [])
            },
            rating_history=[
                RatingHistoryEntry(
                    **{
                        **item,
                        "recorded_at": _parse_datetime(item["recorded_at"]),
                    }
                )
                for item in data.get("rating_history", [])
            ],
        )

    def save(self, snapshot: StoreSnapshot) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(_to_json(snapshot), indent=2), encoding="utf-8")


def _to_json(snapshot: StoreSnapshot) -> dict:
    return {
        "users": [user.__dict__ for user in snapshot.users.values()],
        "leagues": [league.__dict__ for league in snapshot.leagues.values()],
        "members": [
            {**member.__dict__, "joined_at": _format_datetime(member.joined_at)}
            for member in snapshot.members.values()
        ],
        "invites": [
            {
                **invite.__dict__,
                "accepted_at": _format_optional_datetime(invite.accepted_at),
            }
            for invite in snapshot.invites.values()
        ],
        "matches": [
            {
                **match.__dict__,
                "status": str(match.status),
                "played_at": _format_datetime(match.played_at),
                "created_at": _format_datetime(match.created_at),
                "rating_result": match.rating_result.__dict__ if match.rating_result else None,
            }
            for match in snapshot.matches.values()
        ],
        "rating_history": [
            {**entry.__dict__, "recorded_at": _format_datetime(entry.recorded_at)}
            for entry in snapshot.rating_history
        ],
    }


def _format_datetime(value: datetime) -> str:
    return value.isoformat()


def _format_optional_datetime(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _parse_optional_datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _parse_elo_result(value: dict | None) -> EloResult | None:
    return EloResult(**value) if value else None
