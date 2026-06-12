/**
 * Plain-language health advice from lab results.
 */
import { UI_LABELS } from "../utils/plainLanguage";

export function LabPrecautionsPanel({ labAnalysis }) {
  if (!labAnalysis) return null;

  const {
    precautions = [],
    wellness_notes: wellnessNotes = [],
    panel_coverage_pct: coverage,
    missing_core_tests: missing = [],
    disclaimer,
    abnormal_count: abnormalCount = 0,
    normal_count: normalCount = 0,
    llm_extraction: llmExtraction,
  } = labAnalysis;

  if (!precautions.length && !wellnessNotes.length && !missing.length) {
    return null;
  }

  return (
    <div className="lab-precautions-panel">
      <div className="lab-precautions-header">
        <h4>What your results mean</h4>
        <div className="lab-precautions-meta">
          {llmExtraction?.used && (
            <span className="lab-summary-pill lab-summary-llm">
              {llmExtraction.added_count > 0
                ? `AI +${llmExtraction.added_count} tests`
                : "AI-enhanced"}
            </span>
          )}
          {coverage != null && <span>{coverage}% core panel detected</span>}
          <span className="lab-summary-pill lab-summary-normal">{normalCount} good</span>
          {abnormalCount > 0 && (
            <span className="lab-summary-pill lab-summary-abnormal">{abnormalCount} need attention</span>
          )}
        </div>
      </div>

      {precautions.length > 0 && (
        <section className="lab-precautions-section">
          <h5>{UI_LABELS.precautions}</h5>
          <ul className="lab-precautions-list">
            {precautions.map((item) => (
              <li key={item.test} className="lab-precaution-item lab-precaution-abnormal">
                <div className="lab-precaution-title">
                  <span className="lab-status-badge lab-status-abnormal">{item.flag}</span>
                  <strong>{item.test}</strong>
                  <span className="lab-precaution-value">{item.value}</span>
                  <span className="lab-precaution-ref">Ref: {item.reference_range}</span>
                </div>
                <p>{item.precaution}</p>
              </li>
            ))}
          </ul>
        </section>
      )}

      {wellnessNotes.length > 0 && (
        <section className="lab-precautions-section">
          <h5>{UI_LABELS.wellness}</h5>
          <ul className="lab-precautions-list lab-wellness-list">
            {wellnessNotes.slice(0, 12).map((item) => (
              <li key={item.test} className="lab-precaution-item lab-precaution-normal">
                <strong>{item.test}</strong> {item.value} — {item.message}
              </li>
            ))}
            {wellnessNotes.length > 12 && (
              <li className="lab-precaution-more">+{wellnessNotes.length - 12} more normal values</li>
            )}
          </ul>
        </section>
      )}

      {missing.length > 0 && (
        <p className="lab-precautions-missing">
          Not found in report (may be absent or OCR missed): {missing.join(", ")}.
        </p>
      )}

      {disclaimer && <p className="lab-precautions-disclaimer">{disclaimer}</p>}
    </div>
  );
}
