# Architecture

## Pipeline overview

```
Bid document received
        |
        v
Item Matching Service        (queries Postgres + pgvector — product catalog)
        |
        v
Institutional Memory Check   (queries Synapt Context Substrate — past bid records)
        |
        v
Outreach Agent                (Agent Hub-governed, low autonomy)
        |
        v
Human Approval Gate           (reviewer approves before anything sends)
        |
        v
Tracking Dashboard            (status view)
        |
        `--> logged back into Institutional Memory as a new record
```

Each stage below: what it does, what it depends on, what "done" looks like.

## Data source split: Context Substrate vs. our own Postgres/pgvector

**Decided after the Context Substrate workshop (Sivaraman K Lakshmanan,
Synapt team) — do not relitigate without a reason documented here.**

Context Substrate auto-ingests documents (any format — PDF, Excel, JSON,
unstructured text) into a combined graph + vector store and returns one
consolidated answer per query. It's genuinely a good fit for a lot of what
we need — but the Synapt team explicitly flagged a limitation: it is **not**
intended for data shaped like a CRM/ERP/order-management system, i.e. **a
large number of rows where each row is its own individual entity**. Small
structured data (their example: ~1,000 lines of policy rules) is fine;
large row-per-record catalogs are the pattern they said to avoid.

Our 600-SKU product catalog is exactly that shape — one row per SKU. So we
split by data type instead of routing everything through one system:

| Data | System | Why |
|---|---|---|
| **Product catalog** (600 SKUs, row-per-record) | Our own **Postgres + pgvector** | Matches the Synapt team's stated caution against row-heavy structured/CRM-like data |
| **Incoming bid documents** (messy PDF/Excel/email) | **Synapt Context Substrate** | Exactly the unstructured-document ingestion case it's built for, no restriction here |
| **Institutional memory** (narrative summaries of past bids — what was matched, decided, resolved) | **Synapt Context Substrate** | Document/narrative-shaped, not row-per-record — matches the "connecting knowledge across time" use case Sivaraman described |

**Open item:** the catalog is a borderline case (structured, but each row is
a short, largely self-contained description, not deeply relational like a
CRM). We asked Sivaraman directly whether a 600-row catalog like ours would
still work in Context Substrate or falls into the same category as CRM/ERP
data. **Update this table if his answer changes the recommendation** —
this decision should come from his direct answer, not just our inference
from the workshop.

## Stage 1 — Bid document intake

**What it does:** Accepts a bid document in any format (PDF, Excel, email
text) and extracts a structured list of requested items + quantities.

**Implementation notes:**
- Use Claude for extraction — give it the raw document content/text and ask
  for structured JSON output (item description, quantity, any spec details).
- Don't try to build a rules-based parser per format. Let the LLM handle
  format variance; that's the whole point of using it here.
- Output contract: a list of `{raw_description: str, quantity: int}` objects
  that Stage 2 consumes.

## Stage 2 — Item Matching Service

**What it does:** For each extracted item, finds the best-matching SKU in
Sysco's (synthetic) catalog using semantic search, not keyword matching.

**Implementation notes:**
- Uses **our own Postgres + pgvector**, not Context Substrate — see "Data
  source split" above for why.
- Generate embeddings for the catalog once (on load/seed), store in
  `pgvector`. See `DATA_MODEL.md` for the `products` table.
- For each incoming item: embed the description, run a similarity search,
  take the top-5 candidates, then use Claude to re-rank and pick the best
  match with a short explanation ("why this match") — this explanation is
  what makes the demo feel intelligent rather than a black-box lookup.
- Output contract: `{raw_description, matched_sku, confidence, explanation}`.

**Not Agent Hub-registered.** This is a backend service, not an agent — see
"Agent Hub scoping decision" below.

## Stage 3 — Institutional Memory Check

**What it does:** Before running outreach from scratch, checks whether a
similar past bid exists and reuses its matches/supplier picks if so. This
is what powers the "Bid B resolves faster" demo moment.

**Implementation notes:**
- Uses **Synapt Context Substrate**, not our own pgvector — see "Data
  source split" above. Past-bid summaries are narrative/document-shaped
  (what was matched, who was selected, how it resolved), which fits
  Context Substrate's ingestion model well, unlike the row-per-record
  catalog.
- Ingest each completed bid as a short narrative document rather than a
  raw data dump — Context Substrate organizes this into its knowledge
  graph automatically (workshop noted ~5–10 min turnaround per ingestion).
- Query it with a prompt describing the new bid; it returns one
  consolidated answer rather than a set of raw hits to re-rank ourselves.
- Similarity should still capture: item overlap, customer segment, recency
  — encode these into the query prompt / ingested narrative structure.
- If a strong match is found, short-circuit parts of Stage 2/4 with cached
  results instead of recomputing — this is literally the performance
  difference the demo needs to show.

**Not Agent Hub-registered** — same reasoning as Stage 2.

## Stage 4 — Outreach Agent

**What it does:** Given matched items + candidate suppliers, drafts
personalized outreach messages and tracks response status.

**Implementation notes:**
- This IS the Agent Hub-registered agent. See `AGENT_MANIFESTS.md` for the
  manifest.
- Drafts, but never sends, without passing through Stage 5.
- For the demo: simulate sending (a mock inbox view is sufficient) rather
  than depending on real email infrastructure — don't make the live demo
  fragile to real network/email delivery issues.

## Stage 5 — Human Approval Gate

**What it does:** A reviewer sees drafted outreach and explicitly
approves/rejects before anything is marked "sent."

**Implementation notes:**
- Simple UI: list of pending drafts, Approve/Reject buttons.
- This satisfies the governance principle from the Agent Hub workshop:
  *"low autonomy agents with a clean approval record is a stronger
  submission than a fully autonomous one nobody can audit."* Make this
  visible in the demo, not just implemented — it's a pitch strength, not
  just a safety feature.

## Stage 6 — Tracking Dashboard

**What it does:** Shows live status of matching, outreach, and approvals.
Also the surface where the "time saved" stat gets displayed for the demo.

**Implementation notes:**
- React frontend, pulls live bid/matching/outreach state from the backend.
- Structured run state can live in Postgres tables (`bids`, `bid_items`,
  `outreach`) once persistence lands.
- On completion, writes a narrative summary of the finalized bid into
  Synapt Context Substrate (closes the loop into Stage 3 for future bids).

## Agent Hub scoping decision (don't relitigate without reason)

**Only the Outreach Agent is registered in Synapt Agent Hub.** Item Matching
and Institutional Memory are plain backend services calling Context
Substrate directly.

**Why:** Agent Hub's value is governing *consequential actions* — autonomy
levels, approval gates, versioning, audit trails. Item Matching and Memory
Check don't act on the outside world, they just retrieve and return
information — there's nothing to approve or gate. The Outreach Agent
drafts something that will eventually go to an external supplier, which is
exactly the kind of action the Agent Hub governance model exists for.

**Pitch framing:** this is not "using less Synapt IP," it's putting
governance precisely where the workshop said it belongs — on actions with
real-world consequences, not on retrieval.

## Open questions to resolve before finalizing this doc further

- **Agent Hub glue code:** how much manual glue code is required to connect
  multiple services/agents into one working pipeline, given Agent Hub's
  Build/Deploy phases were described as only partially available. Get a
  concrete answer from the Synapt Agent Hub team (via Gopi) and update this
  section once known — it affects the Week 3–4 time estimate in
  `ROADMAP.md`.
- **Catalog fit for Context Substrate:** confirm directly with Sivaraman
  whether our 600-row product catalog is small/self-contained enough to fit
  Context Substrate despite being row-per-record, or whether it should
  stay in our own Postgres/pgvector as currently planned. If his answer
  changes the recommendation, update the "Data source split" table above
  and `DATA_MODEL.md` accordingly.
