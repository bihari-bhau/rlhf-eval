import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import DimensionScore, Evaluation, EvaluationStatus, Repo
from app.services.dimensions import run_all_dimensions
from app.services.git_clone import clone_or_update


def _execute_evaluation(db: Session, ev: Evaluation) -> None:
    repo = db.get(Repo, ev.repo_id)
    if not repo:
        ev.status = EvaluationStatus.failed
        ev.error_message = "repo missing"
        ev.completed_at = datetime.now(timezone.utc)
        db.commit()
        return

    ev.status = EvaluationStatus.running
    ev.error_message = None
    db.commit()

    try:
        path = clone_or_update(repo.full_name, repo.github_url)
        repo.local_path = path
        db.add(repo)

        for r in run_all_dimensions(path):
            db.add(
                DimensionScore(
                    evaluation_id=ev.id,
                    dimension_code=r.code,
                    automated_score=r.automated_score,
                    detail=r.detail,
                )
            )
        ev.status = EvaluationStatus.completed
        ev.completed_at = datetime.now(timezone.utc)
        ev.error_message = None
    except Exception as e:
        ev.status = EvaluationStatus.failed
        ev.error_message = str(e)[:4000]
        ev.completed_at = datetime.now(timezone.utc)

    db.commit()


def run_evaluation_sync(db: Session, repo_id: uuid.UUID) -> Evaluation:
    repo = db.get(Repo, repo_id)
    if not repo:
        raise ValueError("repo not found")

    ev = Evaluation(repo_id=repo.id, status=EvaluationStatus.pending)
    db.add(ev)
    db.commit()
    db.refresh(ev)
    _execute_evaluation(db, ev)
    db.refresh(ev)
    return ev


def continue_evaluation_async(evaluation_id: uuid.UUID) -> None:
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        ev = db.get(Evaluation, evaluation_id)
        if ev:
            _execute_evaluation(db, ev)
    finally:
        db.close()
