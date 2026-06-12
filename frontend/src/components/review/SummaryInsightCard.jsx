import { formatClinicalSummary } from "../../utils/clinicalSummaryFormat";

export function SummaryInsightCard({ summaryText, labAnalysis, isFinalized, onFinalize, canReview, finalizing }) {
  const formatted = formatClinicalSummary(summaryText, labAnalysis);

  return (
    <div className="dash-card dash-card-hero">
      <div className="dash-card-head">
        <h2>What we found</h2>
        {isFinalized ? (
          <span className="dash-pill dash-pill-good">Approved by doctor</span>
        ) : (
          <span className="dash-pill dash-pill-warn">Awaiting review</span>
        )}
      </div>

      <p className="dash-insight-headline">{formatted.headline}</p>

      {formatted.attention.length > 0 && (
        <div className="dash-insight-block dash-insight-warn">
          <h4>Needs attention</h4>
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
        <div className="dash-insight-block dash-insight-good">
          <h4>Looks healthy</h4>
          <p>{formatted.healthy.join(" · ")}</p>
        </div>
      )}

      {formatted.showFullNote && (
        <details className="dash-details">
          <summary>Full notes for your doctor</summary>
          <p>{formatted.doctorNote}</p>
        </details>
      )}

      {canReview && !isFinalized && (
        <button type="button" className="dash-btn dash-btn-primary dash-btn-block" onClick={onFinalize} disabled={finalizing}>
          {finalizing ? "Saving…" : "Physician approves this summary"}
        </button>
      )}
      {isFinalized && <div className="dash-approved-banner">Summary approved and saved.</div>}
    </div>
  );
}
