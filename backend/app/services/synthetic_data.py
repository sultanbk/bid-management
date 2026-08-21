import csv
import json
from functools import lru_cache
from pathlib import Path

from app.models.pipeline import BidDocument, Product, Supplier

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data" / "synthetic"

BID_FILE_BY_ID = {
    "bid_a": "bid_a.json",
    "bid-b": "bid_b.json",
    "bid_b": "bid_b.json",
    "bid-a": "bid_a.json",
    "BID-A-001": "bid_a.json",
    "BID-B-002": "bid_b.json",
}


@lru_cache
def load_products() -> list[Product]:
    with (DATA_DIR / "products.csv").open(newline="", encoding="utf-8") as file:
        return [Product.model_validate(row) for row in csv.DictReader(file)]


@lru_cache
def load_suppliers() -> list[Supplier]:
    with (DATA_DIR / "suppliers.csv").open(newline="", encoding="utf-8") as file:
        return [Supplier.model_validate(row) for row in csv.DictReader(file)]


def load_bid_document(bid_id: str) -> BidDocument:
    file_name = BID_FILE_BY_ID.get(bid_id)
    if not file_name:
        supported = ", ".join(sorted(BID_FILE_BY_ID))
        raise ValueError(f"Unknown demo bid '{bid_id}'. Supported values: {supported}, both")

    with (DATA_DIR / file_name).open(encoding="utf-8") as file:
        return BidDocument.model_validate(json.load(file))
