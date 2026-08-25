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

**Last updated:** `2026-08-24` by `Claude Code session`

**Current week:** `Week 2-3 complete` (Item Matching + Outreach Agent + Institutional Memory + Approval Gate + Dashboard all working)

**Status:**
- [x] Day 0 prerequisites complete (architecture, manifest, synthetic data)
- [x] Week 1 complete — architecture finalized, FastAPI skeleton, synthetic data generated, demo script locked
- [x] Week 2 complete — Item Matching Service with pgvector + optional Claude re-rank (matching_v2.py), embeddings service, CSV fallback
- [x] Week 3 complete — Outreach Agent (outreach_v2.py) with Claude drafting, supplier selection, Agent Hub governance rules (drafts only, never sends)
- [x] Week 3-4 overlap complete — Institutional Memory (memory_v2.py) with Context Substrate-shaped service, narrative storage, Bid A→B reuse working
- [x] Week 4 complete — Human Approval Gate UI in frontend (reviewer name required, explicit approve endpoint), full pipeline wired end-to-end
- [x] Dashboard complete — React dashboard shows stages, matched items, outreach drafts, Bid A vs Bid B comparison, approval UI
- [ ] Week 5 — Internal review, polish, rehearsal
- [ ] Week 6 — Final rehearsal + Finale (Sep 23)

**Active blockers:**
- Synapt Agent Hub / Context Substrate sandbox access not confirmed (using local simulations)
- Agent Hub catalog search and exact manifest schema pending sandbox access
- Real LLM embeddings not yet integrated (deterministic hash fallback in use)
- `D:\bid-management` is inside a parent Git repository but is not its own repo; repo-wide `git status` is noisy and slow.

**Next session should start with:**
- Replace deterministic hash embeddings with real `text-embedding-3-small` or Anthropic embeddings in `embedding_service.py`
- When Context Substrate sandbox available: swap `memory_v2.py` local simulation for real client integration
- Polish approval UI: add mock inbox view, rejection flow, audit trail display
- Add internal review prep: demo timing script, backup video recording plan

### Change Log

- `2026-08-12` - Added local FastAPI backend scaffold with Pydantic contracts,
  synthetic CSV/JSON data loading, deterministic item matching, in-memory
  institutional memory, local outreach drafting, simulated approval, tracking
  metrics, and tests. Main endpoint: `POST /pipeline/run-demo/{bid_id}`.
