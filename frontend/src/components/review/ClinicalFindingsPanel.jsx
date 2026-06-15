import { formatClinicalSummary } from "../../utils/clinicalSummaryFormat";

export function ClinicalFindingsPanel({
  summaryText,
  labAnalysis,
  docType,
  imaging,
  confidence,
  isFinalized,
  canReview,
  onFinalize,
  finalizing,
}) {
  const formatted = formatClinicalSummary(summaryText, labAnalysis, { docType, imaging });
  const pct = confidence != null ? Math.round(confidence * 100) : null;
  const confidenceCaption =
    docType === "xray"
      ? "Based on ChestNet image analysis signals."
      : "Based on OCR, NLP, and document quality signals.";

  return (
    <section className="cv-findings-primary" aria-labelledby="findings-heading">
      <div className="cv-findings-hero">
        <h2 id="findings-heading">AI clinical summary</h2>
        <p className="cv-findings-headline">{formatted.headline}</p>

        {formatted.attention.length > 0 && (
          <div className="cv-finding-attention">
            <h4>Key findings requiring attention</h4>
            <ul>
              {formatted.attention.map((item) => (
                <li key={item.test}>
                  <strong>{item.test}</strong> ({item.flag}) — {item.text}
                </li>
              ))}
            </ul>
          </div>
        )}

        {formatted.healthy.length > 0 && (
          <div className="cv-finding-healthy">
            <strong>Within normal range:</strong> {formatted.healthy.join(", ")}
          </div>
        )}

        {formatted.showFullNote && (
          <details className="cv-admin-fold" style={{ marginTop: "var(--cv-space-3)" }}>
            <summary>Full clinical notes</summary>
            <div className="cv-admin-body">
              <p style={{ margin: 0, fontSize: "var(--cv-text-sm)", lineHeight: 1.6 }}>{formatted.doctorNote}</p>
            </div>
          </details>
        )}

        {canReview && !isFinalized && (
          <button
            type="button"
            className="cv-btn cv-btn-primary cv-btn-block"
            style={{ marginTop: "var(--cv-space-3)" }}
            onClick={onFinalize}
            disabled={finalizing}
          >
            {finalizing ? "Approving…" : "Physician approves summary"}
          </button>
        )}
        {isFinalized && (
          <div className="success-banner" style={{ marginTop: "var(--cv-space-2)" }}>
            Summary approved and finalized.
          </div>
        )}
      </div>

      <aside>
        {pct != null && (
          <div className="cv-confidence-card">
            <p className="cv-confidence-label">Model confidence</p>
            <div className="cv-confidence-value">{pct}%</div>
            <div className="cv-confidence-bar">
              <div className="cv-confidence-bar-fill" style={{ width: `${pct}%` }} />
            </div>
            <p style={{ margin: "12px 0 0", fontSize: "var(--cv-text-xs)", color: "var(--cv-slate-400)" }}>
              {confidenceCaption}
            </p>
          </div>
        )}

        <NextStepsInline precautions={labAnalysis?.precautions || []} docType={docType} />
      </aside>
    </section>
  );
}

function NextStepsInline({ precautions, docType }) {
  if (!precautions.length) {
    return (
      <div className="cv-next-steps">
        <h3>Recommended next steps</h3>
        <p style={{ margin: 0, fontSize: "var(--cv-text-sm)", color: "var(--cv-slate-500)" }}>
          {docType === "xray"
            ? "Correlate the scan with symptoms and have a radiologist or physician review the image."
            : "No urgent actions. Correlate with clinical presentation and discuss at next visit."}
        </p>
      </div>
    );
  }

  return (
    <div className="cv-next-steps">
      <h3>Recommended next steps</h3>
      <ol>
        {precautions.slice(0, 4).map((p) => (
          <li key={p.test}>
            <strong>{p.test}</strong> ({p.flag}): {p.precaution}
          </li>
        ))}
      </ol>
      <p style={{ margin: "12px 0 0", fontSize: "var(--cv-text-xs)", color: "var(--cv-slate-500)" }}>
        Not a diagnosis. Physician judgment required.
      </p>
    </div>
  );
}
