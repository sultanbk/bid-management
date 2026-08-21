from fastapi import APIRouter, HTTPException

from app.models.pipeline import DemoRunResponse
from app.services.pipeline import pipeline_service

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.post("/run-demo/{bid_id}", response_model=DemoRunResponse)
def run_demo_pipeline(bid_id: str) -> DemoRunResponse:
    try:
        return pipeline_service.run_demo(bid_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/reset-memory")
def reset_demo_memory() -> dict[str, str]:
    return pipeline_service.reset_memory()
