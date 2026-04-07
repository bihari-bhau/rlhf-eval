"""38-criteria checklist endpoint."""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Repo
from app.services.dimensions import run_checklist

router = APIRouter(prefix="/checklist", tags=["checklist"])


@router.get("/repos/{repo_id}")
def get_checklist(repo_id: uuid.UUID, db: Session = Depends(get_db)):
    repo = db.get(Repo, repo_id)
    if not repo:
        raise HTTPException(404, "repo not found")
    if not repo.local_path:
        raise HTTPException(400, "repo not cloned yet — run evaluation first")
    report = run_checklist(repo.local_path)
    return report.to_dict()
