import { AlertTypes } from "../enums/alertTypes";

function priorityBadge(priority = "") {
  const p = priority.toUpperCase();
  if (p === "CRITICAL") return { cls: "badge-critical", label: "Critical" };
  if (p === "MODERATE" || p === "MEDIUM") return { cls: "badge-moderate", label: "Moderate" };
  return { cls: "badge-low", label: "Normal" };
}

export function AlertsTable({ alerts, onAcknowledge, acknowledgingId }) {
  if (!alerts?.length) {
    return (
      <div style={{
        textAlign: "center", padding: "2.5rem", color: "var(--text-muted)",
        background: "#f8fafc", borderRadius: "8px", fontSize: "0.95rem",
      }}>
        <div style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>✓</div>
        No active alerts — all clear.
      </div>
    );
  }

  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Priority</th>
          <th>Title</th>
          <th>Message</th>
          <th>Created</th>
          {onAcknowledge && <th style={{ textAlign: "right" }}>Action</th>}
        </tr>
      </thead>
      <tbody>
        {alerts.map((alert) => {
          const { cls, label } = priorityBadge(alert.priority);
          return (
            <tr
              key={alert.id}
              className={alert.priority === AlertTypes.CRITICAL ? "row-critical" : ""}
            >
              <td>
                <span className={`badge ${cls}`}>{label}</span>
              </td>
              <td style={{ fontWeight: 600 }}>{alert.title}</td>
              <td style={{ color: "var(--text-secondary)", maxWidth: "320px" }}>{alert.message}</td>
              <td style={{ whiteSpace: "nowrap", color: "var(--text-muted)", fontSize: "0.85rem" }}>
                {new Date(alert.created_at).toLocaleString("en-IN", {
                  day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit",
                })}
              </td>
              {onAcknowledge && (
                <td style={{ textAlign: "right" }}>
                  {alert.is_acknowledged ? (
                    <span style={{ color: "var(--risk-low)", fontWeight: 600, fontSize: "0.85rem" }}>
                      ✓ Acknowledged
                    </span>
                  ) : (
                    <button
                      type="button"
                      onClick={() => onAcknowledge(alert.id)}
                      disabled={acknowledgingId === alert.id}
                      style={{
                        background: "var(--primary-blue)", color: "#fff", border: "none",
                        padding: "0.4rem 0.85rem", borderRadius: "6px",
                        cursor: "pointer", fontSize: "0.85rem", fontWeight: 600,
                        opacity: acknowledgingId === alert.id ? 0.6 : 1,
                        transition: "opacity 0.15s",
                      }}
                    >
                      {acknowledgingId === alert.id ? "Saving…" : "Acknowledge"}
                    </button>
                  )}
                </td>
              )}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
