const ICONS = {
  critical: "▲",
  high: "▲",
  moderate: "●",
  medium: "●",
  low: "—",
  success: "✓",
  info: "◆",
  warning: "!",
  pending: "○",
  approved: "✓",
};

export function StatusBadge({ tone = "low", label, children }) {
  const text = children || label;
  const icon = ICONS[tone] || "•";
  return (
    <span className={`cv-status-badge is-${tone}`}>
      <span className="cv-status-badge-icon" aria-hidden="true">{icon}</span>
      {text}
    </span>
  );
}
