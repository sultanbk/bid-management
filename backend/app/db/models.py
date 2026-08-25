"""
SQLAlchemy models for the PostgreSQL + pgvector database.

These models correspond to the tables defined in DATA_MODEL.md:
- products (catalog with embeddings)
- suppliers
- bids
- bid_items
- outreach

All data is synthetic until real Sysco data access is available.
Mark any assumption tied to synthetic data with `-- SYNTHETIC` in migration files.
"""

import uuid
from datetime import datetime
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class Product(Base):
    """Product catalog - ~500-1000 synthetic SKUs with embeddings for semantic search."""

    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku = Column(String(50), unique=True, nullable=False)
    name = Column(Text, nullable=False)
    category = Column(String(100))
    spec = Column(Text)  # e.g. "2-ply, case of 24"
    embedding = Column(Vector(1536))  # OpenAI text-embedding-3-small dimension
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    bid_items = relationship("BidItem", back_populates="matched_product")

    __table_args__ = (
        Index("ix_products_embedding", "embedding", postgresql_using="ivfflat", postgresql_ops={"embedding": "vector_cosine_ops"}),
        Index("ix_products_category", "category"),
    )

    def __repr__(self):
        return f"<Product(sku='{self.sku}', name='{self.name}')>"


class Supplier(Base):
    """Supplier catalog - ~20-30 synthetic suppliers with reliability scores."""

    __tablename__ = "suppliers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    category = Column(String(100))  # which product categories they serve
    reliability_score = Column(Numeric(3, 2))  # synthetic, 0.00-1.00
    contact_email = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    outreach = relationship("Outreach", back_populates="supplier")

    __table_args__ = (
        Index("ix_suppliers_category", "category"),
    )

    def __repr__(self):
        return f"<Supplier(name='{self.name}', category='{self.category}')>"


class Bid(Base):
    """Bid records - one per incoming customer bid document."""

    __tablename__ = "bids"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_name = Column(Text)
    customer_segment = Column(String(50))  # e.g. "hospital", "restaurant chain"
    raw_document = Column(Text)  # original extracted text, for reference
    status = Column(String(30), default="received")
    context_substrate_ref = Column(Text)  # ID/handle for this bid's record in Context Substrate
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    items = relationship("BidItem", back_populates="bid", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_bids_customer_segment", "customer_segment"),
        Index("ix_bids_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<Bid(id='{self.id}', customer='{self.customer_name}')>"


class BidItem(Base):
    """Individual line items within a bid, with matched SKU and confidence."""

    __tablename__ = "bid_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bid_id = Column(UUID(as_uuid=True), ForeignKey("bids.id", ondelete="CASCADE"), nullable=False)
    raw_description = Column(Text)
    quantity = Column(Integer)
    matched_sku = Column(String(50), ForeignKey("products.sku"))
    match_confidence = Column(Numeric(3, 2))
    match_explanation = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    bid = relationship("Bid", back_populates="items")
    matched_product = relationship("Product", back_populates="bid_items")
    outreach = relationship("Outreach", back_populates="bid_item", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_bid_items_bid_id", "bid_id"),
        Index("ix_bid_items_matched_sku", "matched_sku"),
    )

    def __repr__(self):
        return f"<BidItem(bid_id='{self.bid_id}', sku='{self.matched_sku}')>"


class Outreach(Base):
    """Outreach drafts to suppliers for matched bid items."""

    __tablename__ = "outreach"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bid_item_id = Column(UUID(as_uuid=True), ForeignKey("bid_items.id", ondelete="CASCADE"), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    drafted_message = Column(Text)
    status = Column(String(30), default="drafted")  # drafted -> pending_approval -> approved -> sent -> responded
    quoted_price = Column(Numeric(10, 2))
    approved_by = Column(Text)  # must differ from the agent/author, per governance rule
    approved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    bid_item = relationship("BidItem", back_populates="outreach")
    supplier = relationship("Supplier", back_populates="outreach")

    __table_args__ = (
        Index("ix_outreach_bid_item_id", "bid_item_id"),
        Index("ix_outreach_supplier_id", "supplier_id"),
        Index("ix_outreach_status", "status"),
    )

    def __repr__(self):
        return f"<Outreach(id='{self.id}', status='{self.status}')>"