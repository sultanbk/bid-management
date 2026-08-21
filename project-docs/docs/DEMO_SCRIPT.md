# Demo Script

**Every feature decision should trace back to making this demo better.** If
a piece of work doesn't serve this script, question whether it belongs in
this cycle at all (see `CLAUDE.md` §3, scope discipline).

## The core demo moment

Two similar bids, run back-to-back, live:

1. **Bid A runs cold.** Full pipeline: document in → items extracted →
   matched to catalog → no relevant memory found → outreach drafted →
   approved → tracked. Takes the "full" time.
2. **Bid B runs second**, with meaningfully overlapping items/customer
   segment. The system recognizes similarity to Bid A via Institutional
   Memory and resolves faster — fewer new matches needed, outreach can reuse
   prior supplier picks where appropriate.
3. **The visible proof point:** a timer or step-count comparison between Bid
   A and Bid B on the Tracking Dashboard. This is the single most important
   visual in the entire demo — it's the difference between "we built
   automation" and "we built a system that learns."

## Scenario details (fill in / finalize with the team — placeholder below)

**Bid A**
- Customer: `[e.g. "Riverside Regional Hospital"]`
- Segment: `hospital`
- Items requested: `~15-20 items` — mix of categories (disposables, proteins,
  dry goods) so matching has to do real work, not just exact-string luck
- Expected outcome: full pipeline run, all 6 stages visibly execute

**Bid B**
- Customer: `[e.g. "Lakeside Medical Center"]` — different customer, same
  segment (`hospital`) as Bid A
- Items requested: significant overlap with Bid A's item list (aim for
  ~60-70% overlap) plus a few new items
- Expected outcome: overlapping items resolve via memory reuse, visibly
  faster; new items still go through the full matching flow (so it's clear
  the system isn't just replaying a script — it's doing less *because* it
  recognizes similarity, not because it's faking the second run)

## What "good" looks like in the room

- The live UI actually shows each stage lighting up/completing, not just a
  spinner then a final result — judges should see the pipeline, not just the
  output.
- The human approval step is visibly part of the flow, not skipped for
  demo speed — this is a deliberate pitch strength (see
  `ARCHITECTURE.md` §Stage 5), don't cut it to save 20 seconds.
- Have the exact "time saved" or "steps skipped" number ready to say out
  loud when Bid B finishes — don't make the audience infer the point.

## Fallback plan

Record a clean run of this exact script as backup video before the finale,
in case live demo hits a technical issue during judging. Live demo first,
video ready as safety net — never the other way around.

## To finalize before Week 1 ends

- [ ] Lock exact item lists for Bid A and Bid B (owner: PM)
- [ ] Confirm the overlap percentage actually produces a visible speed
      difference once real code is behind it, not just in theory
- [ ] Decide the exact "time saved" framing/number to say during the demo
