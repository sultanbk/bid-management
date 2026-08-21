# Roadmap

6 weeks, ending at the Grand Finale (Sep 23, 2026). Update the **Status
Tracker** at the bottom after every work session — this is what lets a new
session (or a teammate) know exactly where things stand without re-reading
every past conversation.

## Day 0 — Prerequisites (before Week 1 code starts)

- [ ] Sandbox access confirmed for Agent Hub (and Context Substrate /
      Data Transformation once relevant)
- [ ] Agent Hub catalog searched for any existing agent close to document
      extraction, communication drafting, or matching — clone-and-adapt
      beats building blank
- [ ] Open question answered: how much manual glue code is needed to
      connect multiple services into one workflow (Agent Hub Build/Deploy
      phases are partial) — update `ARCHITECTURE.md` once known
- [ ] Shared repo set up — branching, PR review process, folder ownership
- [ ] Demo scenario locked in `DEMO_SCRIPT.md`

## Week 1 — Design & Foundation

- Architecture diagram finalized (`ARCHITECTURE.md`)
- Outreach Agent manifest drafted (`AGENT_MANIFESTS.md`)
- Dev environment working for every team member (Python/FastAPI skeleton,
  Postgres + pgvector running, basic Claude API call succeeding)
- Synthetic data generated: catalog, suppliers, Bid A + Bid B documents
- **Milestone:** architecture exists, environment works, synthetic data
  exists, demo script is written down.

## Week 2 — Item Matching Service

- Catalog loaded into Postgres with embeddings
- Matching function: embed input → vector search → top-5 candidates →
  Claude re-ranks + explains best match
- Tested against Bid A's document
- **Milestone:** feed in a messy document, get back a clean matched +
  explained SKU list.

## Week 3 — Outreach Agent (start) + Agent Hub registration

- Manifest finalized against real sandbox schema
- Email drafting logic built (Claude drafts, doesn't send)
- Tracking table + status states implemented
- Agent registered in Agent Hub if sandbox supports it
- **Milestone:** given matched items, system drafts outreach and queues it
  for approval.

## Week 3–4 (overlap) — Institutional Memory

- Past-bid storage + retrieval implemented
- Bid A run cold and stored; Bid B run and shown resolving faster via
  memory reuse
- **Milestone:** the core demo moment works end to end, even roughly.

## Week 4 — Human Approval + full pipeline connection

- Approval UI: approve/reject before anything "sends" (simulated sending)
- All 6 stages wired together, no manual intervention except the approval
  click
- **Milestone:** full pipeline runs end-to-end for Bid A and Bid B.

## Week 5 — Dashboard, polish, internal review

- React dashboard: upload → matching → outreach status → approval → time
  saved stat
- Internal review with Ela/Shree — treat as a dry run, act on feedback
- Bug-fixing, demo timing tightened
- **Milestone:** stable, rehearsed, end-to-end live demo.

## Week 6 — Final rehearsal + Finale

- Full team dry-run, multiple times, out loud
- Backup demo video recorded
- Pitch deck finalized with real measured numbers (swap projected % for
  actual measured results wherever possible)
- **Grand Finale — Sep 23**

---

## Status Tracker

> Update this section at the end of every session. Keep it short — status
> and blockers only, not a full log. Older entries can move to a
> `CHANGELOG` section below if this gets long.

**Last updated:** `2026-08-12` by `Codex session`

**Current week:** `Week 1 / foundation`

**Status:**
- [ ] Day 0 prerequisites complete
- [ ] Week 1 complete - local FastAPI demo backend exists; Postgres,
      frontend, and real Claude/Synapt calls are not complete yet
- [ ] Week 2 complete
- [ ] Week 3 complete
- [ ] Week 4 complete
- [ ] Week 5 complete
- [ ] Week 6 complete

**Active blockers:**
- Synapt Agent Hub / Context Substrate sandbox access is not recorded as confirmed.
- Agent Hub catalog search and exact manifest schema are not recorded as complete.
- `D:\bid-management` is inside a parent Git repository but is not its own repo; repo-wide `git status` is noisy and slow.
- Frontend, database migrations, pgvector embeddings, and real LLM/Synapt integrations are not built yet.

**Next session should start with:**
- Add the React dashboard shell that calls `POST /pipeline/run-demo/both` and visualizes stages, matched items, outreach drafts, and the Bid A vs Bid B memory savings.

### Change Log

- `2026-08-12` - Added local FastAPI backend scaffold with Pydantic contracts,
  synthetic CSV/JSON data loading, deterministic item matching, in-memory
  institutional memory, local outreach drafting, simulated approval, tracking
  metrics, and tests. Main endpoint: `POST /pipeline/run-demo/{bid_id}`.
