import { identityStatus } from "../../utils/clinicalSummaryFormat";

export function IdentityCard({ validation }) {
  const status = identityStatus(validation);
  if (!status || !validation) return null;

  return (
    <div className={`cv-identity cv-identity-${status.tone}`} role="status">
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          <strong>{status.title}</strong>
          <span style={{
            fontSize: "var(--cv-text-xs)",
            fontWeight: 600,
            padding: "2px 8px",
            borderRadius: 999,
            background: "rgba(0,0,0,0.06)",
          }}>
            {status.badge}
          </span>
        </div>
        <div style={{ display: "flex", gap: 24, marginTop: 8, flexWrap: "wrap", fontSize: "var(--cv-text-sm)" }}>
          <span><span style={{ color: "var(--cv-slate-500)" }}>Entered: </span>{validation.entered_name || "—"}</span>
          <span><span style={{ color: "var(--cv-slate-500)" }}>On report: </span>{validation.extracted_name || "Could not read"}</span>
        </div>
        {status.message && (
          <p style={{ margin: "8px 0 0", fontSize: "var(--cv-text-sm)", color: "var(--cv-slate-700)" }}>
            {status.message}
          </p>
        )}
      </div>
    </div>
  );
}
