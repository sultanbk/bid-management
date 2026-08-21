from app.models.pipeline import MatchedItem, OutreachDraft, Supplier


class OutreachService:
    def __init__(self, suppliers: list[Supplier]) -> None:
        self.suppliers = suppliers

    def draft_for_items(self, bid_id: str, customer_name: str, items: list[MatchedItem]) -> list[OutreachDraft]:
        drafts: list[OutreachDraft] = []
        for item in items:
            supplier = self._best_supplier_for_category(item.matched_category)
            if supplier is None:
                continue

            drafts.append(
                OutreachDraft(
                    raw_description=item.raw_description,
                    matched_sku=item.matched_sku,
                    supplier_name=supplier.name,
                    supplier_email=supplier.contact_email,
                    drafted_message=(
                        f"Hello {supplier.name}, please provide pricing for "
                        f"{item.quantity} units of {item.matched_name} "
                        f"({item.matched_spec}) for {customer_name}, bid {bid_id}."
                    ),
                    status="pending_approval",
                )
            )

        return drafts

    def _best_supplier_for_category(self, category: str) -> Supplier | None:
        candidates = [supplier for supplier in self.suppliers if supplier.category == category]
        if not candidates:
            return None
        return max(candidates, key=lambda supplier: supplier.reliability_score)
