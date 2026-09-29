import { useEffect, useState } from "react";
import { api } from "../api";
import OutcomeStamp from "./OutcomeStamp";

const OUTCOMES = ["APPROVED", "DENIED", "ESCALATED"];

const timeFmt = new Intl.DateTimeFormat(undefined, {
  month: "short",
  day: "numeric",
  hour: "numeric",
  minute: "2-digit",
});

function formatTime(iso) {
  if (!iso) return "—";
  return timeFmt.format(new Date(iso));
}

export default function AdminView() {
  const [rows, setRows] = useState([]);
  const [stats, setStats] = useState({});
  const [outcomeFilter, setOutcomeFilter] = useState("");
  const [expandedId, setExpandedId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  function load() {
    setLoading(true);
    setError("");
    Promise.all([api.listRefundRequests(outcomeFilter), api.getStats()])
      .then(([reqs, s]) => {
        setRows(reqs);
        setStats(s);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(load, [outcomeFilter]);

  const total = OUTCOMES.reduce((sum, o) => sum + (stats[o] || 0), 0);

  return (
    <div className="view view--admin">
      <div className="admin-header">
        <div>
          <h1 className="admin-header__title">Case log</h1>
          <p className="admin-header__lede">Every request, the rule that decided it, and why.</p>
        </div>
        <button type="button" className="btn btn--ghost" onClick={load} disabled={loading}>
          {loading ? "Refreshing…" : "Refresh"}
        </button>
      </div>

      <dl className="tally">
        <div className="tally__item">
          <dt>Total</dt>
          <dd>{total}</dd>
        </div>
        {OUTCOMES.map((o) => (
          <div className="tally__item" key={o}>
            <dt>{o.charAt(0) + o.slice(1).toLowerCase()}</dt>
            <dd className={`tally__count tally__count--${o.toLowerCase()}`}>{stats[o] || 0}</dd>
          </div>
        ))}
      </dl>

      <div className="filter-row" role="group" aria-label="Filter by outcome">
        <button
          type="button"
          className={`chip ${outcomeFilter === "" ? "chip--active" : ""}`}
          onClick={() => setOutcomeFilter("")}
        >
          All
        </button>
        {OUTCOMES.map((o) => (
          <button
            key={o}
            type="button"
            className={`chip chip--${o.toLowerCase()} ${outcomeFilter === o ? "chip--active" : ""}`}
            onClick={() => setOutcomeFilter(o)}
          >
            {o.charAt(0) + o.slice(1).toLowerCase()}
          </button>
        ))}
      </div>

      {error && <p className="form-error">{error}</p>}

      <div className="ledger-wrap">
        <table className="ledger">
          <thead>
            <tr>
              <th>Time</th>
              <th>Customer</th>
              <th>Order</th>
              <th>Outcome</th>
              <th>Rule</th>
              <th>Summary</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && !loading && (
              <tr>
                <td colSpan={6} className="ledger__empty">
                  No requests match this filter yet.
                </td>
              </tr>
            )}
            {rows.map((r) => (
              <RequestRow
                key={r.id}
                record={r}
                expanded={expandedId === r.id}
                onToggle={() => setExpandedId(expandedId === r.id ? null : r.id)}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function RequestRow({ record, expanded, onToggle }) {
  return (
    <>
      <tr className="ledger__row" onClick={onToggle} aria-expanded={expanded}>
        <td className="mono">{formatTime(record.created_at)}</td>
        <td className="mono">{record.customer_id}</td>
        <td className="mono">{record.order_id || "—"}</td>
        <td>
          <OutcomeStamp outcome={record.outcome} size="sm" />
        </td>
        <td className="mono">{record.rule_id}</td>
        <td className="ledger__summary">{record.summary}</td>
      </tr>
      {expanded && (
        <tr className="ledger__detail-row">
          <td colSpan={6}>
            <RequestDetail record={record} />
          </td>
        </tr>
      )}
    </>
  );
}

function RequestDetail({ record }) {
  const intent = record.extracted || {};
  return (
    <div className="detail">
      <div className="detail__col">
        <h3>Customer message</h3>
        <p className="detail__message">&ldquo;{record.message}&rdquo;</p>
        <h3>Reply sent</h3>
        <p className="detail__message">{record.customer_reply}</p>
      </div>

      <div className="detail__col">
        <h3>Extracted intent</h3>
        <dl className="kv">
          <div>
            <dt>Reason</dt>
            <dd className="mono">{intent.reason || "—"}</dd>
          </div>
          <div>
            <dt>Claimed amount</dt>
            <dd className="mono">
              {intent.claimed_amount != null ? `$${intent.claimed_amount}` : "—"}
            </dd>
          </div>
          <div>
            <dt>Order mentioned in text</dt>
            <dd className="mono">{intent.mentioned_order_id || "—"}</dd>
          </div>
          <div>
            <dt>Decided by</dt>
            <dd className="mono">{record.decided_by}</dd>
          </div>
        </dl>
        {record.flags?.length > 0 && (
          <>
            <h3>Guardrail flags</h3>
            <ul className="flag-list">
              {record.flags.map((f, i) => (
                <li key={i} className="mono">
                  {f}
                </li>
              ))}
            </ul>
          </>
        )}
      </div>

      <div className="detail__col detail__col--wide">
        <h3>Audit trail</h3>
        <ol className="audit-trail">
          {(record.audit || []).map((check, i) => (
            <li key={i} className={check.passed ? "audit-trail__ok" : "audit-trail__stop"}>
              <span className="mono audit-trail__rule">{check.rule}</span>
              <span>{check.detail}</span>
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}
