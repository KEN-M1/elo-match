from __future__ import annotations

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB


metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)


users = Table(
    "users",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("email", String(320), nullable=False, unique=True),
    Column("name", String(255)),
    Column("image", Text),
)


leagues = Table(
    "leagues",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("name", String(255), nullable=False),
    Column("slug", String(120), nullable=False, unique=True),
    Column("owner_id", String(36), ForeignKey("users.id"), nullable=False),
    Column("description", Text),
    Column("is_public", Boolean, nullable=False, server_default="true"),
    Column("default_k", Integer, nullable=False, server_default="32"),
    Column("initial_rating", Float, nullable=False, server_default="1000"),
    Column("rating_floor", Float, nullable=False, server_default="100"),
)


league_members = Table(
    "league_members",
    metadata,
    Column("league_id", String(36), ForeignKey("leagues.id"), primary_key=True),
    Column("user_id", String(36), ForeignKey("users.id"), primary_key=True),
    Column("role", String(32), nullable=False, server_default="member"),
    Column("rating", Float, nullable=False, server_default="1000"),
    Column("wins", Integer, nullable=False, server_default="0"),
    Column("losses", Integer, nullable=False, server_default="0"),
    Column("joined_at", DateTime(timezone=True), nullable=False),
    CheckConstraint("role in ('admin', 'member')", name="league_member_role"),
)


invites = Table(
    "invites",
    metadata,
    Column("token", String(64), primary_key=True),
    Column("league_id", String(36), ForeignKey("leagues.id"), nullable=False),
    Column("created_by_id", String(36), ForeignKey("users.id"), nullable=False),
    Column("accepted_by_id", String(36), ForeignKey("users.id")),
    Column("accepted_at", DateTime(timezone=True)),
)


matches = Table(
    "matches",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("league_id", String(36), ForeignKey("leagues.id"), nullable=False),
    Column("winner_id", String(36), ForeignKey("users.id"), nullable=False),
    Column("loser_id", String(36), ForeignKey("users.id"), nullable=False),
    Column("reported_by_id", String(36), ForeignKey("users.id"), nullable=False),
    Column("status", String(32), nullable=False, server_default="PENDING"),
    Column("confirmed_by_id", String(36), ForeignKey("users.id")),
    Column("disputed_by_id", String(36), ForeignKey("users.id")),
    Column("dispute_note", Text),
    Column("played_at", DateTime(timezone=True), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("rating_result", JSONB),
    CheckConstraint("winner_id <> loser_id", name="match_distinct_players"),
    CheckConstraint(
        "status in ('PENDING', 'DISPUTED', 'COMPLETED', 'REJECTED')",
        name="match_status",
    ),
)


rating_history = Table(
    "rating_history",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", String(36), ForeignKey("users.id"), nullable=False),
    Column("league_id", String(36), ForeignKey("leagues.id"), nullable=False),
    Column("match_id", String(36), ForeignKey("matches.id")),
    Column("rating", Float, nullable=False),
    Column("recorded_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("user_id", "league_id", "match_id", name="rating_history_match_once"),
)
