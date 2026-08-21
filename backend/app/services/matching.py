from app.models.pipeline import BidItemInput, MatchedItem, Product
from app.services.text import token_set


class MatchingService:
    def __init__(self, products: list[Product]) -> None:
        self.products = products

    def match_item(self, item: BidItemInput) -> MatchedItem:
        candidates = [
            product
            for product in self.products
            if item.category_hint is None or product.category == item.category_hint
        ]
        best_product = max(candidates or self.products, key=lambda product: self._score(item, product))
        confidence = round(min(0.98, 0.55 + self._score(item, best_product) * 0.08), 2)

        return MatchedItem(
            raw_description=item.raw_description,
            quantity=item.quantity,
            category_hint=item.category_hint,
            matched_sku=best_product.sku,
            matched_name=best_product.name,
            matched_category=best_product.category,
            matched_spec=best_product.spec,
            confidence=confidence,
            explanation=(
                "Matched locally using category hint and token overlap against the "
                "synthetic catalog. This is the deterministic placeholder for "
                "embedding search plus LLM reranking."
            ),
            source="fresh_match",
        )

    def _score(self, item: BidItemInput, product: Product) -> float:
        item_tokens = token_set(item.raw_description)
        product_tokens = token_set(f"{product.name} {product.spec} {product.category}")
        if not item_tokens:
            return 0

        overlap = len(item_tokens & product_tokens)
        spec_bonus = 1 if any(token in product_tokens for token in item_tokens if token.isdigit()) else 0
        return overlap + spec_bonus
