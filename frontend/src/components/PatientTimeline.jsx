/**
 * PatientTimeline — renders encounter history from backend timeline payload.
 * Shape: { encounter_count, timeline: [{ encounter_id, date, event, status }] }
 */
export function PatientTimeline({ timeline }) {
  const events = timeline?.timeline ?? timeline?.encounters ?? [];

  if (!events.length) {
    return (
      <p style={{ color: "var(--text-muted)", fontStyle: "italic", fontSize: "0.9rem" }}>
        No previous encounters found for this patient.
      </p>
    );
  }

  const statusColor = (s = "") => {
    const st = s.toUpperCase();
    if (st === "FINALIZED") return "var(--risk-low)";
    if (st === "REVIEW_REQUIRED") return "var(--risk-moderate)";
    if (st === "PROCESSING") return "var(--border-focus)";
    return "var(--text-muted)";
  };

  const statusLabel = (s = "") => {
    const map = {
      FINALIZED: "Finalized",
      REVIEW_REQUIRED: "Pending Review",
      PROCESSING: "Processing",
    };
    return map[s.toUpperCase()] ?? s;
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 0, position: "relative" }}>
      <div style={{
        position: "absolute", left: "11px", top: "16px",
        bottom: "16px", width: "2px",
        background: "linear-gradient(to bottom, var(--primary-blue), #e2e8f0)",
        borderRadius: "2px",
      }} />

      {events.map((item, idx) => {
        const key = item.encounter_id || item.id || idx;
        const title = item.event || item.chief_complaint || "Clinical Encounter";
        const dateValue = item.date || item.created_at;

        return (
          <div key={key} style={{ display: "flex", gap: "1rem", marginBottom: "1.25rem", position: "relative" }}>
            <div style={{
              width: 24, height: 24, borderRadius: "50%", flexShrink: 0,
              background: idx === 0 ? "var(--primary-blue)" : "#e2e8f0",
              border: `2px solid ${idx === 0 ? "var(--primary-blue)" : "#cbd5e1"}`,
              display: "grid", placeItems: "center", zIndex: 1,
            }}>
              <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#fff" }} />
            </div>

            <div style={{
              flex: 1, background: "#fff", border: "1px solid var(--border-light)",
              borderRadius: "10px", padding: "0.85rem 1rem",
              boxShadow: "var(--shadow-sm)",
              borderLeft: idx === 0 ? "3px solid var(--primary-blue)" : "3px solid #e2e8f0",
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "0.5rem", marginBottom: "0.35rem" }}>
                <span style={{ fontWeight: 700, fontSize: "0.9rem", color: "var(--text-primary)" }}>
                  {title}
                </span>
                <span style={{
                  fontSize: "0.75rem", fontWeight: 600, padding: "0.15rem 0.5rem",
                  borderRadius: "9999px", background: `${statusColor(item.status)}18`,
                  color: statusColor(item.status), whiteSpace: "nowrap",
                }}>
                  {statusLabel(item.status)}
                </span>
              </div>
              {dateValue && (
                <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  {new Date(dateValue).toLocaleDateString("en-IN", {
                    day: "2-digit", month: "short", year: "numeric",
                  })}
                </div>
              )}
            </div>
          </div>
        );
      })}

      <div style={{ marginLeft: "2rem", fontSize: "0.8rem", color: "var(--text-muted)", fontStyle: "italic" }}>
        {timeline?.encounter_count ?? events.length} encounter{events.length !== 1 ? "s" : ""} total
      </div>
    </div>
  );
}
