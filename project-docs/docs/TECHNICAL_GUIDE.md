# Technical Implementation Guide

> **For AI assistants working on this project.** This document captures the complete technical architecture, code organization, and implementation details so you can be productive immediately without re-reading all the design docs.

---

## 1. Project Overview

**Sysco Intelligent Supplier Collaboration Portal** — AI-agent system for Prodapt IPL 2026 (Grand Finale: Sep 23, 2026).

**What it does:** Automates Sysco's bid management pipeline:
1. **Bid intake** — Load synthetic bid documents (PDF/Excel simulated)
2. **Item matching** — Embed items → pgvector similarity search → Claude re-rank → best SKU
3. **Institutional memory** — Query Synapt Context Substrate for past bids → reuse matches
4. **Outreach Agent** — Draft RFQ emails to suppliers (Agent Hub-governed, low autonomy)
5. **Human approval** — Reviewer must approve before anything "sends"
6. **Tracking** — Dashboard shows Bid A vs Bid B comparison (learning proof)

**Key constraint:** Only the **Outreach Agent** is registered in Synapt Agent Hub. Item Matching & Memory are plain services (no consequential actions to govern).

---

## 2. Repository Structure

```
bid-management/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app + lifespan (DB init)
│   │   ├── db/
│   │   │   ├── session.py          # Async engine, session factory, Base
│   │   │   ├── models.py           # SQLAlchemy models (Product, Supplier, Bid, BidItem, Outreach)
│   │   │   ├── seed.py             # Idempotent CSV → DB loader
│   │   │   └── embedding_service.py # Embedding generation + pgvector search
│   │   ├── models/
│   │   │   └── pipeline.py         # Pydantic request/response contracts
│   │   ├── routes/
│   │   │   ├── pipeline.py         # V1 routes (in-memory demo, used by tests)
│   │   │   └── pipeline_v2.py      # V2 routes (async, DB-backed, real approval)
│   │   ├── services/
│   │   │   ├── synthetic_data.py   # CSV/JSON loaders (products, suppliers, bids)
│   │   │   ├── text.py             # Text normalization utilities
│   │   │   ├── matching.py         # V1 deterministic matcher (CSV, token overlap)
│   │   │   ├── matching_v2.py      # V2 pgvector + optional Claude re-rank
│   │   │   ├── memory.py           # V1 in-memory institutional memory
│   │   │   ├── memory_v2.py        # V2 Context Substrate-shaped service
│   │   │   ├── outreach.py         # V1 template-based outreach
│   │   │   ├── outreach_v2.py      # V2 Claude-drafted outreach + supplier reuse
│   │   │   ├── pipeline.py         # V1 orchestrator (sync, auto-approves)
│   │   │   └── pipeline_v2.py      # V2 orchestrator (async, stops at pending_approval)
│   │   ├── routes/
│   │   └── tests/
│   │       └── test_pipeline.py    # V1 pipeline tests (3 passing)
│   ├── requirements.txt
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── main.jsx                # React demo dashboard (V2 API)
│   │   └── styles.css
│   ├── package.json                # Vite + React 19 + lucide-react
│   └── index.html
├── data/
│   └── synthetic/
│       ├── products.csv            # ~600 SKUs, 5 categories
│       ├── suppliers.csv           # ~35 suppliers, reliability scores
│       ├── bid_a.json              # 18 items, hospital
│       └── bid_b.json              # 22 items (~82% overlap with A)
├── project-docs/
│   ├── CLAUDE.md                   # Master entry point (READ FIRST)
│   └── docs/
│       ├── BUSINESS_CONTEXT.md     # Sysco scale, bid lifecycle, glossary
│       ├── ARCHITECTURE.md         # Pipeline diagram, data-split rationale
│       ├── DATA_MODEL.md           # Postgres schema + Context Substrate notes
│       ├── DEMO_SCRIPT.md          # Bid A/B script, overlap targets
│       ├── ROADMAP.md              # 6-week plan + status tracker
│       ├── AGENT_MANIFESTS.md      # Outreach Agent manifest (YAML)
│       ├── CODING_CONVENTIONS.md   # Folder structure, naming, principles
│       └── TECHNICAL_GUIDE.md      # THIS FILE
└── .gitignore
```

---

## 3. Data Model (PostgreSQL + pgvector)

