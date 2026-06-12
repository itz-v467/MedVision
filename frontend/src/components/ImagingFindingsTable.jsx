/**
 * Imaging AI findings — detected/abnormal (red) vs not detected/normal (green).
 */
export function ImagingFindingsTable({ findings = {} }) {
  const entries = Object.entries(findings).sort(
    (a, b) => (b[1]?.probability ?? 0) - (a[1]?.probability ?? 0)
  );

  if (!entries.length) {
    return (
      <p style={{ color: "var(--text-muted)", fontStyle: "italic", fontSize: "0.9rem", margin: 0 }}>
        No imaging predictions available.
      </p>
    );
  }

  const abnormalCount = entries.filter(([, d]) => d?.detected).length;

  return (
    <div className="lab-results-panel">
      <div className="lab-results-header">
        <h4>Imaging Finding Specification</h4>
        <div className="lab-results-legend">
          <span className="lab-legend-item lab-legend-normal">● Not detected</span>
          <span className="lab-legend-item lab-legend-abnormal">● Detected</span>
        </div>
      </div>
      <div className="lab-results-summary">
        <span className="lab-summary-pill lab-summary-normal">{entries.length - abnormalCount} normal</span>
        {abnormalCount > 0 && (
          <span className="lab-summary-pill lab-summary-abnormal">{abnormalCount} detected</span>
        )}
      </div>
      <div className="lab-results-table-wrap">
        <table className="lab-results-table">
          <thead>
            <tr>
              <th>Finding</th>
              <th>Probability</th>
              <th>Status</th>
              <th>Clinical detail</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(([name, data]) => {
              const prob = (data?.probability ?? 0) * 100;
              const detected = !!data?.detected;
              const rowClass = detected ? "lab-row-abnormal" : "lab-row-normal";
              const statusClass = detected ? "lab-status-abnormal" : "lab-status-normal";
              const detail = detected
                ? `AI model detected ${name.replace(/_/g, " ")} at ${prob.toFixed(1)}% confidence. Correlate with clinical presentation and imaging review.`
                : `No significant ${name.replace(/_/g, " ")} pattern detected (${prob.toFixed(1)}% probability).`;

              return (
                <tr key={name} className={rowClass}>
                  <td className="lab-cell-name">{name.replace(/_/g, " ")}</td>
                  <td className={detected ? "lab-value-abnormal" : "lab-value-normal"}>
                    {prob.toFixed(1)}%
                  </td>
                  <td>
                    <span className={`lab-status-badge ${statusClass}`}>
                      {detected ? "DETECTED" : "NORMAL"}
                    </span>
                  </td>
                  <td className="lab-cell-detail">{detail}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
