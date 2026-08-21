from app.models.pipeline import MatchedItem, OutreachDraft, PipelineMetrics, StageSummary


class TrackingService:
    def build_stages(
        self,
        total_items: int,
        fresh_matches: int,
        reused_items: int,
        outreach: list[OutreachDraft],
    ) -> list[StageSummary]:
        memory_status = "completed" if reused_items else "completed"
        memory_details = (
            f"Reused {reused_items} item matches from institutional memory."
            if reused_items
            else "No reusable bid memory found; all items used fresh matching."
        )

        return [
            StageSummary(
                name="Bid document intake",
                status="completed",
                details=f"Loaded {total_items} structured items from synthetic bid data.",
                items_processed=total_items,
            ),
            StageSummary(
                name="Item Matching Service",
                status="completed",
                details=f"Matched {fresh_matches} items locally against the synthetic catalog.",
                items_processed=fresh_matches,
            ),
            StageSummary(
                name="Institutional Memory Check",
                status=memory_status,
                details=memory_details,
                items_processed=reused_items,
            ),
            StageSummary(
                name="Outreach Agent",
                status="completed",
                details=f"Drafted {len(outreach)} supplier outreach messages.",
                items_processed=len(outreach),
            ),
            StageSummary(
                name="Human Approval Gate",
                status="completed",
                details="Demo reviewer approved all drafts; no communication was sent automatically.",
                items_processed=len(outreach),
            ),
            StageSummary(
                name="Tracking Dashboard",
                status="completed",
                details="Run summary is ready for dashboard rendering and memory writeback.",
                items_processed=total_items,
            ),
        ]

    def build_metrics(self, items: list[MatchedItem], outreach: list[OutreachDraft]) -> PipelineMetrics:
        total_items = len(items)
        reused = len([item for item in items if item.source == "memory_reuse"])
        fresh = total_items - reused
        full_steps = total_items * 3
        simulated_steps = fresh * 3 + reused

        return PipelineMetrics(
            total_items=total_items,
            fresh_matches=fresh,
            memory_reused_items=reused,
            outreach_drafts=len(outreach),
            simulated_steps=simulated_steps,
            simulated_steps_saved=max(0, full_steps - simulated_steps),
        )
