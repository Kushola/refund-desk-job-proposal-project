import { useState } from "react";
import CustomerView from "./components/CustomerView";
import AdminView from "./components/AdminView";

export default function App() {
  const [tab, setTab] = useState("customer");

  return (
    <div className="app">
      <header className="app-header">
        <span className="wordmark">Refund Desk</span>
        <nav className="tabs" aria-label="Views">
          <button
            type="button"
            className={`tab ${tab === "customer" ? "tab--active" : ""}`}
            onClick={() => setTab("customer")}
          >
            Customer
          </button>
          <button
            type="button"
            className={`tab ${tab === "admin" ? "tab--active" : ""}`}
            onClick={() => setTab("admin")}
          >
            Admin
          </button>
        </nav>
      </header>
      <main className="app-main">{tab === "customer" ? <CustomerView /> : <AdminView />}</main>
    </div>
  );
}
