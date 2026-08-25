# AI Assistant Quick Reference

> **Read this first when joining the project.** One-page cheat sheet for any AI assistant working on this codebase.

---

## What This Project Is

**Sysco Intelligent Supplier Collaboration Portal** — AI agent system for **Prodapt IPL 2026** (Finale: Sep 23, 2026).

Automates Sysco's bid management: item matching → institutional memory → supplier outreach → human approval → tracking. **Core demo:** Bid B resolves faster than Bid A because it reuses memory from Bid A.

---

## The 6-Stage Pipeline

```
1. Bid intake          → Load synthetic JSON (no real parsing yet)
2. Item Matching       → pgvector similarity + optional Claude re-rank
3. Institutional Memory→ Context Substrate narrative query (local sim now)
4. Outreach Agent      → Drafts RFQs (Agent Hub-governed, LOW autonomy)
5. Human Approval      → Reviewer MUST approve before "send"
6. Tracking Dashboard  → Bid A vs Bid B comparison + memory write-back
```

**Only Stage 4 (Outreach Agent) is in Agent Hub.** Stages 2 & 3 are plain services — no consequential actions to govern.

---

## Key Files You'll Touch

| Task | File |
|------|------|
| Matching logic | `backend/app/services/matching_v2.py` |
| Memory logic | `backend/app/services/memory_v2.py` |
| Outreach logic | `backend/app/services/outreach_v2.py` |
| Pipeline orchestration | `backend/app/services/pipeline_v2.py` |
| API routes | `backend/app/routes/pipeline_v2.py` |
| Frontend dashboard | `frontend/src/main.jsx` |
| DB models | `backend/app/db/models.py` |
| Synthetic data | `data/synthetic/*.csv, *.json` |

---

## Critical Design Decisions (Don't Change Without Discussion)

1. **Catalog in pgvector, not Context Substrate** — Synapt team said Context Substrate isn't for row-per-record CRM data
2. **Memory as narratives** — Context Substrate ingests documents, not rows
3. **Agent autonomy = LOW** — Outreach Agent drafts, NEVER sends without Stage 5 approval
4. **Separate author/approver** — `approved_by` on outreach must be a human, not the agent
5. **Graceful fallbacks everywhere** — DB down → CSV; Claude down → template; demo never hard-fails

---

## Synthetic Data (Don't Invent — Extend These)

| File | Records | Key Fields |
|------|---------|------------|
| `products.csv` | 598 SKUs | sku, name, category, spec |
| `suppliers.csv` | 35 | name, category, reliability_score, contact_email |
| `bid_a.json` | 18 items | hospital, items with category_hint |
| `bid_b.json` | 22 items | hospital, **82% overlap** with A + 4 new |

**Overlap drives the demo.** If you change items, update both bids to maintain overlap.

---

## Running the Demo

```bash
# Terminal 1: Backend
cd backend && uvicorn app.main:app --port 8000 --reload

# Terminal 2: Frontend
cd frontend && npm run dev

# Open http://127.0.0.1:5173 → "Run Bid A/B Demo"
```

---

## API Endpoints (V2 = Demo Ready)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/pipeline/v2/run-demo/both` | Run Bid A + B |
| POST | `/pipeline/v2/run-demo/bid_a` | Single bid |
| POST | `/pipeline/v2/reset-memory` | Clear memory (cold start) |
| POST | `/pipeline/v2/approve/{bid_id}` | Stage 5: `{reviewer: "Name"}` |

---

## Environment Variables

| Var | Required? | Purpose |
|-----|-----------|---------|
| `DATABASE_URL` | No (falls back to CSV) | Postgres + pgvector |
| `ANTHROPIC_API_KEY` | No (falls back to deterministic) | Enables Claude re-rank + drafting |

---

## Testing

```bash
cd backend && python -m pytest tests/ -v
# 3 tests pass (V1 pipeline)
```

---

## Next Work Items (Priority Order)

1. **Real embeddings** — Replace hash fallback in `embedding_service.py` with OpenAI/Anthropic
2. **Context Substrate integration** — Swap `memory_v2.py` local sim for real client
3. **Agent Hub manifest** — Finalize `AGENT_MANIFESTS.md` + register in sandbox
4. **Approval UI polish** — Mock inbox, better status tracking in `main.jsx`
5. **Metrics dashboard** — Real-time stage timing, cost tracking

---

## Glossary (Use These Terms)

| Term | Meaning |
|------|---------|
| RFQ | Request for Quote |
| SKU | Stock Keeping Unit |
| AST | Assortment Selection Team (matches items to SKUs) |
| BEx | Bid Extraction tool |
| MCC | Merchandise Customer Contract |
| RevMan | Revenue Management |
| OPCO | Operating Company (fulfillment) |
| BidCoE | Bid Center of Excellence |

---

## When Stuck

1. Check `project-docs/docs/TECHNICAL_GUIDE.md` — full implementation details
2. Check `project-docs/docs/ARCHITECTURE.md` — pipeline diagram + rationale
3. Check `project-docs/docs/DEMO_SCRIPT.md` — exact demo scenario
4. Don't guess — ask the human if a decision isn't documented