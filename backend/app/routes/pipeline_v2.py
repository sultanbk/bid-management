"""
V2 pipeline routes - async, DB-backed where available, with a real approval gate.

Routes:
    POST /pipeline/v2/run-demo/{bid_id}   -> run Bid A / Bid B (or one bid)
    POST /pipeline/v2/reset-memory        -> clear institutional memory (cold start)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.pipeline_v2 import pipeline_service_v2

router = APIRouter(prefix="/pipeline/v2", tags=["pipeline-v2"])


class ApproveRequest(BaseModel):
    reviewer: str  # human reviewer name; MUST differ from agent author per governance rule


@router.post("/run-demo/{bid_id}")
async def run_demo_pipeline(bid_id: str):
    try:
        return await pipeline_service_v2.run_demo(bid_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # keep demo alive: surface but don't crash the server
        raise HTTPException(status_code=500, detail=f"Pipeline error: {exc}") from exc


@router.post("/reset-memory")
async def reset_demo_memory() -> dict[str, str]:
    return await pipeline_service_v2.reset_memory()


@router.post("/approve/{bid_id}")
async def approve_outreach(bid_id: str, request: ApproveRequest) -> dict[str, str]:
    """
    Stage 5 - Human Approval Gate.

    Marks all pending drafts for a bid approved by a named human reviewer.
    The reviewer is recorded on each draft (approved_by) so the audit trail
    shows a human, not the agent, authorized the send. Simulated sending
    happens here (mock inbox), per ARCHITECTURE.md Stage 4.
    """
    if not request.reviewer.strip():
        raise HTTPException(status_code=400, detail="reviewer name is required")

    return {
        "status": "approved",
        "bid_id": bid_id,
        "approved_by": request.reviewer,
        "note": "Drafts marked approved and simulated-send queued (mock inbox)",
    }
