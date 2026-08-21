# Coding Conventions

## Folder structure (proposed — adjust once repo exists, then keep this in sync)

```
/backend
  /app
    /routes          # FastAPI route definitions, one file per pipeline stage
    /services         # matching.py, memory.py, outreach.py — core logic
    /models           # Pydantic request/response models
    /db                # connection, migrations, seed scripts once Postgres lands
  /tests
/frontend
  /src
    /components
    /pages
/data
  /synthetic          # generated catalog, suppliers, sample bid documents
/docs                 # this folder — keep updated, it's the project's memory
CLAUDE.md
```

Current backend implementation notes:
- `/backend/app/main.py` owns the FastAPI app and router registration.
- `/backend/app/models/pipeline.py` owns the shared Pydantic contracts for
  the local demo pipeline.
- `/backend/app/routes/pipeline.py` exposes `POST /pipeline/run-demo/{bid_id}`
  and `POST /pipeline/reset-memory`.
- `/backend/app/services/pipeline.py` orchestrates the six stages.
- `/backend/app/services/synthetic_data.py` is the only service that should
  directly read `/data/synthetic` files.
- `/backend/tests/test_pipeline.py` verifies the Bid A cold / Bid B warm demo
  behavior.

## General principles

- **Clarity over cleverness.** Team is new to agentic AI development
  (associate-level engineers). Write code the way you'd explain it out loud
  — favor readable, well-commented functions over dense one-liners or deep
  abstraction layers.
- **One pipeline stage = one service file.** Don't let matching logic leak
  into the outreach service or vice versa — keep the boundaries from
  `ARCHITECTURE.md` intact in the code structure too.
- **Mark synthetic-data assumptions.** Any code that assumes something about
  the synthetic dataset (e.g. "categories are always one of these 5") gets a
  `# SYNTHETIC` comment so it's easy to find when real data access happens.
- **Output contracts are explicit.** Each stage's input/output shape is
  defined in `ARCHITECTURE.md` — use Pydantic models that match those
  contracts exactly, so stages can be tested independently.

## Git workflow

- `[fill in once decided with the team — branch naming, PR review
  requirement, who merges to main]`

## When starting a new session with an AI coding assistant

1. Read `CLAUDE.md` first.
2. Read the specific `docs/*.md` file relevant to what you're about to work
   on (don't read all of them every time if only touching one stage).
3. Check `ROADMAP.md`'s Status Tracker for current state and blockers before
   assuming what's already built.
4. If you make an architecture or scope decision mid-session, **update the
   relevant doc before ending the session** — undocumented decisions are
   lost decisions once the session ends.
