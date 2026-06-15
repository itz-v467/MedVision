function EvidenceCard({ card }) {
  return (
    <div className={`cv-evidence-card${card.tone ? ` is-${card.tone}` : ""}`}>
      <span className="cv-evidence-card-label">{card.label}</span>
      <span className="cv-evidence-card-value">{card.value}</span>
      {card.note && <span className="cv-evidence-card-note">{card.note}</span>}
    </div>
  );
}

function EvidenceRows({ rows }) {
  if (!rows?.length) return null;
  return (
    <div className="cv-evidence-table-wrap">
      <table className="cv-evidence-table">
        <thead>
          <tr>
            <th scope="col">Finding / test</th>
            <th scope="col">Result</th>
            <th scope="col">Clinical note</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={`${row.label}-${row.value}`} className={row.tone ? `is-${row.tone}` : ""}>
              <td>{row.label}</td>
              <td>{row.value}</td>
              <td>{row.note || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function EvidenceChain({ sources = [], activeId, onSelect, detail }) {
  if (!sources.length) {
    return (
      <p className="cv-evidence-empty">
        No supporting information is available for this case yet.
      </p>
    );
  }

  const active = sources.find((s) => s.id === activeId) || sources[0];
  const fileNames = detail?.documents?.map((d) => d.file_name).filter(Boolean) || [];

  return (
    <div className="cv-evidence">
      <div className="cv-evidence-steps" role="tablist" aria-label="How the summary was built">
        {sources.map((source) => {
          const isActive = active.id === source.id;
          return (
            <button
              key={source.id}
              type="button"
              role="tab"
              aria-selected={isActive}
              className={`cv-evidence-step${isActive ? " is-active" : ""}`}
              onClick={() => onSelect(source.id)}
            >
              <span className="cv-evidence-step-num" aria-hidden="true">
                {source.step}
              </span>
              <span className="cv-evidence-step-body">
                <span className="cv-evidence-step-title">{source.title}</span>
                <span className="cv-evidence-step-summary">{source.summary}</span>
              </span>
            </button>
          );
        })}
      </div>

      <div className="cv-evidence-detail" role="tabpanel">
        <h3 className="cv-evidence-detail-title">{active.detailTitle}</h3>
        {active.intro && <p className="cv-evidence-detail-intro">{active.intro}</p>}

        {active.confidenceNote && (
          <p className="cv-evidence-confidence">{active.confidenceNote}</p>
        )}

        {active.cards?.length > 0 && (
          <div className="cv-evidence-card-grid">
            {active.cards.map((card) => (
              <EvidenceCard key={`${active.id}-${card.label}`} card={card} />
            ))}
          </div>
        )}

        {active.highlights?.length > 0 && (
          <ul className="cv-evidence-highlights">
            {active.highlights.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        )}

        <EvidenceRows rows={active.rows} />

        {active.terms?.length > 0 && (
          <dl className="cv-evidence-terms">
            {active.terms.map((group) => (
              <div key={group.label} className="cv-evidence-term-group">
                <dt>{group.label}</dt>
                <dd>{group.items.join(", ")}</dd>
              </div>
            ))}
          </dl>
        )}

        {active.references?.length > 0 && (
          <ol className="cv-evidence-references">
            {active.references.map((ref, idx) => (
              <li key={`${active.id}-ref-${idx}`}>{ref}</li>
            ))}
          </ol>
        )}

        {active.id === "imaging" && (
          <p className="cv-evidence-jump">
            <a href="#chest-xray-viewer" className="cv-btn cv-btn-sm cv-btn-secondary">
              View marked area on X-ray
            </a>
          </p>
        )}

        {active.excerpt && (
          <div className="cv-evidence-excerpt">
            <p className="cv-evidence-excerpt-label">Quoted from the document</p>
            <p className="cv-evidence-excerpt-text">{active.excerpt}</p>
            {active.excerptNote && (
              <p className="cv-evidence-excerpt-note">{active.excerptNote}</p>
            )}
          </div>
        )}

        {fileNames.length > 0 && (
          <p className="cv-evidence-files">
            <span>Source file</span>
            {fileNames.join(", ")}
          </p>
        )}
      </div>
    </div>
  );
}
