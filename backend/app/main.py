from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import checklist, comparisons, evaluations, export_rlhf, human, repos

app = FastAPI(title="RLHF Repo Eval", version="0.2.0")

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(repos.router, prefix="/api")
app.include_router(evaluations.router, prefix="/api")
app.include_router(human.router, prefix="/api")
app.include_router(comparisons.router, prefix="/api")
app.include_router(export_rlhf.router, prefix="/api")
app.include_router(checklist.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.2.0"}