All tables in `backend/app/db/models.py`:

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `products` | Catalog (~600 SKUs) | `sku` PK, `name`, `category`, `spec`, `embedding vector(1536)` |
| `suppliers` | Supplier catalog (~35) | `id` UUID PK, `name`, `category`, `reliability_score`, `contact_email` |
| `bids` | Bid header | `id` UUID PK, `customer_name`, `customer_segment`, `raw_document`, `context_substrate_ref` |
| `bid_items` | Line items + matches | `id` UUID PK, `bid_id` FK, `raw_description`, `quantity`, `matched_sku`, `match_confidence`, `match_explanation` |
| `outreach` | Drafted RFQs | `id` UUID PK, `bid_item_id` FK, `supplier_id` FK, `drafted_message`, `status`, `quoted_price`, `approved_by`, `approved_at` |

**Indexes:**
- `products.embedding` → `ivfflat` with `vector_cosine_ops` (pgvector ANN)
- `products.category`, `suppliers.category`, `bids.customer_segment`, `bid_items.bid_id`, `outreach.status`

**No `past_bids` table** — institutional memory lives in Synapt Context Substrate as narrative documents (per `DATA_MODEL.md` §Institutional memory).

---

## 4. Synthetic Data

Located in `data/synthetic/`:

| File | Records | Notes |
|------|---------|-------|
| `products.csv` | 598 SKUs | Categories: paper-disposables, disposables-cutlery, disposables-cups, proteins, produce, dry-goods, kitchen-equipment, disposables-bowls, disposables-foil, disposables-wrap, cleaning, packaging, cups-lids, uniforms, safety-equipment, baking, beverages |
| `suppliers.csv` | 35 suppliers | `reliability_score` 0.83–0.98 (synthetic, for selection demo) |
| `bid_a.json` | 18 items | Customer: "Riverside Regional Hospital", segment: hospital |
| `bid_b.json` | 22 items | Customer: "Lakeside Medical Center", segment: hospital, **82% overlap** with A |

**Overlap items (14 of 18 from A):**
- 2-ply dinner napkins
- heavy duty plastic forks
- chicken breast 6oz
- ground beef 80/20
- atlantic salmon 6oz
- romaine lettuce hearts
- yellow onions
- russet potatoes
- long grain rice
- large eggs 15dz
- whole milk gallon
- unsalted butter 1lb
- #10 can diced tomatoes
- extra virgin olive oil
- stainless steel hotel pans
- full size sheet pans
- quaternary sanitizer
- nitrile gloves large

**New in B (4 items):**
- turkey breast boneless
- baby spinach triple washed
- shredded mozzarella
- instant read digital food thermometer

---

## 5. V1 vs V2 Pipeline

| Aspect | V1 (`pipeline.py`) | V2 (`pipeline_v2.py`) |
|--------|-------------------|----------------------|
| **Execution** | Sync, in-memory | Async, DB-backed where available |
| **Matching** | Token overlap on CSV catalog | pgvector similarity + optional Claude re-rank |
| **Memory** | In-memory dataclass | Context Substrate-shaped service (local fallback) |
| **Outreach** | Template only | Claude-drafted + supplier reuse param |
| **Approval** | Auto-approves for demo | Stops at `pending_approval`; explicit endpoint |
| **Fallback** | N/A | DB down → CSV matcher; Claude down → template |
| **Tests** | 3 passing in `test_pipeline.py` | Manual verification only |

**Run V1:** `POST /pipeline/run-demo/both`
**Run V2:** `POST /pipeline/v2/run-demo/both`

---

## 6. Service Details

### 6.1 MatchingServiceV2 (`matching_v2.py`)

```python
async def match_item(item: BidItemInput, session: AsyncSession) -> MatchedItem:
    # 1. Embed item description (deterministic hash fallback)
    query_embedding = await generate_embedding(item.raw_description)

    # 2. pgvector similarity search (top-5 by category)
    candidates = await search_similar_products(session, query_embedding, item.category_hint, 5)

    # 3. Claude re-rank (if ANTHROPIC_API_KEY set)
    if self.anthropic:
        best = await self._llm_rerank(item, candidates)
    else:
        best = candidates[0]  # deterministic fallback

    # 4. Return MatchedItem with confidence + explanation
```

**Key points:**
- Caches results in `self._cache` keyed by normalized description
- `generate_embedding()` = deterministic SHA256 expansion to 1536 dims (replace with real LLM when API key available)
- `_llm_rerank()` prompts Claude with candidate list → returns JSON `{matched_sku, confidence, explanation}`
- Falls back to top vector candidate on any error

### 6.2 InstitutionalMemoryServiceV2 (`memory_v2.py`)

