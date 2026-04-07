"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-04-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

evaluation_status = postgresql.ENUM(
    "pending", "running", "completed", "failed", name="evaluationstatus", create_type=False
)


def upgrade() -> None:
    evaluation_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "repos",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("github_url", sa.String(length=2048), nullable=False),
        sa.Column("full_name", sa.String(length=512), nullable=False),
        sa.Column("local_path", sa.String(length=2048), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_repos_full_name"), "repos", ["full_name"], unique=False)

    op.create_table(
        "evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("repo_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", evaluation_status, nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["repo_id"], ["repos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "dimension_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evaluation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dimension_code", sa.String(length=8), nullable=False),
        sa.Column("automated_score", sa.Float(), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["evaluation_id"], ["evaluations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("evaluation_id", "dimension_code", name="uq_eval_dimension"),
    )

    op.create_table(
        "human_dimension_overrides",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("repo_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dimension_code", sa.String(length=8), nullable=False),
        sa.Column("human_score", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["repo_id"], ["repos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("repo_id", "dimension_code", name="uq_repo_dimension_override"),
    )

    op.create_table(
        "star_ratings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("repo_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("stars", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["repo_id"], ["repos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("repo_id"),
    )

    op.create_table(
        "comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("repo_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["repo_id"], ["repos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "repo_comparisons",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("repo_a_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("repo_b_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("preferred_repo_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["preferred_repo_id"], ["repos.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["repo_a_id"], ["repos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["repo_b_id"], ["repos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("repo_comparisons")
    op.drop_table("comments")
    op.drop_table("star_ratings")
    op.drop_table("human_dimension_overrides")
    op.drop_table("dimension_scores")
    op.drop_table("evaluations")
    op.drop_index(op.f("ix_repos_full_name"), table_name="repos")
    op.drop_table("repos")
    evaluation_status.drop(op.get_bind(), checkfirst=True)
