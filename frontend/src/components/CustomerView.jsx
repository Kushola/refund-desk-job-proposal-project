import { useEffect, useState } from "react";
import { api } from "../api";
import OutcomeStamp from "./OutcomeStamp";

const money = (n) => `$${Number(n).toFixed(2)}`;

export default function CustomerView() {
  const [customers, setCustomers] = useState([]);
  const [customerId, setCustomerId] = useState("");
  const [orders, setOrders] = useState([]);
  const [orderId, setOrderId] = useState("");
  const [message, setMessage] = useState("");
  const [loadingOrders, setLoadingOrders] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.listCustomers().then(setCustomers).catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    if (!customerId) {
      setOrders([]);
      setOrderId("");
      return;
    }
    setLoadingOrders(true);
    setOrderId("");
    api
      .listOrders(customerId)
      .then(setOrders)
      .catch((e) => setError(e.message))
      .finally(() => setLoadingOrders(false));
  }, [customerId]);

  const selectedOrder = orders.find((o) => o.id === orderId);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!customerId || !orderId || !message.trim()) return;
    setSubmitting(true);
    setError("");
    setResult(null);
    try {
      const record = await api.submitRefundRequest({
        customer_id: customerId,
        order_id: orderId,
        message: message.trim(),
      });
      setResult(record);
    } catch (e) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  }

  function startOver() {
    setResult(null);
    setMessage("");
  }

  return (
    <div className="view view--customer">
      <section className="intake" aria-labelledby="intake-heading">
        <h1 id="intake-heading" className="intake__title">
          Request a refund
        </h1>
        <p className="intake__lede">
          Pick who you're signed in as for this demo, choose the order, and describe what happened.
        </p>

        <form className="intake__form" onSubmit={handleSubmit}>
          <label className="field">
            <span className="field__label">Customer</span>
            <select
              value={customerId}
              onChange={(e) => setCustomerId(e.target.value)}
              required
            >
              <option value="" disabled>
                Choose a customer&hellip;
              </option>
              {customers.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} &mdash; {c.id}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span className="field__label">Order</span>
            <select
              value={orderId}
              onChange={(e) => setOrderId(e.target.value)}
              disabled={!customerId || loadingOrders}
              required
            >
              <option value="" disabled>
                {loadingOrders ? "Loading orders…" : "Choose an order…"}
              </option>
              {orders.map((o) => (
                <option key={o.id} value={o.id} disabled={o.refunded}>
                  {o.id} &mdash; {o.item_name} ({money(o.amount)})
                  {o.refunded ? " · already refunded" : ""}
                </option>
              ))}
            </select>
          </label>

          {selectedOrder && (
            <dl className="order-facts">
              <div>
                <dt>Status</dt>
                <dd>{selectedOrder.status}</dd>
              </div>
              <div>
                <dt>Delivered</dt>
                <dd>{selectedOrder.delivered_date || "not yet"}</dd>
              </div>
              <div>
                <dt>Final sale</dt>
                <dd>{selectedOrder.final_sale ? "yes" : "no"}</dd>
              </div>
            </dl>
          )}

          <label className="field">
            <span className="field__label">What happened?</span>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="e.g. It arrived with a cracked screen."
              rows={4}
              maxLength={2000}
              required
            />
          </label>

          {error && <p className="form-error">{error}</p>}

          <button type="submit" className="btn btn--primary" disabled={submitting}>
            {submitting ? "Sending…" : "Send request"}
          </button>
        </form>
      </section>

      <section className="reply-pane" aria-live="polite">
        {!result && !submitting && (
          <p className="reply-pane__empty">Your decision and reply will appear here.</p>
        )}
        {submitting && <p className="reply-pane__empty">Reviewing your request&hellip;</p>}
        {result && (
          <div className="decision">
            <OutcomeStamp outcome={result.outcome} size="lg" animate />
            <div className="chat-bubble">{result.customer_reply}</div>
            <button type="button" className="btn btn--ghost" onClick={startOver}>
              Send another request
            </button>
          </div>
        )}
      </section>
    </div>
  );
}
