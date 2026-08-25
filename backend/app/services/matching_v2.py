"""
Item Matching Service V2 - Uses PostgreSQL + pgvector for semantic search.

This replaces the deterministic in-memory MatchingService with a real embedding-based
semantic search against the product catalog.

Per ARCHITECTURE.md:
- Uses our own Postgres + pgvector (not Context Substrate)
- Generate embeddings for catalog once, store in pgvector
- For each incoming item: embed description → similarity search → top-5 candidates
- Use Claude to re-rank and pick best match with explanation
- Output: {raw_description, matched_sku, confidence, explanation}
"""

import asyncio
from typing import Optional

from anthropic import AsyncAnthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.embedding_service import generate_embedding, search_similar_products
from app.db.models import Product
from app.db.session import get_session
from app.models.pipeline import BidItemInput, MatchedItem
from app.services.text import normalize_text


class MatchingServiceV2:
    """
    Real embedding-based item matching service.

    Architecture (from ARCHITECTURE.md):
    1. Embed incoming item description
    2. Vector similarity search in pgvector (top-5 by category)
    3. Claude re-ranks top-5 and picks best with explanation
    4. Return matched item with confidence and explanation
    """

    def __init__(self, anthropic_api_key: Optional[str] = None) -> None:
        self.anthropic = AsyncAnthropic(api_key=anthropic_api_key) if anthropic_api_key else None
        self._cache: dict[str, MatchedItem] = {}  # Simple in-memory cache for demo

    async def match_item(self, item: BidItemInput, session: AsyncSession) -> MatchedItem:
        """
        Match a single bid item to the best product in the catalog.

        Args:
            item: Bid item to match
            session: Database session

        Returns:
            MatchedItem with sku, confidence, explanation, and source
        """
        # Check cache first (for demo speed)
        cache_key = normalize_text(item.raw_description)
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            return cached.model_copy(update={
                "raw_description": item.raw_description,
                "quantity": item.quantity,
                "category_hint": item.category_hint,
            })

        # Step 1: Generate embedding for the item
        query_embedding = await generate_embedding(item.raw_description)

        # Step 2: Vector similarity search (top-5 candidates)
        candidates = await search_similar_products(
            session=session,
            query_embedding=query_embedding,
            category=item.category_hint,
            limit=5,
        )

        if not candidates:
            # Fallback - no matches found
            return MatchedItem(
                raw_description=item.raw_description,
                quantity=item.quantity,
                category_hint=item.category_hint,
                matched_sku="NO-MATCH",
                matched_name="No match found",
                matched_category="",
                matched_spec="",
                confidence=0.0,
                explanation="No similar products found in catalog",
                source="fresh_match",
            )

        # Step 3: If we have Anthropic, use LLM to re-rank and explain
        if self.anthropic:
            best_match = await self._llm_rerank(item, candidates)
        else:
            # Deterministic fallback: pick top candidate by similarity
            best_match = candidates[0]
            similarity = getattr(best_match, "_similarity", 0.8)
            confidence = round(min(0.98, max(0.55, similarity)), 2)
            best_match = MatchedItem(
                raw_description=item.raw_description,
                quantity=item.quantity,
                category_hint=item.category_hint,
                matched_sku=best_match.sku,
                matched_name=best_match.name,
                matched_category=best_match.category or "",
                matched_spec=best_match.spec or "",
                confidence=confidence,
                explanation=(
                    f"Matched via pgvector similarity search (similarity: {similarity:.2f}). "
                    f"Category: {best_match.category}. Spec: {best_match.spec}. "
                    "This is the deterministic placeholder for embedding search plus LLM reranking."
                ),
                source="fresh_match",
            )

        # Cache the result
        self._cache[cache_key] = best_match
        return best_match

    async def _llm_rerank(self, item: BidItemInput, candidates: list[Product]) -> MatchedItem:
        """
        Use Claude to re-rank candidates and pick the best match with explanation.

        This is the "intelligent" part - LLM understands context, abbreviations,
        and nuance that pure vector similarity might miss.
        """
        # Build prompt with candidates
        candidate_descriptions = []
        for i, c in enumerate(candidates):
            similarity = getattr(c, "_similarity", 0.0)
            candidate_descriptions.append(
                f"{i+1}. SKU: {c.sku} | Name: {c.name} | Category: {c.category} | Spec: {c.spec} | Vector Similarity: {similarity:.2f}"
            )

        prompt = f"""You are Sysco's AST (Assortment Selection Team) expert. Match the customer's requested item to the best Sysco SKU.

Customer Request: "{item.raw_description}"
Quantity: {item.quantity}
Category Hint: {item.category_hint or "Not specified"}

Candidate Sysco Products (pre-ranked by vector similarity):
{chr(10).join(candidate_descriptions)}

Pick the BEST match. Consider:
- Exact product type match (e.g. "2-ply dinner napkins" → 2-ply napkins, not 1-ply or cocktail napkins)
- Packaging/size compatibility
- Category alignment
- Hospital/foodservice context (not retail)

Respond with JSON only:
{{
    "matched_sku": "SKU-HERE",
    "confidence": 0.XX,
    "explanation": "Brief explanation of why this is the best match, referencing specific attributes"
}}"""

        try:
            response = await self.anthropic.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=300,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}],
            )

            import json
            result = json.loads(response.content[0].text)

            matched_sku = result["matched_sku"]
            confidence = float(result["confidence"])
            explanation = result["explanation"]

            # Find the matched product
            matched_product = next((c for c in candidates if c.sku == matched_sku), candidates[0])

            return MatchedItem(
                raw_description=item.raw_description,
                quantity=item.quantity,
                category_hint=item.category_hint,
                matched_sku=matched_product.sku,
                matched_name=matched_product.name,
                matched_category=matched_product.category or "",
                matched_spec=matched_product.spec or "",
                confidence=confidence,
                explanation=explanation,
                source="fresh_match",
            )

        except Exception as e:
            # Fallback to top candidate on any error
            fallback = candidates[0]
            similarity = getattr(fallback, "_similarity", 0.8)
            return MatchedItem(
                raw_description=item.raw_description,
                quantity=item.quantity,
                category_hint=item.category_hint,
                matched_sku=fallback.sku,
                matched_name=fallback.name,
                matched_category=fallback.category or "",
                matched_spec=fallback.spec or "",
                confidence=round(min(0.98, max(0.55, similarity)), 2),
                explanation=f"LLM reranking failed ({type(e).__name__}), using top vector match. Similarity: {similarity:.2f}",
                source="fresh_match",
            )

    async def match_items_batch(self, items: list[BidItemInput], session: AsyncSession) -> list[MatchedItem]:
        """Match multiple items concurrently."""
        tasks = [self.match_item(item, session) for item in items]
        return await asyncio.gather(*tasks)