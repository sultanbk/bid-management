# Business Context

## The client: Sysco

World's largest food-away-from-home distributor.

- $84B+ annual revenue (FY2026)
- ~670,000 customer locations (restaurants, hospitals, schools, casinos, retail chains)
- 333 distribution centers, 10 countries
- 275,000+ products in catalog
- Competitors: US Foods, Performance Food Group, Gordon Food Service

At this scale, a manual/email-driven process is a structural bottleneck on
growth, not a minor inconvenience. Use these numbers when justifying why
automation matters — "saves one team some emails" undersells it; "removes a
bottleneck that scales with 670K customer relationships" is accurate.

## The business problem: bid management

A customer (hospital, school, restaurant chain, retailer, etc.) wants to
source food/supplies for ~3 years and puts it out to bid. Sysco competes
against other distributors to win it.

### The lifecycle (11 stages, per Sysco's own process documentation)

| # | Stage | Status in Sysco's existing tools (BidGenie/ChaMP) |
|---|---|---|
| 1 | Identify Bids | No — not covered |
| 2 | Bid Intake | Yes — covered |
| 3 | Bid Verification | Yes — covered |
| 4 | Identify Suppliers | Yes — covered |
| 5 | Solicit / Manage Response | Yes on paper, but customer states this is still their #1 real bottleneck |
| 6 | Item Matching | Stub — partial/placeholder |
| 7 | Item Content Readiness | Stub |
| 8 | RevMan (Pricing) | Stub |
| 9 | Regional Approval | No |
| 10 | Customer Communication | No |
| 11 | Customer Onboarding | No |

**"Stub" = half-built, not usable.** "Yes" stages are already covered — don't
rebuild them. Our project targets stage 5 (real pain, not just claimed
coverage) and stage 6 (explicitly incomplete).

### Narrative walkthrough

1. Customer sends a document — PDF, Excel, scanned invoice, menu card. No
   standard format.
2. Internal system **Bix** vets it against Sysco's catalog.
3. The **AST** team manually searches millions of SKUs to find equivalent
   Sysco products for whatever the customer listed.
4. Sysco needs prices from its own suppliers. For **X requested items × Y
   candidate suppliers per item**, someone manually emails every combination
   — e.g. 100 items × 10 suppliers = up to 1,000 emails, over Outlook, no
   system of record. **This is the single biggest stated pain point.**
5. Sales team (~8,000 consultants) reviews the resulting assortment.
6. Pricing/Revenue team (**MCC → RevMan** handoff) finalizes margins — today
   this handoff is an informal working file, not structured.
7. Bid is submitted.
8. If won, Operations (warehouse/**OPCO**) fulfills.

### Existing Sysco tools — don't duplicate these

- **BidGenie** — centralizes vendor communication, suggests items from RFP
  criteria, tracks supplier docs. **Demo stage only, not live.**
- **ChaMP XL** — roadmap to integrate BEx + AST + ChaMP and improve AST's
  match rate. Also demo/roadmap stage.

### Pain points, direct from the customer (use these verbatim in pitches)

1. **Manual supplier solicitation** over Outlook, no system of record — the
   single biggest bottleneck.
2. **BEx ↔ AST not integrated** — items extracted by BEx are manually
   re-entered into AST for matching.
3. **AST matching algorithm gaps** — match quality needs improvement.
4. **No structured MCC → RevMan handoff** — informal working file only.
5. **Boilerplate RFP responses not automated** — assembled manually every bid.
6. **No institutional memory** — no persistent catalogs or repeat-bid reuse;
   every bid starts from scratch.
7. **Limited native Salesforce AI** — some automation needs to live outside
   Salesforce as independent agents. (This is why we're building standalone,
   not inside SF360.)
8. **15+ fragmented point systems** (SF360, BEx, AST, SMT, SUS, SIM360, etc.)

## Our scope: Use Case 1 only, this cycle

**Intelligent Supplier Collaboration Portal**
Auto-extracts supplier pricing submissions and compiles a structured working
document, replacing manual RFQ compilation. Targets pain points #1 and #3
directly.

- Projected impact: 70–80% reduction in manual RFQ processing time
- ROI timeline: 3–6 months
- Synapt IP: Agent Hub (outreach agent governance), Context Substrate
  (bid-document ingestion + institutional memory)

Use Cases 2 (Predictive Supplier Matching) and 3 (Dynamic Pricing
Intelligence) are designed and documented as Phase 2 candidates — **not
built this cycle.** See `../CLAUDE.md` §3 for the scope-discipline rule.

## Domain glossary

| Term | Meaning |
|---|---|
| **RFQ** | Request for Quote — asking a supplier for pricing on an item |
| **SKU** | Stock Keeping Unit — a specific product in Sysco's catalog |
| **Bix** | Internal system that vets incoming bid documents against the catalog |
| **AST** | Team/tool that manually matches customer-requested items to Sysco SKUs |
| **BEx** | Tool that extracts items from bid documents (feeds into AST, manually today) |
| **MCC** | Merchandise Customer Contract — the working file/decisions before pricing |
| **RevMan** | Revenue Management — finalizes pricing/margin |
| **OPCO** | Operating Company / warehouse — fulfills the order after a bid is won |
| **FDE** | Forward Deployed Engineer — the model where we build agents that build the platform, rather than building the platform directly |
| **BidCoE** | Bid Center of Excellence — the larger proposal this project feeds into |
| **SF360** | Salesforce, the CRM Sysco's current bid tooling partly runs on |
