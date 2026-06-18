/** Ranked possible conditions from multimodal analysis. */

export function PossibleDiseasesReport({ report = [], patterns = [] }) {
  const items = report.length
    ? report
    : patterns.map((p, idx) => ({
        rank: idx + 1,
        condition: p.condition,
        likelihood: p.score >= 0.7 ? "high" : "moderate",
        key_evidence: p.evidence_factors || [],
        missing_data: [],
      }));

  if (!items.length) {
    return (
      <p className="cv-section-sub">
        Upload symptoms, labs, and imaging together for a ranked condition report.
      </p>
    );
  }

  return (
    <div className="cv-diseases-report">
      <ol className="cv-diseases-list">
        {items.map((item) => (
          <li key={`${item.rank}-${item.condition}`} className={`is-${item.likelihood || "low"}`}>
            <div className="cv-diseases-header">
              <span className="cv-diseases-rank">#{item.rank}</span>
              <strong>{item.condition}</strong>
              <span className={`cv-confidence-chip is-${item.likelihood || "low"}`}>{item.likelihood} likelihood</span>
            </div>
            {item.key_evidence?.length > 0 && (
              <ul>
                {item.key_evidence.map((ev) => (
                  <li key={ev}>{ev}</li>
                ))}
              </ul>
            )}
            {item.missing_data?.length > 0 && (
              <p className="cv-diseases-missing">
                Missing: {item.missing_data.join(", ")}
              </p>
            )}
          </li>
        ))}
      </ol>
    </div>
  );
}