```python
async def check(bid: BidDocument) -> (MemoryHit, dict[str, MatchedItem]):
    # Local simulation of Context Substrate behavior
    # Finds past bid in same segment with max item overlap
    # Returns reusable MatchedItems with source="memory_reuse"

async def remember(bid: BidDocument, matched_items: list[MatchedItem]):
    # Builds narrative per DATA_MODEL.md format
    # Stores in self._narratives (simulates Context Substrate ingestion)
```

**Narrative format (per DATA_MODEL.md):**
```
Bid: {customer_name} ({customer_segment})
Date: {iso_timestamp}
Items requested:
  - {raw_description} → {matched_sku} ({matched_name}) [fresh_match|memory_reuse]
Suppliers contacted:
  - {description} → {sku}
Outcome: approved, quoted prices received
```

### 6.3 OutreachServiceV2 (`outreach_v2.py`)

```python
def draft_for_items(bid_id, customer_name, items, reused_supplier_by_sku):
    for item in items:
        supplier = _select_supplier(item, reused_supplier_by_sku)  # memory reuse first
        draft = OutreachDraft(
            raw_description=item.raw_description,
            matched_sku=item.matched_sku,
            supplier_name=supplier.name,
            supplier_email=supplier.contact_email,
            drafted_message=_draft_message(...),  # Claude or template
            status="pending_approval",  # NEVER "sent" here
            approved_by=None,
        )
```

**Supplier selection:**
1. If `reused_supplier_by_sku[matched_sku]` exists → use that supplier (memory reuse)
2. Else → highest `reliability_score` in `matched_category`

**Claude drafting (`_claude_draft`):**
- Prompt: professional RFQ email, <120 words, no invented prices
- Returns None on failure → template fallback
- Template includes: bid_id, customer, item, matched SKU, spec, quantity

---

## 7. API Endpoints

### V1 (sync, for tests)
```
POST /pipeline/run-demo/{bid_id}     # bid_id: bid_a, bid_b, both
POST /pipeline/reset-memory
GET  /health
```

### V2 (async, demo-ready)
```
POST /pipeline/v2/run-demo/{bid_id}   # bid_id: bid_a, bid_b, both
POST /pipeline/v2/reset-memory
POST /pipeline/v2/approve/{bid_id}    # {reviewer: "Name"} — Stage 5 gate
GET  /health
GET  /health/db
```

---

## 8. Running the Demo

### Backend
```bash
cd backend
pip install -r requirements.txt
# Requires PostgreSQL running at DATABASE_URL (default: postgres:postgres@localhost:5432/sysco_bid_mgmt)
# Or it falls back to CSV catalog automatically
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev  # http://127.0.0.1:5173
```

### Demo Flow
1. Start backend + frontend
2. Click **"Run Bid A/B Demo"** → runs both bids through full pipeline
3. **Bid A** (Riverside Hospital): 18 fresh matches, 18 drafts pending approval
4. **Bid B** (Lakeside Medical): 14 memory-reused, 4 fresh, 4 drafts pending
5. Select a bid → enter **Reviewer name** → click **"Approve & Send"**
6. Dashboard shows: "Bid B memory reuse: 14/22", "Simulated steps saved: 42"

---

## 9. Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/sysco_bid_mgmt` | Postgres connection |
| `ANTHROPIC_API_KEY` | (unset) | Enables Claude re-ranking in matching + drafting |

**No required secrets for demo** — both services have deterministic fallbacks.

---

## 10. Key Implementation Decisions (Don't Relitigate)

| Decision | Rationale | Documented |
|----------|-----------|------------|
| Only Outreach Agent in Agent Hub | Governance belongs on consequential actions (sending email), not retrieval | `ARCHITECTURE.md` §Agent Hub scoping |
| Catalog in pgvector, not Context Substrate | Synapt team: Context Substrate not for row-per-record CRM/ERP data | `ARCHITECTURE.md` §Data source split |
| Institutional memory as narratives | Context Substrate excels at document ingestion, not row queries | `DATA_MODEL.md` §Institutional memory |
| V2 stops at `pending_approval` | "Low autonomy + clean approval record > fully autonomous nobody can audit" | `AGENT_MANIFESTS.md` Core principle |
| Graceful fallbacks everywhere | Demo must not hard-fail on sandbox latency | `DATA_MODEL.md` Notes |

---

## 11. Adding New Features

### New matching logic
1. Modify `matching_v2.py` → `_llm_rerank()` prompt or similarity search params
2. Keep cache keyed by `normalize_text(raw_description)`
3. Return `MatchedItem` with `source="fresh_match"`

