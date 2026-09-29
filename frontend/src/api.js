const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5000/api";

async function request(path, options) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const message = body?.error || `Request failed (${res.status})`;
    throw new Error(message);
  }
  return body;
}

export const api = {
  health: () => request("/health"),
  listCustomers: () => request("/customers"),
  listOrders: (customerId) => request(`/customers/${customerId}/orders`),
  submitRefundRequest: (payload) =>
    request("/refund-requests", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listRefundRequests: (outcome) =>
    request(`/refund-requests${outcome ? `?outcome=${outcome}` : ""}`),
  getStats: () => request("/stats"),
};
