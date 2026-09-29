const LABELS = {
  APPROVED: "Approved",
  DENIED: "Denied",
  ESCALATED: "Escalated",
};

// Renders an outcome as an ink-stamp mark. `size` controls scale;
// `animate` plays the stamp-impact entrance for freshly decided requests.
export default function OutcomeStamp({ outcome, size = "md", animate = false }) {
  const label = LABELS[outcome] || outcome;
  const className = [
    "stamp",
    `stamp--${outcome?.toLowerCase()}`,
    `stamp--${size}`,
    animate ? "stamp--animate" : "",
  ]
    .filter(Boolean)
    .join(" ");
  return <span className={className}>{label}</span>;
}
