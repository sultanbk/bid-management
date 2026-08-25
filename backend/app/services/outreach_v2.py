"""
Outreach Agent V2 - The Agent Hub-registered agent.

Per ARCHITECTURE.md Stage 4 and AGENT_MANIFESTS.md:
- This IS the Agent Hub-governed agent (autonomy_level: low)
- Drafts supplier outreach via Claude; NEVER sends without Stage 5 approval
- allowed_actions:   draft_supplier_email, parse_supplier_reply, update_outreach_status
- forbidden_actions: send_email_without_approval, modify_final_pricing,
                     contact_suppliers_outside_matched_list

Governance properties honored here:
- Drafts are produced with status "pending_approval" — never "sent"
- approved_by must be recorded separately (human reviewer, not the agent)
- For the demo, "sending" is simulated (mock inbox), per ARCHITECTURE.md Stage 4
"""

from typing import Optional

from anthropic import AsyncAnthropic

from app.models.pipeline import MatchedItem, OutreachDraft, Supplier


class OutreachServiceV2:
    """
    Claude-powered outreach drafting with supplier selection.

    Supplier selection strategy: highest reliability_score among suppliers
    serving the matched product's category. (Ranking/selection intelligence
    is Use Case 2 — NOT this cycle. # SYNTHETIC: reliability scores are
    synthetic values chosen so selection has something meaningful to work with.)
    """

    def __init__(
        self,
        suppliers: list[Supplier],
        anthropic_api_key: Optional[str] = None,
    ) -> None:
        self.suppliers = suppliers
        self.anthropic = AsyncAnthropic(api_key=anthropic_api_key) if anthropic_api_key else None

    def draft_for_items(
        self,
        bid_id: str,
        customer_name: str,
        items: list[MatchedItem],
        reused_supplier_by_sku: Optional[dict[str, str]] = None,
    ) -> list[OutreachDraft]:
        """
        Draft one outreach message per matched item.

        Args:
            bid_id: Demo bid identifier (e.g. BID-B-002)
            customer_name: End customer the bid is for
            items: Matched items to request pricing for
            reused_supplier_by_sku: Optional map of sku -> supplier name carried over
                from institutional memory (Stage 3). When present, memory reuse wins
                over fresh reliability ranking — this is what makes Bid B visibly
                cheaper/faster than Bid A in the demo.

        Returns:
            Drafts with status="pending_approval". This method never returns
            drafts in any post-approval state — approval happens in Stage 5 only.
        """
        reused_supplier_by_sku = reused_supplier_by_sku or {}
        drafts: list[OutreachDraft] = []

        for item in items:
            if item.matched_sku == "NO-MATCH":
                continue  # nothing to source — surfaced in matching results instead

            supplier = self._select_supplier(item, reused_supplier_by_sku)
            if supplier is None:
                continue  # no supplier covers this category; logged in tracking stage

            drafts.append(
                OutreachDraft(
                    raw_description=item.raw_description,
                    matched_sku=item.matched_sku,
                    supplier_name=supplier.name,
                    supplier_email=supplier.contact_email,
                    drafted_message=self._draft_message(bid_id, customer_name, item, supplier),
                    status="pending_approval",
                    approved_by=None,
                )
            )

        return drafts

    def _select_supplier(
        self,
        item: MatchedItem,
        reused_supplier_by_sku: dict[str, str],
    ) -> Optional[Supplier]:
        """Pick the supplier for an item: memory reuse first, then reliability rank."""
        remembered_name = reused_supplier_by_sku.get(item.matched_sku)
        if remembered_name:
            remembered = next((s for s in self.suppliers if s.name == remembered_name), None)
            if remembered is not None:
                return remembered

        return self._best_supplier_for_category(item.matched_category)

    def _best_supplier_for_category(self, category: str) -> Optional[Supplier]:
        candidates = [s for s in self.suppliers if s.category == category]
        if not candidates:
            return None
        return max(candidates, key=lambda s: s.reliability_score)

    def _draft_message(
        self,
        bid_id: str,
        customer_name: str,
        item: MatchedItem,
        supplier: Supplier,
    ) -> str:
        """Draft the RFQ message. Uses Claude when configured; template otherwise."""
        if self.anthropic:
            message = self._claude_draft(bid_id, customer_name, item, supplier)
            if message:
                return message
            # fall through to template on any LLM failure
        return self._template_draft(bid_id, customer_name, item, supplier)

    def _template_draft(
        self,
        bid_id: str,
        customer_name: str,
        item: MatchedItem,
        supplier: Supplier,
    ) -> str:
        """Deterministic template — the reliable demo path (no API dependency)."""
        return (
            f"Hello {supplier.name},\n\n"
            f"We are sourcing pricing on behalf of {customer_name} ({bid_id}).\n\n"
            f"Requested item : {item.raw_description}\n"
            f"Matched SKU    : {item.matched_sku} — {item.matched_name}\n"
            f"Specification  : {item.matched_spec}\n"
            f"Quantity       : {item.quantity} units\n\n"
            f"Please reply with your unit price, lead time, and delivery terms.\n\n"
            f"Thank you,\nSysco Bid Management Team"
        )

    def _claude_draft(
        self,
        bid_id: str,
        customer_name: str,
        item: MatchedItem,
        supplier: Supplier,
    ) -> Optional[str]:
        """
        Claude-drafted RFQ. Synchronous wrapper around the async API call;
        returns None on any failure so the caller can fall back to the template.
        """
        prompt = f"""Draft a short, professional RFQ email from Sysco's bid management team to a supplier.

To: {supplier.name} <{supplier.contact_email}>
Bid: {bid_id}
End customer: {customer_name}

Item requested: {item.raw_description}
Matched SKU: {item.matched_sku} - {item.matched_name}
Spec: {item.matched_spec}
Quantity: {item.quantity} units

Requirements:
- Ask for unit price, lead time, and delivery terms
- Under 120 words, no markdown, plain text email body only
- Do not invent prices, deadlines, or commitments

Return ONLY the email body text."""

        try:
            import asyncio

            async def _call() -> str:
                response = await self.anthropic.messages.create(
                    model="claude-3-5-haiku-20241022",
                    max_tokens=400,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.content[0].text.strip()

            return asyncio.run(_call())
        except Exception:
            # Any LLM/network error -> template path keeps the demo unbreakable
            return None
