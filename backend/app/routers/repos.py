import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Comment, Evaluation, HumanDimensionOverride, Repo, StarRating
from app.schemas import CommentOut, EvaluationOut, HumanOverrideOut, RepoCreate, RepoDetailOut, RepoOut, StarRatingOut
from app.services.git_clone import parse_github_url

router = APIRouter(prefix="/repos", tags=["repos"])


def _latest_evaluation(repo: Repo) -> Evaluation | None:
    if not repo.evaluations:
        return None
    return max(repo.evaluations, key=lambda x: x.created_at)


@router.get("", response_model=list[RepoOut])
def list_repos(db: Session = Depends(get_db)):
    rows = db.scalars(select(Repo).order_by(Repo.created_at.desc())).all()
    return rows


@router.post("", response_model=RepoOut)
def create_repo(body: RepoCreate, db: Session = Depends(get_db)):
    try:
        full_name = parse_github_url(body.github_url)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    existing = db.scalar(select(Repo).where(Repo.full_name == full_name))
    if existing:
        return existing
    repo = Repo(github_url=body.github_url.strip(), full_name=full_name)
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return repo


@router.get("/{repo_id}", response_model=RepoDetailOut)
def get_repo(repo_id: uuid.UUID, db: Session = Depends(get_db)):
    repo = db.scalar(
        select(Repo)
        .where(Repo.id == repo_id)
        .options(
            selectinload(Repo.evaluations).selectinload(Evaluation.dimension_scores),
            selectinload(Repo.overrides),
            selectinload(Repo.star_rating),
            selectinload(Repo.comments),
        )
    )
    if not repo:
        raise HTTPException(404, "repo not found")

    latest = _latest_evaluation(repo)
    latest_out = None
    if latest:
        latest_out = EvaluationOut.model_validate(latest)

    return RepoDetailOut(
        id=repo.id,
        github_url=repo.github_url,
        full_name=repo.full_name,
        local_path=repo.local_path,
        created_at=repo.created_at,
        latest_evaluation=latest_out,
        overrides=[HumanOverrideOut.model_validate(o) for o in repo.overrides],
        star_rating=StarRatingOut.model_validate(repo.star_rating) if repo.star_rating else None,
        comments=[CommentOut.model_validate(c) for c in sorted(repo.comments, key=lambda x: x.created_at)],
    )


@router.delete("/{repo_id}", status_code=204)
def delete_repo(repo_id: uuid.UUID, db: Session = Depends(get_db)):
    repo = db.get(Repo, repo_id)
    if not repo:
        raise HTTPException(404, "repo not found")
    db.delete(repo)
    db.commit()
