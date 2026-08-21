# Project: Sysco Intelligent Supplier Collaboration Portal

> **Read this file first, every session.** This is the entry point. It links out to
> deeper docs — read those too before touching code that relates to them. Do not
> assume prior session context carries over; this file plus `/docs` is the full
> source of truth.

## 1. What this project is

An AI-agent-based system that automates supplier outreach and item matching for
Sysco's bid management process, built as Team Mission Agents's entry for
**Prodapt IPL 2026** (Innovation Premier League — internal innovation contest).
Grand Finale: **September 23, 2026**.

This is not a toy hackathon idea — it's tied to a real, active business proposal
(an FDE / BidCoE engagement) already in front of Sysco leadership. The problem
statement, the pain points, and the impact numbers below all come from actual
customer conversations, not assumptions. Treat the business context as fact,
not flavor text.

## 2. The one-sentence pitch

> Sysco's suppliers are solicited by hand over Outlook — up to 1,000 manual
> emails per bid, with a 50%+ data entry error rate. We're building an AI
> pipeline that matches customer bid items to Sysco's catalog, drafts and
> tracks supplier outreach automatically, and remembers past bids so similar
> future bids resolve faster — with a human approval checkpoint before any
> outreach is actually sent.

Full business context, the bid lifecycle, and domain glossary: see
`docs/BUSINESS_CONTEXT.md`. Read that before writing anything that touches
domain logic (matching, outreach, pricing) — the vocabulary matters (RFQ, SKU,
AST, BEx, MCC, RevMan, OPCO all mean specific things here).

## 3. What we are building THIS cycle (scope discipline matters)

**Building now — Use Case 1 only:**
**Intelligent Supplier Collaboration Portal** — item matching + supplier
outreach + institutional memory, fully working, live-demoable end to end.

**NOT building this cycle (documented, not implemented):**
- Use Case 2 — Predictive Supplier Matching & Recommendation (Phase 2)
- Use Case 3 — Dynamic Pricing Intelligence Engine (Phase 2)

**If a session drifts toward building Use Case 2 or 3 logic, stop and flag it.**
Scope creep here is the single biggest risk to finishing by the finale. Every
line of code should trace back to one of the five pipeline stages in
`docs/ARCHITECTURE.md`.

## 4. Architecture at a glance

Six-stage pipeline. Full diagram, component reasoning, and the Agent Hub
scoping decision: see `docs/ARCHITECTURE.md`.

```
Bid document → Item Matching Service → Institutional Memory Check
  → Outreach Agent (Agent Hub-governed) → Human Approval Gate
  → Tracking Dashboard → (logged back into Institutional Memory)
```

**Key design decision, don't relitigate without reason:** only the Outreach
Agent is registered in Synapt Agent Hub. Item Matching and Institutional
Memory are backend services, not Agent Hub agents. Item Matching queries our
own Postgres + `pgvector` catalog; Institutional Memory queries Synapt Context
Substrate for past-bid narrative records. They don't take consequential
actions, so they don't need Agent Hub's governance/approval machinery. Full
rationale in `docs/ARCHITECTURE.md`.

## 5. Tech stack (do not introduce new tools without updating this file)

| Layer | Choice | Why |
|---|---|---|
| LLM | Claude (Anthropic API) | document parsing, drafting, reasoning |
| Backend | Python + FastAPI | fast to build, strong AI-tooling ecosystem |
| Database | PostgreSQL + `pgvector` | structured catalog/supplier data + product vector similarity search |
| Frontend | React | live dashboard: matching, outreach status, approval screen |
| Orchestration/Governance | Synapt Agent Hub (sandbox) | Outreach Agent only — see §4 |
| Knowledge/Memory | Synapt Context Substrate (sandbox) | bid-document ingestion + past-bid narrative memory |
| Fallback | If Synapt sandbox access is delayed | build standalone against the stack above, swap in Synapt components later without changing the data model |

Full schema: `docs/DATA_MODEL.md`. Agent manifest spec: `docs/AGENT_MANIFESTS.md`.

## 6. The demo (build with this in mind from day 1)

Two similar bids run back-to-back. Bid B resolves faster/with less new work
because the system reuses matches and supplier picks from Bid A —proving this
is a learning system, not just automation. Exact scripted items, suppliers,
and expected timings: `docs/DEMO_SCRIPT.md`. **Every feature should ask "does
this make the demo better or does it just add scope?"**

## 7. Current status / roadmap

Week-by-week plan, milestones, and what "done" looks like at each stage:
`docs/ROADMAP.md`. Update the status table in that file at the end of each
work session so the next session (yours or a teammate's) knows exactly where
things stand.

## 8. Working conventions

- Folder structure, naming, commit/PR conventions: `docs/CODING_CONVENTIONS.md`
- Team is new to agentic AI dev (associate-level engineers) — favor clear,
  well-commented code over clever abstractions. Optimize for "the next person
  reading this understands it fast," not for minimal line count.
- All synthetic data lives in `docs/DEMO_SCRIPT.md` and `/data` — never
  fabricate new sample data ad hoc mid-session; extend the documented set
  instead so the demo stays consistent.
- Data is synthetic (no real Sysco data access yet). Every place that touches
  "real data" assumptions should be clearly marked `# SYNTHETIC` in code
  comments so swapping to real data later is a find-and-replace, not an
  archaeology project.

## 9. Docs index

| File | Contents |
|---|---|
| `docs/BUSINESS_CONTEXT.md` | Sysco scale, bid lifecycle, pain points, glossary |
| `docs/ARCHITECTURE.md` | Full pipeline diagram, component reasoning, Agent Hub scoping |
| `docs/AGENT_MANIFESTS.md` | Outreach Agent manifest spec + governance rules |
| `docs/DATA_MODEL.md` | Postgres/pgvector schema |
| `docs/DEMO_SCRIPT.md` | Bid A / Bid B scripted scenario |
| `docs/ROADMAP.md` | Week-by-week plan + live status tracker |
| `docs/CODING_CONVENTIONS.md` | Folder structure, naming, workflow |

**When in doubt about scope, business logic, or a past decision — check these
docs before asking the user to re-explain. If the answer genuinely isn't
here, ask, then propose adding the answer to the relevant doc so it's not
lost again.**
