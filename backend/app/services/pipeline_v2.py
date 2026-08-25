"""
Pipeline Orchestrator V2 - wires the real service stack end to end.

Stage wiring (per ARCHITECTURE.md):
  1. Bid intake            -> synthetic_data loader (Claude extraction lands Week 2+)
  2. Item Matching         -> MatchingServiceV2 (pgvector + optional Claude re-rank)
  3. Institutional Memory  -> InstitutionalMemoryServiceV2 (Context Substrate-shaped)
  4. Outreach Agent        -> OutreachServiceV2 (Agent Hub-governed; drafts only)
  5. Human Approval Gate   -> explicit approve endpoint (never auto-approved in v2)
  6. Tracking              -> metrics + stage summaries; writes memory back at the end

Resilience rules (from DATA_MODEL.md "Notes for whoever's coding this"):
- Every external dependency (Postgres, Claude API) degrades gracefully:
  DB down -> CSV catalog fallback; Claude unavailable -> deterministic scoring.
  The demo must not hard-fail because a sandbox is slow or unreachable.
"""

import asyncio
import logging
import os
import time
from datetime import datetime

from app.models.pipeline import (
    BidDocument,
    DemoRunResponse,
    MatchedItem,
    MemoryHit,
    OutreachDraft,
    PipelineMetrics,
    PipelineRun,
    StageSummary,
)
from app.services.matching import MatchingService as MatchingServiceFallback
from app.services.matching_v2 import MatchingServiceV2
from app.services.memory_v2 import InstitutionalMemoryServiceV2
from app.services.outreach import OutreachService as OutreachServiceFallback
from app.services.outreach_v2 import OutreachServiceV2
from app.services.synthetic_data import load_bid_document, load_products, load_suppliers
from app.services.text import normalize_text

logger = logging.getLogger("pipeline_v2")


def _anthropic_key() -> str | None:
    return os.getenv("ANTHROPIC_API_KEY") or None


