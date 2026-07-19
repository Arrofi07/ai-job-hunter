from fastapi import FastAPI

from app.jobs.routes import router as jobs_router
from app.resume.routes import router as resume_router

app = FastAPI(title="AI Job Hunter")
app.include_router(resume_router)
app.include_router(jobs_router)


@app.get("/health")
def health():
    return {"status": "ok"}