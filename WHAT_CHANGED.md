# What changed from your original (rlhf-eval → rlhf-eval-best)

## New files
- `backend/app/routers/checklist.py`  — new endpoint `GET /api/checklist/repos/{id}` that runs the full 38-criteria checklist on a cloned repo and returns pass/fail per criterion with ACCEPT/REJECT verdict.

## Modified files

### `backend/app/services/dimensions.py` (major upgrade)
The original had D1-D9 dimension scripts only.  
Now contains **both**:
1. **Full 38-criteria `RepoChecker`** (criteria 1–38 with MUST/SHOULD/CHECK tiers) — same logic as the separate pipeline tool
2. **D1-D9 dimension scripts** (unchanged from your original) — still used by the evaluation runner
3. New helper `run_checklist(repo_path)` callable from anywhere

### `backend/app/routers/export_rlhf.py` (enhanced)
Original had one endpoint: `GET /api/export/jsonl`.  
Now has three:
- `GET /api/export/jsonl` — original format, unchanged
- `GET /api/export/dpo` — **HuggingFace DPO format** (prompt/chosen/rejected/reward_chosen/reward_rejected) — ready for `trl.DPOTrainer`
- `GET /api/export/summary` — lightweight JSON dashboard summary (total repos, avg scores, comparison counts)

### `backend/app/main.py`
Added the checklist router.

## What stayed the same
- All models, schemas, database setup, alembic migrations
- All human annotation: overrides, star ratings, comments
- All comparison (pairwise) logic
- Docker Compose configuration
- Frontend (React/Tailwind)
- Evaluation runner (git clone → D1-D9 → DB)

## New API endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/checklist/repos/{id} | 38-criteria report for a cloned repo |
| GET | /api/export/dpo | HuggingFace DPO JSONL |
| GET | /api/export/summary | Summary JSON |