class PipelineServiceV2:
    """
    Async pipeline over the V2 services.

    Unlike the V1 demo pipeline (which auto-approved drafts to keep the old
    frontend simple), V2 stops at `pending_approval`. Approval is an explicit,
    separate API call — that separation IS the governance story we pitch.
    """

    def __init__(self) -> None:
        self.memory = InstitutionalMemoryServiceV2()
        self._matcher_v2: MatchingServiceV2 | None = None
        self._outreach_v2: OutreachServiceV2 | None = None
        self._db_available: bool | None = None

    # ------------------------------------------------------------------ setup

    def _services(self) -> tuple[MatchingServiceV2, OutreachServiceV2]:
        """Lazily construct V2 services so import cost isn't paid at module load."""
        if self._matcher_v2 is None:
            api_key = _anthropic_key()
            self._matcher_v2 = MatchingServiceV2(anthropic_api_key=api_key)
            self._outreach_v2 = OutreachServiceV2(load_suppliers(), anthropic_api_key=api_key)
        return self._matcher_v2, self._outreach_v2

    async def _check_db(self) -> bool:
        """One-time database reachability probe; result cached for process lifetime."""
        if self._db_available is None:
            try:
                from sqlalchemy import text

                from app.db.session import engine

                async with engine.begin() as conn:
                    await conn.execute(text("SELECT 1"))
                self._db_available = True
            except Exception as exc:  # DB down / not seeded yet -> CSV fallback
                logger.warning("Postgres unavailable (%s); using CSV catalog fallback", exc)
                self._db_available = False
        return self._db_available

    # ------------------------------------------------------------------- runs

    async def run_demo(self, requested_bid_id: str) -> DemoRunResponse:
        normalized = requested_bid_id.lower()
        bid_ids = ["bid_a", "bid_b"] if normalized in {"both", "all"} else [requested_bid_id]
        runs = [await self._run_one(bid_id) for bid_id in bid_ids]
        return DemoRunResponse(requested_bid_id=requested_bid_id, runs=runs)

    async def reset_memory(self) -> dict[str, str]:
        self.memory.reset()
        return {"status": "memory reset"}

    # -------------------------------------------------------------- one bid

    async def _run_one(self, bid_id: str) -> PipelineRun:
        run_started = time.perf_counter()

        bid = load_bid_document(bid_id)

        # Stage 1 — intake summary (extraction is scripted until BEx-style parsing lands)
        stages: list[StageSummary] = [
            StageSummary(
                name="Bid document intake",
                status="completed",
                details=f"Loaded {len(bid.items)} items for {bid.customer_name}",
                items_processed=len(bid.items),
            )
        ]

        # Stage 3 — institutional memory check (BEFORE matching, per architecture)
        memory_hit, reused_by_description = await self.memory.check(bid)
        stages.append(self._memory_stage_summary(memory_hit))

        # Stage 2 — item matching (skipped per-item when memory covers it)
        matched_items = await self._match_items(bid, reused_by_description)
        fresh = sum(1 for m in matched_items if m.source == "fresh_match")
        reused_count = sum(1 for m in matched_items if m.source == "memory_reuse")
        stages.append(
            StageSummary(
                name="Item Matching Service",
                status="completed" if fresh else "skipped",
                details=f"{fresh} fresh matches ({self._matching_backend()}), {reused_count} reused from memory",
                items_processed=fresh,
            )
        )

        # Stage 4 — outreach drafting (drafts only; carries supplier reuse forward)
        drafts = await self._draft_outreach(bid, matched_items)
        stages.append(
            StageSummary(
                name="Outreach Agent",
                status="completed",
                details=f"{len(drafts)} drafts queued for approval (Agent Hub-governed, autonomy: low)",
                items_processed=len(drafts),
            )
        )

        # Stage 5 — human approval gate: NOT auto-executed in v2.
        stages.append(
            StageSummary(
                name="Human Approval Gate",
                status="completed",
                details=f"Awaiting reviewer action on {len(drafts)} draft(s)",
                items_processed=len(drafts),
            )
        )

        metrics = self._build_metrics(matched_items, drafts, run_started)

        # Stage 6 — tracking + write-back into institutional memory
        await self.memory.remember(bid, matched_items)
        stages.append(
            StageSummary(
                name="Tracking Dashboard",
                status="completed",
                details="Run recorded; narrative stored to institutional memory",
                items_processed=len(matched_items),
            )
        )

        return PipelineRun(
            bid_id=bid.bid_id,
            customer_name=bid.customer_name,
            customer_segment=bid.customer_segment,
            memory_hit=memory_hit,
            matched_items=matched_items,
            outreach=drafts,
            stages=stages,
            metrics=metrics,
        )

    # ------------------------------------------------------------ stage impls

    async def _match_items(
        self,
        bid: BidDocument,
        reused_by_description: dict[str, MatchedItem],
    ) -> list[MatchedItem]:
        matched: list[MatchedItem] = []

        # Split items into memory-reused vs needs-fresh-matching
        fresh_items = []
        for item in bid.items:
            key = normalize_text(item.raw_description)
            if key in reused_by_description:
                reused = reused_by_description[key]
                matched.append(
                    reused.model_copy(
                        update={
                            "raw_description": item.raw_description,
                            "quantity": item.quantity,
                            "category_hint": item.category_hint,
                        }
                    )
                )
            else:
                fresh_items.append(item)

        if not fresh_items:
            return matched

        use_db = await self._check_db()

        if use_db:
            matcher, _ = self._services()
            from app.db.session import get_session

            try:
                async with get_session() as session:
                    results = await asyncio.gather(
                        *(matcher.match_item(item, session) for item in fresh_items)
                    )
                matched.extend(results)
                return matched
            except Exception as exc:
                logger.warning("pgvector matching failed (%s); falling back to CSV scorer", exc)

        # Fallback path — deterministic token-overlap matcher over the CSV catalog
        fallback_matcher = MatchingServiceFallback(load_products())
        matched.extend(fallback_matcher.match_item(item) for item in fresh_items)
        return matched

    def _matching_backend(self) -> str:
        return "pgvector" if self._db_available else "CSV fallback"

    async def _draft_outreach(
        self,
        bid: BidDocument,
        matched_items: list[MatchedItem],
    ) -> list[OutreachDraft]:
        _, outreach = self._services()

        # Carry supplier picks from memory forward: sku -> supplier name.
        # In the full build this mapping comes back from Context Substrate with
        # the memory hit; for now the memory service returns matches only, so
        # reuse is expressed through the reused MatchedItems themselves and
        # supplier selection falls to reliability ranking. Kept as a parameter
        # so wiring the real substrate response is a data-plumb, not a rewrite.
        reused_supplier_by_sku: dict[str, str] = {}

        drafts = outreach.draft_for_items(
            bid_id=bid.bid_id,
            customer_name=bid.customer_name,
            items=matched_items,
            reused_supplier_by_sku=reused_supplier_by_sku,
        )
        return drafts

    def _memory_stage_summary(self, hit: MemoryHit) -> StageSummary:
        if hit.found:
            return StageSummary(
                name="Institutional Memory Check",
                status="completed",
                details=(
                    f"Match found: past bid {hit.source_bid_id}, "
                    f"{hit.overlap_count} overlapping items "
                    f"({int(hit.overlap_ratio * 100)}% overlap)"
                ),
                items_processed=hit.overlap_count,
            )
        return StageSummary(
            name="Institutional Memory Check",
            status="completed",
            details="No similar past bid found - cold start",
        )

    # ------------------------------------------------------------- metrics

    def _build_metrics(
        self,
        matched_items: list[MatchedItem],
        drafts: list[OutreachDraft],
        started_at: float,
    ) -> PipelineMetrics:
        fresh_matches = sum(1 for m in matched_items if m.source == "fresh_match")
        reused = sum(1 for m in matched_items if m.source == "memory_reuse")

        # Simulated step accounting (what the dashboard compares across bids).
        # A fresh match costs 3 steps (search catalog, verify spec, select
        # supplier); a memory-reused item costs 0. Drafting is 1 step per RFQ
        # regardless of source.  # SYNTHETIC: step costs are demo constants.
        STEPS_PER_FRESH_MATCH = 3
        simulated_steps = fresh_matches * STEPS_PER_FRESH_MATCH + len(drafts)
        simulated_steps_saved = reused * STEPS_PER_FRESH_MATCH

        return PipelineMetrics(
            total_items=len(matched_items),
            fresh_matches=fresh_matches,
            memory_reused_items=reused,
            outreach_drafts=len(drafts),
            simulated_steps=simulated_steps,
            simulated_steps_saved=simulated_steps_saved,
        )


# Module-level singleton, mirroring the V1 pattern so routes stay thin.
pipeline_service_v2 = PipelineServiceV2()
