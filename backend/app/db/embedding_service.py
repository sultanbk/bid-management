"""
Embedding service for generating and storing product embeddings in pgvector.

Uses OpenAI's text-embedding-3-small (1536 dimensions) or Anthropic's embeddings.
Currently uses a local deterministic fallback for demo purposes - replace with real LLM embeddings.

See DATA_MODEL.md for the products table schema with Vector(1536) column.
"""

import asyncio
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Product
from app.db.session import AsyncSessionLocal


# TODO: Replace with real embedding model when available
# from anthropic import AsyncAnthropic
# from openai import AsyncOpenAI

# EMBEDDING_MODEL = "text-embedding-3-small"  # 1536 dims
# EMBEDDING_DIM = 1536


async def generate_embedding(text: str) -> list[float]:
    """
    Generate an embedding for the given text.

    Current implementation: deterministic hash-based fallback for demo.
    Replace with real LLM embedding call (Anthropic/OpenAI) when API keys available.

    Args:
        text: Input text to embed

    Returns:
        List of 1536 floats (vector embedding)
    """
    # Deterministic fallback - hash-based pseudo-embedding for consistent demo behavior
    # This is NOT a real embedding - replace with actual LLM call
    import hashlib

    # Create a deterministic pseudo-embedding from text hash
    hash_bytes = hashlib.sha256(text.encode()).digest()
    # Expand to 1536 dimensions by cycling and combining
    embedding = []
    for i in range(1536):
        byte_idx = i % 32
        # Mix in position for variation
        mixed = (hash_bytes[byte_idx] + (i // 32)) % 256
        # Normalize to [-1, 1] range
        embedding.append((mixed - 127.5) / 127.5)

    return embedding


async def generate_product_embedding(product: Product) -> list[float]:
    """
    Generate embedding for a product based on its name, spec, and category.

    Combines all text fields into a single string for embedding.
    """
    text = f"{product.name} {product.spec or ''} {product.category or ''}"
    return await generate_embedding(text)


async def embed_all_products(session: AsyncSession, batch_size: int = 50) -> int:
    """
    Generate and store embeddings for all products without embeddings.

    Args:
        session: Database session
        batch_size: Process in batches to avoid memory issues

    Returns:
        Number of products updated
    """
    # Find products without embeddings
    result = await session.execute(
        select(Product).where(Product.embedding.is_(None))
    )
    products = result.scalars().all()

    if not products:
        print("All products already have embeddings")
        return 0

    print(f"Generating embeddings for {len(products)} products...")

    updated = 0
    for i, product in enumerate(products):
        embedding = await generate_product_embedding(product)
        product.embedding = embedding
        updated += 1

        if updated % batch_size == 0:
            await session.flush()
            print(f"  Processed {updated}/{len(products)}")

    await session.commit()
    print(f"Embeddings generated for {updated} products")
    return updated


async def get_product_embedding(session: AsyncSession, sku: str) -> Optional[list[float]]:
    """Get the embedding for a specific product by SKU."""
    result = await session.execute(
        select(Product.embedding).where(Product.sku == sku)
    )
    return result.scalar_one_or_none()


async def search_similar_products(
    session: AsyncSession,
    query_embedding: list[float],
    category: Optional[str] = None,
    limit: int = 5,
) -> list[Product]:
    """
    Search for similar products using cosine similarity on pgvector.

    Args:
        session: Database session
        query_embedding: Vector to search for
        category: Optional category filter
        limit: Number of results to return

    Returns:
        List of similar products ordered by similarity (highest first)
    """
    from sqlalchemy import text

    query = text("""
        SELECT p.*, 1 - (embedding <=> :embedding) AS similarity
        FROM products p
        WHERE (:category IS NULL OR p.category = :category)
        ORDER BY embedding <=> :embedding
        LIMIT :limit
    """)

    result = await session.execute(
        query,
        {"embedding": query_embedding, "category": category, "limit": limit}
    )

    products = []
    for row in result.mappings():
        product = Product(
            id=row["id"],
            sku=row["sku"],
            name=row["name"],
            category=row["category"],
            spec=row["spec"],
            embedding=row["embedding"],
            created_at=row["created_at"],
        )
        # Attach similarity score for debugging
        product._similarity = row["similarity"]  # type: ignore
        products.append(product)

    return products


async def main() -> None:
    """CLI entry point to generate all embeddings."""
    async with AsyncSessionLocal() as session:
        await embed_all_products(session)


if __name__ == "__main__":
    asyncio.run(main())