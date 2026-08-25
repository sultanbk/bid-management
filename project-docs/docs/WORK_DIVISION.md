# Work Division — Sysco Intelligent Supplier Collaboration Portal

> **Team:** 2 engineers | **Finale:** Sep 23, 2026 | **Current:** Week 4 complete (Week 5-6 remaining)
> **Single source of truth:** Update this file at end of every session. Read `ROADMAP.md` for week-by-week status.
> **Chosen Model:** Option A — By Pipeline Stage (Vertical Slices)

---

## 1. Ownership Model: By Pipeline Stage

Each person owns **full vertical slices** — backend service + API + frontend touchpoints for their stages.

| Person | Pipeline Stages Owned | Core Responsibility |
|--------|----------------------|---------------------|
| **Person A** | Stages 1-3: **Bid Intake → Item Matching → Institutional Memory** | "The Brain" — extraction, matching, learning |
| **Person B** | Stages 4-6: **Outreach Agent → Human Approval → Tracking Dashboard** | "The Face" — drafting, governance, visibility |

**Why this split:** Clean separation of concerns. Person A owns "does it match correctly?" Person B owns "does the human trust and approve it?" Minimal overlap = fewer merge conflicts.

---

## 2. Detailed Task Breakdown by Person

### Person A: Stages 1-3 (The Brain)

| ID | Stage | Task | File(s) | Acceptance Criteria | Status |
|----|-------|------|---------|---------------------|--------|
| **A1** | 1: Bid Intake | Verify/document extraction works for Bid A/B JSON (already synthetic) | `backend/app/services/synthetic_data.py`, `backend/app/services/text.py` | Bid A (18 items) + Bid B (22 items) load correctly; quantities parsed | ☐ |
| **A2** | 2: Item Matching | **Replace hash embeddings → real `text-embedding-3-small`** | `backend/app/db/embedding_service.py` | Real embeddings generated; pgvector search returns better matches than hash; latency < 500ms/item | ☐ |
| **A3** | 2: Item Matching | Tune pgvector index (HNSW params) + add embedding cache | `backend/app/db/embedding_service.py`, `backend/app/db/seed.py` | Matching quality ↑; index rebuild documented; cache hits > 80% on re-runs | ☐ |
| **A4** | 2: Item Matching | Optional: Enable Claude re-rank for top-5 candidates | `backend/app/services/matching_v2.py` | Re-rank improves match confidence on ambiguous items; toggleable via env var | ☐ |
| **A5** | 3: Institutional Memory | **Swap local sim → real Context Substrate client** | `backend/app/services/memory_v2.py` | Bid A narrative ingested; Bid B query returns 14/22 overlap; fallback to local if sandbox down | ☐ |
| **A6** | 3: Institutional Memory | Define narrative schema for bid ingestion (what gets stored) | `backend/app/services/memory_v2.py`, `project-docs/docs/DATA_MODEL.md` | Schema captures: items matched, suppliers picked, resolution outcome, customer segment | ☐ |
| **A7** | 1-3 Integration | End-to-end tests: cold run (Bid A) + warm run (Bid B) | `backend/tests/test_pipeline_v2.py` | 3 tests: cold run completes, warm run reuses 14 items, memory hit logged | ☐ |
| **A8** | 1-3 Reliability | Error handling, retries, timeouts for LLM/DB calls | `backend/app/services/matching_v2.py`, `backend/app/services/memory_v2.py` | No unhandled exceptions; structured logging; graceful degradation | ☐ |

---

### Person B: Stages 4-6 (The Face)

