export function EvidenceChain({ sources = [], activeId, onSelect, detail }) {
  if (!sources.length) {
    return (
      <p style={{ color: "var(--cv-slate-500)", fontSize: "var(--cv-text-sm)" }}>
        No evidence sources available for this case.
      </p>
    );
  }

  const active = sources.find((s) => s.id === activeId) || sources[0];

  return (
    <div className="cv-evidence-chain">
      {sources.map((source, idx) => (
        <div key={source.id} className="cv-evidence-node">
          <div>
            <div
              style={{
                width: 10,
                height: 10,
                borderRadius: "50%",
                background: activeId === source.id ? "var(--cv-primary)" : "var(--cv-slate-200)",
                margin: "6px auto",
              }}
            />
            {idx < sources.length - 1 && <div className="cv-evidence-line" />}
          </div>
          <button
            type="button"
            className="cv-evidence-card"
            style={{
              width: "100%",
              textAlign: "left",
              cursor: "pointer",
              border: activeId === source.id ? "1px solid var(--cv-primary)" : undefined,
              background: activeId === source.id ? "var(--cv-primary-muted)" : undefined,
            }}
            onClick={() => onSelect(source.id)}
          >
            <h4>{source.label}</h4>
            <p>{source.meta}</p>
          </button>
        </div>
      ))}

      {active && (
        <div className="cv-panel cv-panel-pad" style={{ marginTop: "var(--cv-space-2)" }}>
          <h4 style={{ margin: "0 0 8px", fontSize: "var(--cv-text-sm)", fontWeight: 600 }}>
            Source reference
          </h4>
          <pre
            style={{
              margin: 0,
              fontSize: "var(--cv-text-xs)",
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
              color: "var(--cv-slate-700)",
              maxHeight: 200,
              overflow: "auto",
            }}
          >
            {active.snippet}
          </pre>
          {detail?.documents?.length > 0 && (
            <div style={{ marginTop: 12, fontSize: "var(--cv-text-xs)", color: "var(--cv-slate-500)" }}>
              Files: {detail.documents.map((d) => d.file_name).join(", ")}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
