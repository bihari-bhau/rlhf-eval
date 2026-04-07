import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Evaluation, EvaluationStatus, Repo
from app.schemas import EvaluationOut
from app.services.evaluation_runner import continue_evaluation_async, run_evaluation_sync

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.post("/repos/{repo_id}/run", response_model=EvaluationOut)
def trigger_evaluation(repo_id: uuid.UUID, db: Session = Depends(get_db)):
    repo = db.get(Repo, repo_id)
    if not repo:
        raise HTTPException(404, "repo not found")
    try:
        ev = run_evaluation_sync(db, repo_id)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return EvaluationOut.model_validate(ev)


@router.post("/repos/{repo_id}/run-async", response_model=EvaluationOut)
def trigger_evaluation_async(repo_id: uuid.UUID, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    repo = db.get(Repo, repo_id)
    if not repo:
        raise HTTPException(404, "repo not found")

    ev = Evaluation(repo_id=repo.id, status=EvaluationStatus.pending)
    db.add(ev)
    db.commit()
    db.refresh(ev)
    background_tasks.add_task(continue_evaluation_async, ev.id)
    return EvaluationOut.model_validate(ev)
