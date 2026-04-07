import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Comment, HumanDimensionOverride, Repo, StarRating
from app.schemas import CommentCreate, CommentOut, HumanOverrideOut, HumanOverrideUpsert, StarRatingOut, StarRatingUpsert

router = APIRouter(tags=["human"])


@router.put("/repos/{repo_id}/overrides/{dimension_code}", response_model=HumanOverrideOut)
def upsert_override(
    repo_id: uuid.UUID,
    dimension_code: str,
    body: HumanOverrideUpsert,
    db: Session = Depends(get_db),
):
    if dimension_code not in {f"D{i}" for i in range(1, 10)}:
        raise HTTPException(400, "dimension must be D1–D9")
    repo = db.get(Repo, repo_id)
    if not repo:
        raise HTTPException(404, "repo not found")

    row = db.scalar(
        select(HumanDimensionOverride).where(
            HumanDimensionOverride.repo_id == repo_id,
            HumanDimensionOverride.dimension_code == dimension_code,
        )
    )
    if row:
        row.human_score = body.human_score
    else:
        row = HumanDimensionOverride(repo_id=repo_id, dimension_code=dimension_code, human_score=body.human_score)
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/repos/{repo_id}/overrides/{dimension_code}", status_code=204)
def delete_override(repo_id: uuid.UUID, dimension_code: str, db: Session = Depends(get_db)):
    row = db.scalar(
        select(HumanDimensionOverride).where(
            HumanDimensionOverride.repo_id == repo_id,
            HumanDimensionOverride.dimension_code == dimension_code,
        )
    )
    if row:
        db.delete(row)
        db.commit()


@router.put("/repos/{repo_id}/stars", response_model=StarRatingOut)
def upsert_stars(repo_id: uuid.UUID, body: StarRatingUpsert, db: Session = Depends(get_db)):
    if not db.get(Repo, repo_id):
        raise HTTPException(404, "repo not found")

    row = db.scalar(select(StarRating).where(StarRating.repo_id == repo_id))
    if row:
        row.stars = body.stars
    else:
        row = StarRating(repo_id=repo_id, stars=body.stars)
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.post("/repos/{repo_id}/comments", response_model=CommentOut)
def add_comment(repo_id: uuid.UUID, body: CommentCreate, db: Session = Depends(get_db)):
    repo = db.get(Repo, repo_id)
    if not repo:
        raise HTTPException(404, "repo not found")
    c = Comment(repo_id=repo_id, body=body.body)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.delete("/comments/{comment_id}", status_code=204)
def delete_comment(comment_id: uuid.UUID, db: Session = Depends(get_db)):
    c = db.get(Comment, comment_id)
    if c:
        db.delete(c)
        db.commit()
