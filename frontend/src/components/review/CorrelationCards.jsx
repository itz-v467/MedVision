/** Cross-modal lab↔imaging correlation cards for unified cases. */

export function CorrelationCards({ correlation }) {
  const cards = correlation?.cards || [];
  if (!cards.length) return null;

  return (
    <section className="cv-section" aria-labelledby="correlation-heading">
      <h2 className="cv-section-title" id="correlation-heading">Cross-modal correlation</h2>
      <p className="cv-section-sub">
        Automated links between laboratory results and chest imaging — for physician review only.
      </p>
      <div className="cv-correlation-grid">
        {cards.map((card, idx) => (
          <article
            key={`${card.label}-${idx}`}
            className={`cv-correlation-card${card.tone === "alert" ? " is-alert" : ""}`}
          >
            <h3 className="cv-correlation-card-title">{card.label}</h3>
            <p className="cv-correlation-card-value">{card.value}</p>
            {card.note && <p className="cv-correlation-card-note">{card.note}</p>}
          </article>
        ))}
      </div>
      {typeof correlation?.weighted_evidence_score === "number" && (
        <p className="cv-correlation-score">
          Cross-source agreement score: {Math.round(correlation.weighted_evidence_score * 100)}%
        </p>
      )}
    </section>
  );
}
