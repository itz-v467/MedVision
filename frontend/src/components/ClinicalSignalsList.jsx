/**
 * NLP clinical entities — flagged findings in red, benign categories in green when empty.
 */
const CATEGORY_LABELS = {
  diseases: "Disease indicators",
  symptoms: "Reported symptoms",
  medications: "Medications",
  allergies: "Allergies",
};

export function ClinicalSignalsList({ entities = {} }) {
  if (!entities || typeof entities !== "object" || Array.isArray(entities)) {
    return null;
  }

  const entries = Object.entries(entities).filter(
    ([, values]) => Array.isArray(values) && values.length > 0
  );

  if (!entries.length) {
    return (
      <div className="clinical-signals-panel">
        <h4>Clinical NLP Signals</h4>
        <p className="clinical-signals-none">No disease keywords or clinical entities matched in report text.</p>
      </div>
    );
  }

  return (
    <div className="clinical-signals-panel">
      <h4>Clinical NLP Signals</h4>
      <ul className="clinical-signals-list">
        {entries.map(([key, values]) => (
          <li key={key} className="clinical-signal-item clinical-signal-abnormal">
            <span className="clinical-signal-label">{CATEGORY_LABELS[key] || key}</span>
            <span className="clinical-signal-values">{values.join(", ")}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
