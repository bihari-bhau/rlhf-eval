"""
RLHF export router — produces two formats:
  GET /api/export/jsonl    standard JSONL (repo_evaluation + pairwise_comparison)
  GET /api/export/dpo      HuggingFace DPO-format JSONL (prompt/chosen/rejected)
  GET /api/export/summary  lightweight summary JSON
"""
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import DIMENSION_CODES, Evaluation, EvaluationStatus, Repo, RepoComparison

router = APIRouter(prefix="/export", tags=["export"])


def _latest_completed(repo: Repo) -> Evaluation | None:
    done = [e for e in repo.evaluations if e.status == EvaluationStatus.completed]
    return max(done, key=lambda e: e.created_at) if done else None


def _merged_dims(repo: Repo, ev: Evaluation | None) -> dict:
    auto = {c: None for c in DIMENSION_CODES}
    detail = {c: None for c in DIMENSION_CODES}
    if ev:
        for ds in ev.dimension_scores:
            auto[ds.dimension_code] = ds.automated_score
            detail[ds.dimension_code] = ds.detail
    ov = {o.dimension_code: o.human_score for o in repo.overrides}
    return {
        c: {
            "automated_score": auto[c],
            "human_override": ov.get(c),
            "final_score": ov.get(c, auto[c]),
            "detail": detail[c],
        }
        for c in DIMENSION_CODES
    }


def _load_all(db: Session):
    repos = db.scalars(
        select(Repo).options(
            selectinload(Repo.evaluations).selectinload(Evaluation.dimension_scores),
            selectinload(Repo.overrides),
            selectinload(Repo.star_rating),
            selectinload(Repo.comments),
        )
    ).all()
    comps = db.scalars(select(RepoComparison).order_by(RepoComparison.created_at.desc())).all()
    return repos, comps


@router.get("/jsonl")
def export_jsonl(db: Session = Depends(get_db)):
    repos, comps = _load_all(db)
    now = datetime.now(timezone.utc).isoformat()
    lines = []

    for repo in repos:
        ev = _latest_completed(repo)
        lines.append(json.dumps({
            "record_type": "repo_evaluation",
            "repo": {"id": str(repo.id), "github_url": repo.github_url, "full_name": repo.full_name},
            "dimensions": _merged_dims(repo, ev),
            "star_rating_1_to_5": repo.star_rating.stars if repo.star_rating else None,
            "comments": [{"id": str(c.id), "body": c.body, "created_at": c.created_at.isoformat()}
                         for c in repo.comments],
            "exported_at": now,
        }, ensure_ascii=False))

    repo_by_id = {r.id: r for r in repos}
    for cmp in comps:
        ra = repo_by_id.get(cmp.repo_a_id)
        rb = repo_by_id.get(cmp.repo_b_id)
        pid = cmp.preferred_repo_id
        pref = "A" if pid == cmp.repo_a_id else ("B" if pid == cmp.repo_b_id else None)
        lines.append(json.dumps({
            "record_type": "pairwise_comparison",
            "repo_a": {"id": str(cmp.repo_a_id), "full_name": ra.full_name if ra else None},
            "repo_b": {"id": str(cmp.repo_b_id), "full_name": rb.full_name if rb else None},
            "preferred": pref,
            "preferred_repo_id": str(pid) if pid else None,
            "notes": cmp.notes,
            "created_at": cmp.created_at.isoformat(),
            "exported_at": now,
        }, ensure_ascii=False))

    body = "\n".join(lines) + ("\n" if lines else "")
    return Response(content=body, media_type="application/x-ndjson",
                    headers={"Content-Disposition": 'attachment; filename="rlhf_export.jsonl"'})


@router.get("/dpo")
def export_dpo(db: Session = Depends(get_db)):
    """
    HuggingFace DPO-format export.
    For each pairwise comparison with a preference, emits:
    { prompt, chosen_repo, rejected_repo, reward_chosen, reward_rejected, metadata }
    The 'prompt' is the task description, chosen/rejected are repo full_names.
    Scores are derived from final dimension averages.
    """
    repos, comps = _load_all(db)
    repo_by_id = {r.id: r for r in repos}
    now = datetime.now(timezone.utc).isoformat()
    lines = []

    def avg_score(repo: Repo) -> float:
        ev = _latest_completed(repo)
        dims = _merged_dims(repo, ev)
        finals = [v["final_score"] for v in dims.values() if v["final_score"] is not None]
        return sum(finals) / len(finals) if finals else 0.5

    for cmp in comps:
        if cmp.preferred_repo_id is None:
            continue
        ra = repo_by_id.get(cmp.repo_a_id)
        rb = repo_by_id.get(cmp.repo_b_id)
        if not ra or not rb:
            continue
        chosen_repo = ra if cmp.preferred_repo_id == cmp.repo_a_id else rb
        rejected_repo = rb if cmp.preferred_repo_id == cmp.repo_a_id else ra
        lines.append(json.dumps({
            "prompt": f"Evaluate this Python repository for RLHF benchmark inclusion: ",
            "chosen": chosen_repo.full_name,
            "rejected": rejected_repo.full_name,
            "reward_chosen": round(avg_score(chosen_repo), 4),
            "reward_rejected": round(avg_score(rejected_repo), 4),
            "metadata": {
                "comparison_id": str(cmp.id),
                "notes": cmp.notes,
                "created_at": cmp.created_at.isoformat(),
                "exported_at": now,
            },
        }, ensure_ascii=False))

    body = "\n".join(lines) + ("\n" if lines else "")
    return Response(content=body, media_type="application/x-ndjson",
                    headers={"Content-Disposition": 'attachment; filename="dpo_export.jsonl"'})


@router.get("/summary")
def export_summary(db: Session = Depends(get_db)):
    """Lightweight JSON summary of all repos and their scores."""
    repos, comps = _load_all(db)
    now = datetime.now(timezone.utc).isoformat()
    out = {
        "exported_at": now,
        "total_repos": len(repos),
        "total_comparisons": len(comps),
        "repos": [],
        "comparisons_with_preference": sum(1 for c in comps if c.preferred_repo_id),
    }
    for repo in repos:
        ev = _latest_completed(repo)
        dims = _merged_dims(repo, ev)
        finals = [v["final_score"] for v in dims.values() if v["final_score"] is not None]
        avg = round(sum(finals) / len(finals), 3) if finals else None
        out["repos"].append({
            "id": str(repo.id),
            "full_name": repo.full_name,
            "avg_dimension_score": avg,
            "star_rating": repo.star_rating.stars if repo.star_rating else None,
            "comment_count": len(repo.comments),
            "evaluated": ev is not None,
        })
    return out
