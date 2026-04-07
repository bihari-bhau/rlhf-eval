# Deployment Guide

## Prerequisites
- Docker Desktop (or Docker Engine + Compose plugin)
- Git
- Node 20+ (for frontend dev only)

---

## Option 1: Full Docker Compose (recommended)

```bash
# 1. Clone / copy this project
cd rlhf-eval-best

# 2. Start the stack (Postgres + API)
docker compose up --build -d

# 3. Run migrations
docker compose exec api alembic upgrade head

# 4. Start frontend dev server (separate terminal)
cd frontend
npm install
npm run dev
# → opens http://localhost:5173
```

**Services:**
- API: http://localhost:8000  (FastAPI + auto-docs at /docs)
- DB:  localhost:5432 (postgres/postgres/rlhf_eval)

---

## Option 2: Local dev (no Docker)

### Backend
```bash
cd backend

# Create virtualenv
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate

# Install deps
pip install -r requirements.txt

# Set env vars
export DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/rlhf_eval
export CLONE_BASE_DIR=/tmp/repos
export CORS_ORIGINS=http://localhost:5173

# Start Postgres separately (or use Docker just for DB):
docker run -d --name pg -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=rlhf_eval -p 5432:5432 postgres:16-alpine

# Run migrations
alembic upgrade head

# Start API
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## Option 3: Production (single server)

```bash
# Build frontend into static files
cd frontend
npm run build          # → dist/

# Serve with nginx reverse-proxy:
# - /         → serve dist/index.html (SPA)
# - /api/*    → proxy_pass http://127.0.0.1:8000

# Run API with gunicorn
pip install gunicorn
gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 4 -b 127.0.0.1:8000
```

Example nginx snippet:
```nginx
server {
    listen 80;
    root /var/www/rlhf-eval/frontend/dist;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | postgresql+psycopg://postgres:postgres@db:5432/rlhf_eval | SQLAlchemy DB URL |
| `CLONE_BASE_DIR` | /data/repos | Where git repos are cloned |
| `CORS_ORIGINS` | http://localhost:5173 | Comma-separated allowed origins |

---

## New API endpoints (added in this version)

| Endpoint | Description |
|---|---|
| `GET /api/checklist/repos/{id}` | 38-criteria ACCEPT/REJECT report for a cloned repo |
| `GET /api/export/dpo` | HuggingFace DPO format JSONL (chosen/rejected pairs) |
| `GET /api/export/summary` | Lightweight JSON summary of all repos + scores |
| `GET /api/export/jsonl` | Original full JSONL export (unchanged) |
| `GET /docs` | FastAPI Swagger UI (all endpoints) |

---

## Running the 38-criteria checklist

After adding a repo and running its evaluation (which clones it locally):

```bash
# Via API
curl http://localhost:8000/api/checklist/repos/<repo-uuid>

# Response includes:
# {
#   "verdict": "ACCEPT" or "REJECT",
#   "pass_count": 31,
#   "fail_count": 7,
#   "results": [ { "number": 1, "description": "...", "category": "MUST", "passed": true, "note": "..." }, ... ]
# }
```

## Exporting for HuggingFace DPO training

```bash
# Download DPO JSONL
curl http://localhost:8000/api/export/dpo > dpo_export.jsonl

# Use with trl DPOTrainer:
from datasets import load_dataset
dataset = load_dataset("json", data_files="dpo_export.jsonl")
```
