# Agent Manifests

Only one agent in this project is registered in Synapt Agent Hub: the
**Outreach Agent**. See `ARCHITECTURE.md` for why Item Matching and
Institutional Memory are not agents.

## Core principle (from the Agent Hub workshop, non-negotiable)

> "Low autonomy agents with a clean approval record is a stronger submission
> than a fully autonomous one nobody can audit."

Concretely:
- The Outreach Agent's autonomy is **low** — it drafts, it does not send.
- The author of the agent and the approver of its actions must be **separate
  roles** — never let one person's action both create and approve an
  outreach draft, even in testing shortcuts. This is a governance property
  the workshop explicitly called out; don't erode it for convenience.
- Nothing is edited in place. Every manifest change is a **new version**; the
  previous version stays in history. Don't overwrite `v1.0.0` — bump it.

## Outreach Agent manifest (draft — update as sandbox specifics become known)

```yaml
agent_id: sysco-supplier-outreach-v1
name: Supplier Outreach Agent
version: 1.0.0
owner: <team name>
description: >
  Drafts and tracks supplier outreach requests for matched bid items.
  Does not send communications without human approval.

allowed_actions:
  - draft_supplier_email
  - parse_supplier_reply
  - update_outreach_status

forbidden_actions:
  - send_email_without_approval
  - modify_final_pricing
  - contact_suppliers_outside_matched_list

autonomy_level: low
approval_required: true
approval_gate: human_reviewer   # separate role from the agent's author

kpis:
  - manual_processing_time_reduction
  - outreach_response_rate
  - approval_turnaround_time

target_platform: standalone_sandbox   # update once sandbox target is confirmed
```

## Things to confirm once sandbox access is live (update this file after)

- [ ] Exact manifest schema Agent Hub expects (field names/types may differ
      from the draft above — this is our best guess pre-sandbox)
- [ ] How registration actually happens (UI form, CLI, API push?)
- [ ] What the approval UI Agent Hub provides natively vs. what we need to
      build ourselves in our own dashboard
- [ ] Whether KPIs/telemetry need to be reported in a specific format for
      Agent Hub's observability features to pick them up
- [ ] Token spend note from the workshop: Agent Hub does **not** enforce
      token budgets today, even though you can declare one in the manifest.
      If cost control matters for the demo, we monitor it ourselves — don't
      assume Agent Hub is doing this for us.

## Versioning discipline for this project

- `v1.0.0` — initial manifest, matches architecture as of kickoff
- Bump minor version for scope changes within Use Case 1 (e.g. adding a new
  `allowed_action`)
- Bump major version only if the agent's fundamental role changes (should not
  happen this cycle — that would be scope creep, see `CLAUDE.md` §3)
- Record what changed and why at the bottom of this file, dated, so a new
  session can see the manifest's history without digging through git log.

### Changelog
- `v1.0.0` — initial draft, pending sandbox confirmation.
