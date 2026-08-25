"""
Seed script for synthetic data.

Loads products.csv, suppliers.csv from /data/synthetic and populates the database.
Idempotent - safe to re-run during development.

Usage:
    python -m app.db.seed
"""

import asyncio
import csv
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from app.db.models import BidItem, Bid, Outreach, Product, Supplier
from app.db.session import AsyncSessionLocal, Base, engine, init_db

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data" / "synthetic"


async def seed_products(session: AsyncSessionLocal) -> None:
    """Load products from CSV. Embeddings are generated separately (see embedding_service)."""
    # Clear existing
    await session.execute("TRUNCATE TABLE products CASCADE")
    print("Cleared products table")

    with (DATA_DIR / "products.csv").open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        products = [
            Product(
                sku=row["sku"],
                name=row["name"],
                category=row["category"],
                spec=row["spec"],
            )
            for row in reader
        ]

    session.add_all(products)
    await session.flush()
    print(f"Seeded {len(products)} products")


async def seed_suppliers(session: AsyncSessionLocal) -> None:
    """Load suppliers from CSV."""
    # Clear existing
    await session.execute("TRUNCATE TABLE suppliers CASCADE")
    print("Cleared suppliers table")

    with (DATA_DIR / "suppliers.csv").open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        suppliers = [
            Supplier(
                name=row["name"],
                category=row["category"],
                reliability_score=float(row["reliability_score"]),
                contact_email=row["contact_email"],
            )
            for row in reader
        ]

    session.add_all(suppliers)
    await session.flush()
    print(f"Seeded {len(suppliers)} suppliers")


async def main() -> None:
    """Run the full seed process."""
    print("Starting database seed...")
    await init_db()
    print("Database initialized")

    async with AsyncSessionLocal() as session:
        await seed_products(session)
        await seed_suppliers(session)
        await session.commit()

    print("\nSeed complete!")
    print(f"  Products: {len(list((DATA_DIR / 'products.csv').open())) - 1}")
    print(f"  Suppliers: {len(list((DATA_DIR / 'suppliers.csv').open())) - 1}")


if __name__ == "__main__":
    asyncio.run(main())