import React, { useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  CheckCircle2,
  Clock3,
  FileText,
  MailCheck,
  RefreshCw,
  Route,
  Search,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import "./styles.css";

const API_BASE = "http://127.0.0.1:8000";

const stageIcons = {
  "Bid document intake": FileText,
  "Item Matching Service": Search,
  "Institutional Memory Check": Sparkles,
  "Outreach Agent": MailCheck,
  "Human Approval Gate": ShieldCheck,
  "Tracking Dashboard": Route,
};

function App() {
  const [demo, setDemo] = useState(null);
  const [selectedBidIndex, setSelectedBidIndex] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState("");
  const [reviewerName, setReviewerName] = useState("");
  const [approvalStatus, setApprovalStatus] = useState(null);
  const [isApproving, setIsApproving] = useState(false);

  const selectedRun = demo?.runs?.[selectedBidIndex] ?? null;
  const comparison = useMemo(() => {
    if (!demo || demo.runs.length < 2) return null;
    const [cold, warm] = demo.runs;
    return {
      coldSteps: cold.metrics.simulated_steps,
      warmSteps: warm.metrics.simulated_steps,
      saved: warm.metrics.simulated_steps_saved,
      reused: warm.metrics.memory_reused_items,
      total: warm.metrics.total_items,
    };
  }, [demo]);

  async function runDemo() {
    setIsRunning(true);
    setError("");
    setApprovalStatus(null);
    try {
      const response = await fetch(`${API_BASE}/pipeline/v2/run-demo/both`, {
        method: "POST",
      });
      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }
      const payload = await response.json();
      setDemo(payload);
      setSelectedBidIndex(0);
    } catch (err) {
      setError(
        "Could not reach the FastAPI backend. Start it from /backend with: uvicorn app.main:app --host 127.0.0.1 --port 8000"
      );
    } finally {
      setIsRunning(false);
    }
  }

  async function resetMemory() {
    try {
      await fetch(`${API_BASE}/pipeline/v2/reset-memory`, { method: "POST" });
      setDemo(null);
      setApprovalStatus(null);
    } catch (err) {
      setError("Could not reset memory. Is the backend running?");
    }
  }

  async function approveOutreach() {
    if (!selectedRun || !reviewerName.trim()) {
      setError("Enter a reviewer name before approving.");
      return;
    }
    setIsApproving(true);
    setError("");
    try {
      const response = await fetch(`${API_BASE}/pipeline/v2/approve/${selectedRun.bid_id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reviewer: reviewerName.trim() }),
      });
      if (!response.ok) {
        throw new Error(`Approval failed: ${response.status}`);
      }
      const result = await response.json();
      setApprovalStatus(result);
    } catch (err) {
      setError(`Approval error: ${err.message}`);
    } finally {
      setIsApproving(false);
    }
  }

  const pendingCount = selectedRun?.outreach.filter((d) => d.status === "pending_approval").length ?? 0;

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Sysco BidCoE demo</p>
          <h1>Intelligent Supplier Collaboration Portal</h1>
        </div>
        <div className="header-actions">
          <button className="secondary-action" onClick={resetMemory} disabled={isRunning}>
            Reset Memory
          </button>
          <button className="primary-action" onClick={runDemo} disabled={isRunning}>
            <RefreshCw size={18} className={isRunning ? "spin" : ""} />
            {isRunning ? "Running" : "Run Bid A/B Demo"}
          </button>
        </div>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <section className="summary-grid">
        <MetricCard label="Bid B memory reuse" value={comparison ? `${comparison.reused}/${comparison.total}` : "--"} />
        <MetricCard label="Simulated steps saved" value={comparison ? comparison.saved : "--"} />
        <MetricCard label="Cold run steps" value={comparison ? comparison.coldSteps : "--"} />
        <MetricCard label="Warm run steps" value={comparison ? comparison.warmSteps : "--"} />
      </section>

      <section className="workbench">
        <aside className="bid-list">
          <div className="panel-heading">
            <h2>Bids</h2>
          </div>
          {demo?.runs?.map((run, index) => (
            <button
              key={run.bid_id}
              className={`bid-tab ${index === selectedBidIndex ? "active" : ""}`}
              onClick={() => setSelectedBidIndex(index)}
            >
              <span>{run.bid_id}</span>
              <small>{run.customer_name}</small>
              <strong>
                {run.metrics.memory_reused_items
                  ? `${run.metrics.memory_reused_items} reused`
                  : "cold run"}
              </strong>
            </button>
          ))}
          {!demo && (
            <div className="empty-state">
              <Clock3 size={22} />
              <p>Run the demo to load Bid A and Bid B.</p>
            </div>
          )}
        </aside>

        <section className="main-panel">
          {selectedRun ? (
            <RunDetails
              run={selectedRun}
              reviewerName={reviewerName}
              setReviewerName={setReviewerName}
              onApprove={approveOutreach}
              isApproving={isApproving}
              approvalStatus={approvalStatus}
              pendingCount={pendingCount}
            />
          ) : (
            <IntroPanel />
          )}
        </section>
      </section>
    </main>
  );
}

function MetricCard({ label, value }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function IntroPanel() {
  return (
    <div className="intro-panel">
      <h2>Demo Flow</h2>
      <p>
        Run Bid A and Bid B back-to-back. Bid A establishes the memory record;
        Bid B reuses overlapping matches so the team can see the learning loop.
        Then approve the outreach to simulate sending to suppliers.
      </p>
    </div>
  );
}

function RunDetails({ run, reviewerName, setReviewerName, onApprove, isApproving, approvalStatus, pendingCount }) {
  const reused = run.metrics.memory_reused_items;

  return (
    <>
      <div className="run-header">
        <div>
          <p className="eyebrow">{run.customer_segment}</p>
          <h2>{run.customer_name}</h2>
        </div>
        <div className="run-score">
          <span>{reused ? "Warm run" : "Cold run"}</span>
          <strong>{run.metrics.simulated_steps_saved} steps saved</strong>
        </div>
      </div>

      <div className="stage-row">
        {run.stages.map((stage) => {
          const Icon = stageIcons[stage.name] ?? CheckCircle2;
          return (
            <div className="stage-chip" key={stage.name} title={stage.details}>
              <Icon size={18} />
              <span>{stage.name.replace(" Service", "").replace(" Gate", "")}</span>
            </div>
          );
        })}
      </div>

      {run.memory_hit?.found && (
        <div className="memory-banner">
          <Sparkles size={16} />
          <span>
            Memory hit: {run.memory_hit.overlap_count} items reused from {run.memory_hit.source_bid_id}
            {" "}({Math.round(run.memory_hit.overlap_ratio * 100)}% overlap)
          </span>
        </div>
      )}

      <div className="content-grid">
        <section className="data-panel">
          <div className="panel-heading">
            <h3>Matched Items</h3>
            <span>{run.metrics.fresh_matches} fresh / {run.metrics.memory_reused_items} reused</span>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Request</th>
                  <th>Matched SKU</th>
                  <th>Confidence</th>
                  <th>Source</th>
                </tr>
              </thead>
              <tbody>
                {run.matched_items.map((item) => (
                  <tr key={`${item.raw_description}-${item.matched_sku}`}>
                    <td>
                      <strong>{item.raw_description}</strong>
                      <small>{item.quantity} units</small>
                    </td>
                    <td>
                      <strong>{item.matched_sku}</strong>
                      <small>{item.matched_name}</small>
                    </td>
                    <td>{Math.round(item.confidence * 100)}%</td>
                    <td>
                      <span className={`source-pill ${item.source}`}>
                        {item.source === "memory_reuse" ? "memory" : "fresh"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="data-panel">
          <div className="panel-heading">
            <h3>Outreach Drafts</h3>
            <span>{run.outreach.length} pending approval</span>
          </div>

          {/* Human Approval Gate UI */}
          <div className="approval-gate">
            <div className="approval-input-row">
              <input
                type="text"
                placeholder="Reviewer name (human, not the agent)"
                value={reviewerName}
                onChange={(e) => setReviewerName(e.target.value)}
                className="reviewer-input"
              />
              <button
                className="approve-button"
                onClick={onApprove}
                disabled={isApproving || pendingCount === 0}
              >
                <ShieldCheck size={16} />
                {isApproving ? "Approving..." : `Approve & Send (${pendingCount})`}
              </button>
            </div>
            {approvalStatus && (
              <div className="approval-confirm">
                <CheckCircle2 size={14} />
                Approved by <strong>{approvalStatus.approved_by}</strong> — {approvalStatus.note}
              </div>
            )}
            <p className="approval-note">
              Governance: the Outreach Agent drafts but never sends. A separate human reviewer
              must approve before anything goes out — this is the Agent Hub autonomy boundary.
            </p>
          </div>

          <div className="draft-list">
            {run.outreach.slice(0, 7).map((draft) => (
              <article className="draft-item" key={`${draft.raw_description}-${draft.supplier_email}`}>
                <div>
                  <strong>{draft.supplier_name}</strong>
                  <small>{draft.supplier_email}</small>
                </div>
                <p>{draft.drafted_message}</p>
                <span className={`status-badge ${draft.status}`}>
                  {draft.status === "pending_approval" ? "Pending approval" : draft.status}
                </span>
              </article>
            ))}
          </div>
        </section>
      </div>
    </>
  );
}

createRoot(document.getElementById("root")).render(<App />);
