import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Repo, RepoComparison
from app.schemas import ComparisonCreate, ComparisonOut

router = APIRouter(prefix="/comparisons", tags=["comparisons"])


@router.get("", response_model=list[ComparisonOut])
def list_comparisons(db: Session = Depends(get_db)):
    rows = db.scalars(select(RepoComparison).order_by(RepoComparison.created_at.desc())).all()
    return rows


@router.post("", response_model=ComparisonOut)
def create_comparison(body: ComparisonCreate, db: Session = Depends(get_db)):
    if body.repo_a_id == body.repo_b_id:
        raise HTTPException(400, "repo_a and repo_b must differ")
    a = db.get(Repo, body.repo_a_id)
    b = db.get(Repo, body.repo_b_id)
    if not a or not b:
        raise HTTPException(404, "repo not found")
    if body.preferred_repo_id is not None:
        if body.preferred_repo_id not in (body.repo_a_id, body.repo_b_id):
            raise HTTPException(400, "preferred_repo_id must be repo_a or repo_b")

    row = RepoComparison(
        repo_a_id=body.repo_a_id,
        repo_b_id=body.repo_b_id,
        preferred_repo_id=body.preferred_repo_id,
        notes=body.notes,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{comparison_id}", status_code=204)
def delete_comparison(comparison_id: uuid.UUID, db: Session = Depends(get_db)):
    row = db.get(RepoComparison, comparison_id)
    if row:
        db.delete(row)
        db.commit()
