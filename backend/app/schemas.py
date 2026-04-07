import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models import EvaluationStatus


class RepoCreate(BaseModel):
    github_url: str

    @field_validator("github_url")
    @classmethod
    def strip_url(cls, v: str) -> str:
        return v.strip()


class RepoOut(BaseModel):
    id: uuid.UUID
    github_url: str
    full_name: str
    local_path: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DimensionScoreOut(BaseModel):
    dimension_code: str
    automated_score: float
    detail: str | None

    model_config = {"from_attributes": True}


class EvaluationOut(BaseModel):
    id: uuid.UUID
    repo_id: uuid.UUID
    status: EvaluationStatus
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None
    dimension_scores: list[DimensionScoreOut] = []

    model_config = {"from_attributes": True}


class HumanOverrideUpsert(BaseModel):
    human_score: float = Field(..., ge=0.0, le=1.0)


class HumanOverrideOut(BaseModel):
    id: uuid.UUID
    repo_id: uuid.UUID
    dimension_code: str
    human_score: float
    updated_at: datetime

    model_config = {"from_attributes": True}


class StarRatingUpsert(BaseModel):
    stars: int = Field(..., ge=1, le=5)


class StarRatingOut(BaseModel):
    id: uuid.UUID
    repo_id: uuid.UUID
    stars: int
    updated_at: datetime

    model_config = {"from_attributes": True}


class CommentCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=20000)


class CommentOut(BaseModel):
    id: uuid.UUID
    repo_id: uuid.UUID
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ComparisonCreate(BaseModel):
    repo_a_id: uuid.UUID
    repo_b_id: uuid.UUID
    preferred_repo_id: uuid.UUID | None = None
    notes: str | None = None


class ComparisonOut(BaseModel):
    id: uuid.UUID
    repo_a_id: uuid.UUID
    repo_b_id: uuid.UUID
    preferred_repo_id: uuid.UUID | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RepoDetailOut(RepoOut):
    latest_evaluation: EvaluationOut | None = None
    overrides: list[HumanOverrideOut] = []
    star_rating: StarRatingOut | None = None
    comments: list[CommentOut] = []