| ID | Stage | Task | File(s) | Acceptance Criteria | Status |
|----|-------|------|---------|---------------------|--------|
| **B1** | 4: Outreach Agent | **Agent Hub manifest finalization + registration** | `project-docs/docs/AGENT_MANIFESTS.md` | Manifest validates; agent registers; governance: draft-only, never auto-send | ☐ |
| **B2** | 4: Outreach Agent | Verify supplier selection logic + Claude drafting quality | `backend/app/services/outreach_v2.py` | Drafts reference correct matched SKU + supplier; tone professional; no hallucinations | ☐ |
| **B3** | 5: Human Approval | **Approval UI polish: mock inbox, rejection flow, audit trail** | `frontend/src/main.jsx` | Reviewer sees "inbox" of drafts; can approve/reject individually; `approved_by` recorded; rejection reason captured | ☐ |
| **B4** | 5: Human Approval | Enforce "reviewer ≠ agent author" governance rule in UI | `frontend/src/main.jsx`, `backend/app/routes/pipeline_v2.py` | UI warns if reviewer name matches agent; backend rejects same-name approval | ☐ |
| **B5** | 6: Tracking Dashboard | **"Time saved" stat with measured numbers** | `frontend/src/main.jsx`, `backend/app/services/tracking.py` | Dashboard: "Bid B saved 42 simulated steps (64% faster) — measured from actual run" | ☐ |
| **B6** | 6: Tracking Dashboard | **Bid A vs Bid B side-by-side comparison view** | `frontend/src/main.jsx` | Toggle shows both bids' matched items, outreach drafts, memory reuse % simultaneously | ☐ |
| **B7** | 6: Tracking Dashboard | Dashboard polish: loading states, error toasts, empty states | `frontend/src/main.jsx`, `frontend/src/styles.css` | No layout shift; clear feedback during pipeline run; accessible (keyboard, contrast) | ☐ |
| **B8** | 4-6 Integration | Record **backup demo video** (clean run, < 3 min) | — | Video committed/shared; plays without backend (static demo mode in frontend) | ☐ |
| **B9** | 4-6 Demo Prep | **Demo rehearsal script + dry-run timing** | `project-docs/docs/DEMO_REHEARSAL.md` | Script with exact speaking lines, click sequence, expected timings; 2+ full dry-runs | ☐ |
| **B10** | 4-6 Demo Prep | Internal review prep (Ela/Shree) + bug-fix sprint | — | Feedback documented; critical bugs fixed; demo stable for finale | ☐ |

---

## 3. Week-by-Week Allocation (Weeks 5-6)

| Week | Person A (Stages 1-3) | Person B (Stages 4-6) | Shared Milestone |
|------|----------------------|----------------------|------------------|
| **Week 5** (Aug 25-31) | A2, A3, A5, A7 | B3, B4, B5, B6 | **Internal review ready** — full demo runs end-to-end with real embeddings + polished approval UI |
| **Week 6** (Sep 1-23) | A4, A6, A8 | B1, B2, B7, B8, B9, B10 | **Finale ready** — Agent Hub registered, backup video recorded, rehearsal script locked, pitch deck with real numbers |

---

## 4. Communication Protocol

| Ritual | Frequency | Duration | Format |
|--------|-----------|----------|--------|
| **Standup** | Daily (Mon-Fri) | 10 min | Async in Slack: "Done / Doing / Blocked" |
| **Sync & Demo** | 2×/week (Tue + Fri) | 30 min | Screen share: run current demo, compare metrics |
| **Planning** | Monday | 15 min | Update this doc; pick top 3 tasks each |
| **Retro** | Friday | 15 min | What worked? What to change? Update ROADMAP.md |

**Blocking rule:** If blocked > 2 hours → post in Slack immediately. Don't spin.

---

## 5. Branch & PR Conventions

| Pattern | Example |
|---------|---------|
| Branch | `personA/a2-real-embeddings`, `personB/b3-approval-ui` |
| PR Title | `[Person A] Real embeddings: text-embedding-3-small integration` |
| PR Description | Links to task ID, includes demo GIF/screenshot, lists test commands |
| Review | Cross-review required (Person A reviews Person B, vice versa) |
| Merge | Squash + delete branch; update `ROADMAP.md` Status Tracker |

---

## 6. Shared State — Update Every Session

