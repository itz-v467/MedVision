/** Top-level health KPIs — scan in 3 seconds (doctor + patient). */

export function HealthMetricsRow({ overview, confidence, abnormalCount = 0, normalCount = 0 }) {
  const coverage = overview?.panel_coverage_pct ?? null;

  return (
    <section className="dash-metrics" aria-label="Report overview">
      <MetricBlob
        label="Tests found"
        value={overview?.lab_tests_parsed ?? "—"}
        sub="from your document"
        accent="neutral"
      />
      <MetricBlob
        label="Need attention"
        value={abnormalCount}
        sub="talk to your doctor"
        accent={abnormalCount > 0 ? "warn" : "good"}
        highlight={abnormalCount > 0}
      />
      <MetricBlob
        label="Look healthy"
        value={normalCount}
        sub="within usual range"
        accent="good"
      />
      <MetricBlob
        label="Report read"
        value={coverage != null ? `${coverage}%` : "—"}
        sub="of common blood panel"
        accent="neutral"
      />
      {confidence != null && (
        <div className="dash-metric-blob dash-metric-dark">
          <span className="dash-metric-label">Reading confidence</span>
          <span className="dash-metric-value">{Math.round(confidence * 100)}%</span>
          <span className="dash-metric-sub">how sure we are</span>
          <div className="dash-mini-bar">
            <div className="dash-mini-bar-fill" style={{ width: `${confidence * 100}%` }} />
          </div>
        </div>
      )}
    </section>
  );
}

function MetricBlob({ label, value, sub, accent = "neutral", highlight = false }) {
  return (
    <div className={`dash-metric-blob dash-metric-${accent}${highlight ? " dash-metric-highlight" : ""}`}>
      <span className="dash-metric-label">{label}</span>
      <span className="dash-metric-value">{value}</span>
      <span className="dash-metric-sub">{sub}</span>
    </div>
  );
}
