/**
 * Lab results in plain language — healthy (green) vs needs attention (red).
 */
import { UI_LABELS } from "../utils/plainLanguage";

export function LabResultsTable({ biomarkers = [], compact = false, variant = "default" }) {
  if (!biomarkers.length) {
    return null;
  }

  const abnormalCount = biomarkers.filter((b) => b.is_abnormal).length;
  const normalCount = biomarkers.filter((b) => b.status === "normal").length;
  const wrapClass =
    variant === "clinical" ? "cv-lab-panel-inner" : variant === "dashboard" ? "dash-lab-card" : "";

  return (
    <div className={`lab-results-panel ${wrapClass}`.trim()}>
      <div className="lab-results-header">
        <h4>{UI_LABELS.labResults}</h4>
        <div className="lab-results-legend">
          <span className="lab-legend-item lab-legend-normal">● {UI_LABELS.normal}</span>
          <span className="lab-legend-item lab-legend-abnormal">● {UI_LABELS.abnormal}</span>
        </div>
      </div>

      <div className="lab-results-summary">
        <span className="lab-summary-pill lab-summary-normal">{normalCount} {UI_LABELS.normal.toLowerCase()}</span>
        {abnormalCount > 0 && (
          <span className="lab-summary-pill lab-summary-abnormal">{abnormalCount} need attention</span>
        )}
      </div>

      <div className={`lab-results-table-wrap${compact ? " lab-results-compact" : ""}`}>
        <table className="lab-results-table">
          <thead>
            <tr>
              <th>Test</th>
              <th>Your result</th>
              <th>{UI_LABELS.referenceRange}</th>
              <th>Status</th>
              {!compact && <th>What it means</th>}
            </tr>
          </thead>
          <tbody>
            {biomarkers.map((item) => (
              <LabResultRow key={item.name} item={item} compact={compact} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function LabResultRow({ item, compact }) {
  const isAbnormal = item.is_abnormal || item.status === "abnormal";
  const rowClass = isAbnormal ? "lab-row-abnormal" : item.status === "normal" ? "lab-row-normal" : "lab-row-unknown";
  const statusClass = isAbnormal ? "lab-status-abnormal" : item.status === "normal" ? "lab-status-normal" : "lab-status-unknown";
  const statusLabel = isAbnormal
    ? item.flag === "HIGH"
      ? "HIGH"
      : item.flag === "LOW"
        ? "LOW"
        : "CHECK"
    : item.status === "normal"
      ? "OK"
      : "—";
  const valueText = item.display_value || `${item.value}${item.unit ? ` ${item.unit}` : ""}`;
  const rawNote =
    item.raw_value != null &&
    item.raw_value !== item.value &&
    `${item.raw_value}${item.raw_unit ? ` ${item.raw_unit}` : ""}`;
  const detail = [
    item.precaution || item.interpretation || item.clinical_note || "",
    rawNote ? `OCR raw: ${rawNote}` : "",
  ]
    .filter(Boolean)
    .join(" · ") || "—";

  return (
    <tr className={rowClass}>
      <td className="lab-cell-name">{item.name}</td>
      <td className={`lab-cell-value ${isAbnormal ? "lab-value-abnormal" : "lab-value-normal"}`}>
        {valueText}
      </td>
      <td className="lab-cell-ref">{item.reference_range || "—"}</td>
      <td>
        <span className={`lab-status-badge ${statusClass}`}>{statusLabel}</span>
      </td>
      {!compact && <td className="lab-cell-detail">{detail}</td>}
    </tr>
  );
}