### New memory behavior
1. Modify `memory_v2.py` → `_local_simulation_check()` or `_build_query_prompt()`
2. When Context Substrate sandbox ready: replace `_local_simulation_check()` with real client call
3. Narrative format must match `DATA_MODEL.md` for query compatibility

### New outreach action
1. Add to `allowed_actions` in `AGENT_MANIFESTS.md` manifest
2. Implement in `outreach_v2.py` (never auto-send)
3. Add approval UI if new action needs human gate

---

## 12. Common Tasks

### Reset institutional memory (cold start)
```bash
curl -X POST http://127.0.0.1:8000/pipeline/v2/reset-memory
```

### Run single bid
```bash
curl -X POST http://127.0.0.1:8000/pipeline/v2/run-demo/bid_a
```

### Approve outreach
```bash
curl -X POST http://127.0.0.1:8000/pipeline/v2/approve/BID-A-001 \
  -H "Content-Type: application/json" \
  -d '{"reviewer": "Jane Reviewer"}'
```

### Seed database (after Postgres is up)
```bash
cd backend
python -m app.db.seed
python -m app.db.embedding_service  # generates embeddings for all products
```

---

## 13. Testing

```bash
cd backend
python -m pytest tests/ -v
# 3 tests passing:
# - test_bid_b_reuses_memory_when_running_both
# - test_unknown_bid_raises_value_error
# - test_run_demo_endpoint_supports_both
```

**Note:** Tests use V1 pipeline (`pipeline.py`). V2 has no automated tests yet — manual verification via frontend.

---

## 14. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError: asyncpg` | Dependencies not installed | `pip install asyncpg pgvector` |
| `Connection refused` to DB | Postgres not running | Start Postgres, or let fallback to CSV (works automatically) |
| `ANTHROPIC_API_KEY` not set | Claude calls skip | Set env var to enable LLM re-rank/draft |
| Frontend shows "Could not reach backend" | Backend not on port 8000 | Check `uvicorn` running, CORS not configured (uses same origin) |
| Bid B shows 0 reused | Memory not persisted between runs | Memory is in-process; run `/pipeline/v2/run-demo/both` in one call |

---

## 15. File Ownership Map

| Area | Primary Files | Secondary |
|------|--------------|-----------|
| DB schema | `db/models.py` | `db/seed.py`, `db/embedding_service.py` |
| Matching logic | `services/matching_v2.py` | `services/matching.py` (fallback) |
| Memory logic | `services/memory_v2.py` | `services/memory.py` (fallback) |
| Outreach logic | `services/outreach_v2.py` | `services/outreach.py` (fallback) |
| Pipeline orchestration | `services/pipeline_v2.py` | `services/pipeline.py` (V1) |
| API routes | `routes/pipeline_v2.py` | `routes/pipeline.py` (V1) |
| Frontend | `frontend/src/main.jsx` | `frontend/src/styles.css` |
| Synthetic data | `data/synthetic/*.csv, *.json` | `services/synthetic_data.py` |

---

## 16. Next Steps (Roadmap Alignment)

Per `ROADMAP.md`, current status: **Week 1/2 complete**. Next priorities:

| Week | Task | Files to Touch |
|------|------|----------------|
| 2 | Real embedding generation (replace hash fallback) | `db/embedding_service.py` |
| 3 | Context Substrate integration (replace local sim) | `services/memory_v2.py` |
| 3 | Agent Hub manifest finalization + registration | `docs/AGENT_MANIFESTS.md` |
| 4 | Full approval UI polish + mock inbox | `frontend/src/main.jsx` |
| 5 | Dashboard metrics + internal review | `frontend/src/main.jsx`, `services/tracking.py` |

---

## 17. Glossary (from BUSINESS_CONTEXT.md)

| Term | Meaning |
|------|---------|
| **RFQ** | Request for Quote — asking a supplier for pricing |
| **SKU** | Stock Keeping Unit — a specific product in Sysco's catalog |
| **Bix** | Internal system that vets incoming bid documents |
| **AST** | Team/tool that manually matches items to Sysco SKUs |
| **BEx** | Tool that extracts items from bid documents |
| **MCC** | Merchandise Customer Contract — working file before pricing |
| **RevMan** | Revenue Management — finalizes pricing/margin |
| **OPCO** | Operating Company / warehouse — fulfills after bid won |
| **FDE** | Forward Deployed Engineer — build agents that build platform |
| **BidCoE** | Bid Center of Excellence — larger proposal this feeds into |
| **SF360** | Salesforce CRM |

---

*Last updated: 2026-08-24. Update this file when architecture or key implementation details change.*