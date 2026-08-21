from typing import Literal

from pydantic import BaseModel, Field


class BidItemInput(BaseModel):
    raw_description: str
    quantity: int
    category_hint: str | None = None


class BidDocument(BaseModel):
    bid_id: str
    customer_name: str
    customer_segment: str
    raw_document_note: str
    items: list[BidItemInput]


class Product(BaseModel):
    sku: str
    name: str
    category: str
    spec: str


class Supplier(BaseModel):
    name: str
    category: str
    reliability_score: float
    contact_email: str


class MatchedItem(BaseModel):
    raw_description: str
    quantity: int
    category_hint: str | None
    matched_sku: str
    matched_name: str
    matched_category: str
    matched_spec: str
    confidence: float = Field(ge=0, le=1)
    explanation: str
    source: Literal["fresh_match", "memory_reuse"]


class MemoryHit(BaseModel):
    found: bool
    source_bid_id: str | None = None
    overlap_count: int = 0
    overlap_ratio: float = 0
    reused_descriptions: list[str] = Field(default_factory=list)


class OutreachDraft(BaseModel):
    raw_description: str
    matched_sku: str
    supplier_name: str
    supplier_email: str
    drafted_message: str
    status: Literal["pending_approval", "approved", "sent"]
    approved_by: str | None = None


class StageSummary(BaseModel):
    name: str
    status: Literal["completed", "skipped"]
    details: str
    items_processed: int = 0


class PipelineMetrics(BaseModel):
    total_items: int
    fresh_matches: int
    memory_reused_items: int
    outreach_drafts: int
    simulated_steps: int
    simulated_steps_saved: int


class PipelineRun(BaseModel):
    bid_id: str
    customer_name: str
    customer_segment: str
    memory_hit: MemoryHit
    matched_items: list[MatchedItem]
    outreach: list[OutreachDraft]
    stages: list[StageSummary]
    metrics: PipelineMetrics


class DemoRunResponse(BaseModel):
    requested_bid_id: str
    runs: list[PipelineRun]
