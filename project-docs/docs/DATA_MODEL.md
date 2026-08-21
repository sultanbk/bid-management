# Data Model

Two systems, split by data shape — see `ARCHITECTURE.md` → "Data source
split" for the full reasoning (decided after the Context Substrate
workshop with Sivaraman K Lakshmanan):

- **PostgreSQL + `pgvector`** — for the product catalog (`products`) and
  suppliers (`suppliers`). Row-per-record structured data, which the Synapt
  team flagged as a poor fit for Context Substrate.
- **Synapt Context Substrate** — for institutional memory (past bid
  narratives). Document/narrative-shaped data, which is exactly what
  Context Substrate is built to ingest and query. No table schema needed
  here — you ingest a written summary per completed bid and query it with
  a prompt; Context Substrate handles chunking, graph relationships, and
  retrieval internally.

The tables below (`products`, `suppliers`, `bids`, `bid_items`, `outreach`)
live in our own Postgres. **`past_bids` (further down) has moved to Context
Substrate and is no longer a Postgres table** — see that section for what
replaces it.

All data is **synthetic** until real Sysco data access is available. Mark
any assumption tied to synthetic data with `-- SYNTHETIC` in migration files
so it's easy to find when swapping to real data later.

## Tables

### `products` (the catalog)
```sql
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku VARCHAR(50) UNIQUE NOT NULL,
    name TEXT NOT NULL,
    category VARCHAR(100),
    spec TEXT,               -- e.g. "2-ply, case of 24"
    embedding vector(1536),  -- match to your embedding model's dimension
    created_at TIMESTAMP DEFAULT now()
);
CREATE INDEX ON products USING ivfflat (embedding vector_cosine_ops);
```
Target: ~500–1,000 synthetic SKUs across a handful of categories
(paper/disposables, proteins, produce, dry goods, kitchen equipment) —
enough variety to make matching demo-convincing without needing the full
275K-SKU realism.

### `suppliers`
```sql
CREATE TABLE suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    category VARCHAR(100),          -- which product categories they serve
    reliability_score NUMERIC(3,2), -- synthetic, 0.00-1.00
    contact_email TEXT,
    created_at TIMESTAMP DEFAULT now()
);
```
Target: ~20–30 synthetic suppliers, a few per category, with varied
reliability scores so ranking/selection has something meaningful to work
with later (Use Case 2, not this cycle — but keep the field so the schema
doesn't need rework in Phase 2).

### `bids`
```sql
CREATE TABLE bids (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_name TEXT,
    customer_segment VARCHAR(50),  -- e.g. "hospital", "restaurant chain"
    raw_document TEXT,             -- original extracted text, for reference
    status VARCHAR(30) DEFAULT 'received',
    context_substrate_ref TEXT,    -- ID/handle for this bid's record in Context Substrate, once memory is ingested there
    created_at TIMESTAMP DEFAULT now()
);
```
No local embedding column here — bid-level similarity for institutional
memory is handled by Context Substrate now, not by a `pgvector` column on
this table. `context_substrate_ref` just lets us look up the corresponding
record there if needed (e.g. for debugging or displaying "matched to past
bid X" in the dashboard).

### `bid_items`
```sql
CREATE TABLE bid_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bid_id UUID REFERENCES bids(id),
    raw_description TEXT,
    quantity INTEGER,
    matched_sku VARCHAR(50) REFERENCES products(sku),
    match_confidence NUMERIC(3,2),
    match_explanation TEXT,
    created_at TIMESTAMP DEFAULT now()
);
```

### `outreach`
```sql
CREATE TABLE outreach (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bid_item_id UUID REFERENCES bid_items(id),
    supplier_id UUID REFERENCES suppliers(id),
    drafted_message TEXT,
    status VARCHAR(30) DEFAULT 'drafted',  -- drafted -> pending_approval -> approved -> sent -> responded
    quoted_price NUMERIC(10,2),
    approved_by TEXT,               -- must differ from the agent/author, per governance rule
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT now()
);
```

### Institutional memory — now lives in Synapt Context Substrate, not Postgres

No `past_bids` table. Instead, at the end of Stage 6 (Tracking Dashboard),
for every completed bid, **ingest a short narrative document into Context
Substrate** describing what happened — this is what closes the loop and
makes Bid B faster than Bid A.

Suggested narrative shape (a plain text/markdown document per bid, not a
DB row):

```
Bid: {customer_name} ({customer_segment})
Date: {created_at}
Items requested: {list of raw_description + matched_sku pairs}
Suppliers contacted: {list of supplier names per item}
Outcome: {approved / quoted prices / any notes}
```

To check for a similar past bid (Stage 3), query Context Substrate with a
prompt describing the new bid's items/segment and let it return the
consolidated match — don't try to replicate vector similarity scoring
yourself; that's what Context Substrate handles internally per the
workshop.

**Open item:** confirm the exact ingestion mechanism (API call, upload
endpoint, required format) once Context Substrate sandbox access is live,
and update this section with the real integration details.

## Notes for whoever's coding this

- Use a consistent embedding model/dimension for `products` — this is now
  the *only* place we manage embeddings ourselves; Context Substrate
  handles its own internally for institutional memory.
- Seed scripts for synthetic data should be idempotent (safe to re-run) —
  you'll be resetting/reseeding often during development.
- Keep `raw_document` / `raw_description` fields even after matching —
  needed for the demo narrative ("here's the messy input, here's what we
  matched it to") and for debugging bad matches.
- Because institutional memory now lives outside Postgres, the Stage 3
  (Institutional Memory Check) code path involves an external API call to
  Context Substrate, not a local SQL query — budget for network latency
  and add error handling for that call specifically (e.g. what happens in
  the demo if Context Substrate is slow or unreachable — have a graceful
  fallback, don't let it hard-fail the whole pipeline).
