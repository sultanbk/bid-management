from app.models.pipeline import DemoRunResponse, MatchedItem, PipelineRun
from app.services.approval import ApprovalService
from app.services.matching import MatchingService
from app.services.memory import InstitutionalMemoryService
from app.services.outreach import OutreachService
from app.services.synthetic_data import load_bid_document, load_products, load_suppliers
from app.services.text import normalize_text
from app.services.tracking import TrackingService


class PipelineService:
    def __init__(self) -> None:
        self.memory = InstitutionalMemoryService()
        self.matcher = MatchingService(load_products())
        self.outreach = OutreachService(load_suppliers())
        self.approval = ApprovalService()
        self.tracking = TrackingService()

    def run_demo(self, requested_bid_id: str) -> DemoRunResponse:
        normalized = requested_bid_id.lower()
        bid_ids = ["bid_a", "bid_b"] if normalized in {"both", "all"} else [requested_bid_id]
        runs = [self._run_one(bid_id) for bid_id in bid_ids]
        return DemoRunResponse(requested_bid_id=requested_bid_id, runs=runs)

    def reset_memory(self) -> dict[str, str]:
        self.memory.reset()
        return {"status": "memory reset"}

    def _run_one(self, bid_id: str) -> PipelineRun:
        bid = load_bid_document(bid_id)
        memory_hit, reused_by_description = self.memory.check(bid)

        matched_items: list[MatchedItem] = []
        for item in bid.items:
            normalized_description = normalize_text(item.raw_description)
            if normalized_description in reused_by_description:
                reused = reused_by_description[normalized_description]
                matched_items.append(
                    reused.model_copy(
                        update={
                            "raw_description": item.raw_description,
                            "quantity": item.quantity,
                            "category_hint": item.category_hint,
                        }
                    )
                )
                continue

            matched_items.append(self.matcher.match_item(item))

        drafts = self.outreach.draft_for_items(bid.bid_id, bid.customer_name, matched_items)
        approved_drafts = self.approval.approve_for_demo(drafts)
        metrics = self.tracking.build_metrics(matched_items, approved_drafts)
        stages = self.tracking.build_stages(
            total_items=metrics.total_items,
            fresh_matches=metrics.fresh_matches,
            reused_items=metrics.memory_reused_items,
            outreach=approved_drafts,
        )

        self.memory.remember(bid, matched_items)

        return PipelineRun(
            bid_id=bid.bid_id,
            customer_name=bid.customer_name,
            customer_segment=bid.customer_segment,
            memory_hit=memory_hit,
            matched_items=matched_items,
            outreach=approved_drafts,
            stages=stages,
            metrics=metrics,
        )


pipeline_service = PipelineService()
