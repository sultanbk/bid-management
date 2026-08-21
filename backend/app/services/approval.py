from app.models.pipeline import OutreachDraft


class ApprovalService:
    def approve_for_demo(self, drafts: list[OutreachDraft], reviewer: str = "demo_reviewer") -> list[OutreachDraft]:
        return [
            draft.model_copy(update={"status": "approved", "approved_by": reviewer})
            for draft in drafts
        ]