| Artifact | Location | Updated By |
|----------|----------|------------|
| **Roadmap Status Tracker** | `project-docs/docs/ROADMAP.md` (lines 81-113) | Both — end of session |
| **Work Division Status** | This file (Section 2 tables) | Both — when task status changes |
| **Demo Metrics Log** | `project-docs/docs/DEMO_METRICS.md` | Person B — after each demo run |
| **Blockers Log** | `project-docs/docs/BLOCKERS.md` | Both — immediately when blocked |

---

## 7. Demo Script Reference (from `DEMO_SCRIPT.md`)

**The only thing that matters for the finale:**

1. **Bid A (Riverside Regional Hospital)** — Cold run: 18 items, all fresh matches, 18 drafts pending
2. **Bid B (Lakeside Medical Center)** — Warm run: 22 items, 14 reused from Bid A (82% overlap), 4 fresh, 4 drafts pending
3. **Visible proof:** Dashboard shows "Bid B memory reuse: 14/22" + "Simulated steps saved: 42"
4. **Human approval:** Reviewer name entered → "Approve & Send" → audit trail visible
5. **Narrative:** "Bid B resolved in 40% of the steps because the system learned from Bid A"

---

## 8. Risk Register & Mitigations

| Risk | Likelihood | Impact | Mitigation | Owner |
|------|------------|--------|------------|-------|
| Synapt sandbox not granted | High | Medium | Local sims are demo-ready; document as "simulated" in pitch | Person A |
| Real embeddings break matching quality | Low | High | Keep hash fallback behind flag; A/B test before merge | Person A |
| Demo UI flaky during live judging | Medium | Critical | Record backup video (B8); static demo mode in frontend | Person B |
| Scope creep (Use Case 2/3) | Medium | High | **Hard rule:** No code outside 6-stage pipeline without PM approval | Both |
| One person overwhelmed | Medium | High | Weekly capacity check in retro; rebalance tasks if needed | Both |

---

## 9. Quick Reference — Key Files by Owner

| Area | Person A Files | Person B Files |
|------|----------------|----------------|
| **Embeddings** | `backend/app/db/embedding_service.py` | — |
| **Memory** | `backend/app/services/memory_v2.py` | — |
| **Matching** | `backend/app/services/matching_v2.py` | — |
| **Outreach** | — | `backend/app/services/outreach_v2.py` |
| **Pipeline Orchestration** | `backend/app/services/pipeline_v2.py` (stages 1-3) | `backend/app/services/pipeline_v2.py` (stages 4-6) |
| **API Routes** | — | `backend/app/routes/pipeline_v2.py` (approval endpoint) |
| **Dashboard UI** | — | `frontend/src/main.jsx` |
| **Styles** | — | `frontend/src/styles.css` |
| **Agent Hub** | — | `project-docs/docs/AGENT_MANIFESTS.md` |
| **Demo Docs** | — | `DEMO_REHEARSAL.md`, `DEMO_METRICS.md` |
| **Tests** | `backend/tests/test_pipeline_v2.py` | — |

---

## 10. Handoff Points (Where You Must Sync)

| Handoff | From | To | Artifact |
|---------|------|-----|----------|
| Matched items → Outreach | Person A (matching_v2.py) | Person B (outreach_v2.py) | `matched_items: List[MatchedItem]` — SKU, confidence, explanation |
| Memory hits → Pipeline | Person A (memory_v2.py) | Person B (pipeline_v2.py) | `memory_hit: MemoryHit` — overlap_count, source_bid_id, reused_items |
| Approval status → Dashboard | Person B (approval endpoint) | Person B (frontend) | `approved_by`, `approved_at`, `status` per draft |
| Demo metrics → Pitch deck | Person B (tracking.py) | Both | Measured: steps saved, time saved, reuse % |

---

## 11. Sign-Off

| Role | Name | Date |
|------|------|------|
| Person A (Stages 1-3) | | |
| Person B (Stages 4-6) | | |

> **Update this file at the end of every session.** Change ☐ → ✅ when done. Add notes in Status column.