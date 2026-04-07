import enum
import uuid
from datetime import datetime, timezone


def _utcnow():
    return datetime.now(timezone.utc)

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EvaluationStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


DIMENSION_CODES = tuple(f"D{i}" for i in range(1, 10))


class Repo(Base):
    __tablename__ = "repos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    github_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    full_name: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    local_path: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    evaluations: Mapped[list["Evaluation"]] = relationship(back_populates="repo", cascade="all, delete-orphan")
    overrides: Mapped[list["HumanDimensionOverride"]] = relationship(back_populates="repo", cascade="all, delete-orphan")
    star_rating: Mapped["StarRating | None"] = relationship(back_populates="repo", uselist=False, cascade="all, delete-orphan")
    comments: Mapped[list["Comment"]] = relationship(back_populates="repo", cascade="all, delete-orphan")


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repo_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("repos.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[EvaluationStatus] = mapped_column(
        Enum(EvaluationStatus, name="evaluationstatus"),
        default=EvaluationStatus.pending,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    repo: Mapped["Repo"] = relationship(back_populates="evaluations")
    dimension_scores: Mapped[list["DimensionScore"]] = relationship(
        back_populates="evaluation", cascade="all, delete-orphan"
    )


class DimensionScore(Base):
    __tablename__ = "dimension_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False
    )
    dimension_code: Mapped[str] = mapped_column(String(8), nullable=False)
    automated_score: Mapped[float] = mapped_column(Float, nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    evaluation: Mapped["Evaluation"] = relationship(back_populates="dimension_scores")

    __table_args__ = (UniqueConstraint("evaluation_id", "dimension_code", name="uq_eval_dimension"),)


class HumanDimensionOverride(Base):
    __tablename__ = "human_dimension_overrides"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repo_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("repos.id", ondelete="CASCADE"), nullable=False)
    dimension_code: Mapped[str] = mapped_column(String(8), nullable=False)
    human_score: Mapped[float] = mapped_column(Float, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    repo: Mapped["Repo"] = relationship(back_populates="overrides")

    __table_args__ = (UniqueConstraint("repo_id", "dimension_code", name="uq_repo_dimension_override"),)


class StarRating(Base):
    __tablename__ = "star_ratings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repo_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("repos.id", ondelete="CASCADE"), nullable=False, unique=True)
    stars: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    repo: Mapped["Repo"] = relationship(back_populates="star_rating")


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repo_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("repos.id", ondelete="CASCADE"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    repo: Mapped["Repo"] = relationship(back_populates="comments")


class RepoComparison(Base):
    __tablename__ = "repo_comparisons"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repo_a_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("repos.id", ondelete="CASCADE"), nullable=False)
    repo_b_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("repos.id", ondelete="CASCADE"), nullable=False)
    preferred_repo_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("repos.id", ondelete="SET NULL"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
