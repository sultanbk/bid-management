# Quick Start Guide

> Get the Sysco Intelligent Supplier Collaboration Portal running locally in 5 minutes.

---

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** (for frontend)
- **PostgreSQL 15+** with **pgvector** extension (optional — app falls back to CSV catalog)

---

## 1. Backend Setup

```bash
cd backend

# Create virtual environment (recommended)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Optional: PostgreSQL + pgvector

If you have Postgres running locally:

```bash
# Create database
createdb sysco_bid_mgmt

# Enable pgvector (run once)
psql -d sysco_bid_mgmt -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Set DATABASE_URL (optional — defaults to localhost:5432)
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/sysco_bid_mgmt"
```

**If Postgres is not available:** The app automatically falls back to the CSV catalog. No setup required.

### Seed the database (if using Postgres)

```bash
# Load products & suppliers from CSV
python -m app.db.seed

# Generate embeddings for all products (uses deterministic fallback)
python -m app.db.embedding_service
```

### Run the backend

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Verify:**
- `http://127.0.0.1:8000/health` → `{"status": "ok"}`
- `http://127.0.0.1:8000/health/db` → `{"status": "ok", "database": "connected"}` (or `"error"` if fallback)
- `http://127.0.0.1:8000/docs` → FastAPI Swagger UI

---

## 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

**Opens:** `http://127.0.0.1:5173`

---

## 3. Run the Demo

1. Open `http://127.0.0.1:5173`
2. Click **"Run Bid A/B Demo"**
3. Wait ~2 seconds — both bids process through the full pipeline
4. Click on **BID-A-001** (Riverside Regional Hospital) → 18 items, all fresh matches
5. Click on **BID-B-002** (Lakeside Medical Center) → 14 reused from memory, 4 fresh
6. **Key metric:** "Simulated steps saved" = 42 (proves learning loop)
7. Enter a **Reviewer name** (e.g., "Jane Reviewer")
8. Click **"Approve & Send"** — drafts move to approved, mock send queued

---

## 4. API Quick Reference

```bash
# Run both bids (V2 async pipeline)
curl -X POST http://127.0.0.1:8000/pipeline/v2/run-demo/both

# Run single bid
curl -X POST http://127.0.0.1:8000/pipeline/v2/run-demo/bid_a

# Reset institutional memory (cold start)
curl -X POST http://127.0.0.1:8000/pipeline/v2/reset-memory

# Approve outreach for a bid
curl -X POST http://127.0.0.1:8000/pipeline/v2/approve/BID-A-001 \
  -H "Content-Type: application/json" \
  -d '{"reviewer": "Jane Reviewer"}'

# Health checks
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/health/db
```

---

## 5. Running Tests

```bash
cd backend
python -m pytest tests/ -v

# Expected: 3 passed
# test_bid_b_reuses_memory_when_running_both
# test_unknown_bid_raises_value_error
# test_run_demo_endpoint_supports_both
```

---

## 6. Enabling Real LLM Features (Optional)

Set `ANTHROPIC_API_KEY` to enable:
- **Claude re-ranking** in Item Matching (picks best of top-5 candidates with explanation)
- **Claude-drafted RFQ emails** in Outreach (professional, context-aware)

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# Restart uvicorn
```

**Without the key:** Deterministic fallbacks keep the demo fully functional.

---

## 7. Project Structure Cheat Sheet

```
bid-management/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry
│   │   ├── db/                  # DB models, seed, embeddings
│   │   ├── routes/
│   │   │   ├── pipeline.py      # V1 (sync, tests use this)
│   │   │   └── pipeline_v2.py   # V2 (async, demo uses this)
│   │   ├── services/
│   │   │   ├── matching_v2.py   # pgvector + optional Claude
│   │   │   ├── memory_v2.py     # Context Substrate simulation
│   │   │   ├── outreach_v2.py   # Claude drafting + approval
│   │   │   └── pipeline_v2.py   # Orchestrator
│   │   └── tests/test_pipeline.py
│   └── requirements.txt
├── frontend/
│   ├── src/main.jsx             # React dashboard
│   └── package.json
├── data/synthetic/              # CSV + JSON demo data
└── project-docs/docs/           # All design docs
```

---

## 8. Common Issues

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: asyncpg` | `pip install asyncpg pgvector` |
| Backend: `Connection refused` (DB) | Start Postgres, or let CSV fallback work (it does automatically) |
| Frontend: "Could not reach backend" | Ensure backend on `127.0.0.1:8000`; check no firewall |
| Bid B shows 0 reused | Memory is in-process — run both bids in ONE call (`/run-demo/both`) |
| Tests fail with `ModuleNotFoundError: app` | Run from `backend/` directory: `python -m pytest tests/` |

---

## 9. Next Steps

- **Week 2:** Replace hash embedding with real `text-embedding-3-small` in `db/embedding_service.py`
- **Week 3:** Swap `memory_v2.py` local simulation for real Context Substrate client
- **Week 4:** Polish approval UI + mock inbox in `frontend/src/main.jsx`
- **Week 5:** Internal review, metrics dashboard, rehearsal

---

*Built for Prodapt IPL 2026 — Grand Finale: September 23, 2026*