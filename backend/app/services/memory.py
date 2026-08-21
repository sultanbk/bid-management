from dataclasses import dataclass, field

from app.models.pipeline import BidDocument, MatchedItem, MemoryHit
from app.services.text import normalize_text


@dataclass
class PastBidRecord:
    bid_id: str
    customer_segment: str
    matched_by_description: dict[str, MatchedItem]


@dataclass
class InstitutionalMemoryService:
    records: list[PastBidRecord] = field(default_factory=list)

    def check(self, bid: BidDocument) -> tuple[MemoryHit, dict[str, MatchedItem]]:
        if not self.records:
            return MemoryHit(found=False), {}

        requested = {normalize_text(item.raw_description) for item in bid.items}
        best_record: PastBidRecord | None = None
        best_overlap: set[str] = set()

        for record in self.records:
            if record.customer_segment != bid.customer_segment:
                continue
            overlap = requested & set(record.matched_by_description)
            if len(overlap) > len(best_overlap):
                best_record = record
                best_overlap = overlap

        if not best_record or not best_overlap:
            return MemoryHit(found=False), {}

        reused = {
            description: best_record.matched_by_description[description].model_copy(
                update={"source": "memory_reuse"}
            )
            for description in best_overlap
        }
        return (
            MemoryHit(
                found=True,
                source_bid_id=best_record.bid_id,
                overlap_count=len(best_overlap),
                overlap_ratio=round(len(best_overlap) / len(requested), 2),
                reused_descriptions=sorted(best_overlap),
            ),
            reused,
        )

    def remember(self, bid: BidDocument, matched_items: list[MatchedItem]) -> None:
        matched_by_description = {
            normalize_text(item.raw_description): item.model_copy(update={"source": "fresh_match"})
            for item in matched_items
        }
        self.records = [record for record in self.records if record.bid_id != bid.bid_id]
        self.records.append(
            PastBidRecord(
                bid_id=bid.bid_id,
                customer_segment=bid.customer_segment,
                matched_by_description=matched_by_description,
            )
        )

    def reset(self) -> None:
        self.records.clear()
