from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.db.session import init_db, close_db
from app.routes.pipeline import router as pipeline_router
from app.routes.pipeline_v2 import router as pipeline_v2_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - initialize and close database."""
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="Sysco Intelligent Supplier Collaboration Portal",
    version="0.1.0",
    description="Local demo backend for bid matching, outreach, approval, and memory.",
    lifespan=lifespan,
)

app.include_router(pipeline_router)
app.include_router(pipeline_v2_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db")
async def db_health_check() -> dict[str, str]:
    """Check database connectivity."""
    try:
        from app.db.session import engine
        from sqlalchemy import text
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}