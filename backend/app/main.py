from fastapi import FastAPI

from app.routes.pipeline import router as pipeline_router

app = FastAPI(
    title="Sysco Intelligent Supplier Collaboration Portal",
    version="0.1.0",
    description="Local demo backend for bid matching, outreach, approval, and memory.",
)

app.include_router(pipeline_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
