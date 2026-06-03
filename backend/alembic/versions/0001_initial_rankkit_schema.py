"""Initial RankKit schema.

Revision ID: 0001
Revises:
Create Date: 2026-06-02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("image", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_table(
        "leagues",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_public", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("default_k", sa.Integer(), server_default="32", nullable=False),
        sa.Column("initial_rating", sa.Float(), server_default="1000", nullable=False),
        sa.Column("rating_floor", sa.Float(), server_default="100", nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], name=op.f("fk_leagues_owner_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_leagues")),
        sa.UniqueConstraint("slug", name=op.f("uq_leagues_slug")),
    )
    op.create_table(
        "invites",
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("league_id", sa.String(length=36), nullable=False),
        sa.Column("created_by_id", sa.String(length=36), nullable=False),
        sa.Column("accepted_by_id", sa.String(length=36), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["accepted_by_id"], ["users.id"], name=op.f("fk_invites_accepted_by_id_users")),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], name=op.f("fk_invites_created_by_id_users")),
        sa.ForeignKeyConstraint(["league_id"], ["leagues.id"], name=op.f("fk_invites_league_id_leagues")),
        sa.PrimaryKeyConstraint("token", name=op.f("pk_invites")),
    )
    op.create_table(
        "league_members",
        sa.Column("league_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=32), server_default="member", nullable=False),
        sa.Column("rating", sa.Float(), server_default="1000", nullable=False),
        sa.Column("wins", sa.Integer(), server_default="0", nullable=False),
        sa.Column("losses", sa.Integer(), server_default="0", nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("role in ('admin', 'member')", name=op.f("ck_league_members_league_member_role")),
        sa.ForeignKeyConstraint(["league_id"], ["leagues.id"], name=op.f("fk_league_members_league_id_leagues")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_league_members_user_id_users")),
        sa.PrimaryKeyConstraint("league_id", "user_id", name=op.f("pk_league_members")),
    )
    op.create_table(
        "matches",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("league_id", sa.String(length=36), nullable=False),
        sa.Column("winner_id", sa.String(length=36), nullable=False),
        sa.Column("loser_id", sa.String(length=36), nullable=False),
        sa.Column("reported_by_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="PENDING", nullable=False),
        sa.Column("confirmed_by_id", sa.String(length=36), nullable=True),
        sa.Column("disputed_by_id", sa.String(length=36), nullable=True),
        sa.Column("dispute_note", sa.Text(), nullable=True),
        sa.Column("played_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rating_result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.CheckConstraint("status in ('PENDING', 'DISPUTED', 'COMPLETED', 'REJECTED')", name=op.f("ck_matches_match_status")),
        sa.CheckConstraint("winner_id <> loser_id", name=op.f("ck_matches_match_distinct_players")),
        sa.ForeignKeyConstraint(["confirmed_by_id"], ["users.id"], name=op.f("fk_matches_confirmed_by_id_users")),
        sa.ForeignKeyConstraint(["disputed_by_id"], ["users.id"], name=op.f("fk_matches_disputed_by_id_users")),
        sa.ForeignKeyConstraint(["league_id"], ["leagues.id"], name=op.f("fk_matches_league_id_leagues")),
        sa.ForeignKeyConstraint(["loser_id"], ["users.id"], name=op.f("fk_matches_loser_id_users")),
        sa.ForeignKeyConstraint(["reported_by_id"], ["users.id"], name=op.f("fk_matches_reported_by_id_users")),
        sa.ForeignKeyConstraint(["winner_id"], ["users.id"], name=op.f("fk_matches_winner_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_matches")),
    )
    op.create_table(
        "rating_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("league_id", sa.String(length=36), nullable=False),
        sa.Column("match_id", sa.String(length=36), nullable=True),
        sa.Column("rating", sa.Float(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["league_id"], ["leagues.id"], name=op.f("fk_rating_history_league_id_leagues")),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], name=op.f("fk_rating_history_match_id_matches")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_rating_history_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rating_history")),
        sa.UniqueConstraint("user_id", "league_id", "match_id", name="rating_history_match_once"),
    )


def downgrade() -> None:
    op.drop_table("rating_history")
    op.drop_table("matches")
    op.drop_table("league_members")
    op.drop_table("invites")
    op.drop_table("leagues")
    op.drop_table("users")
