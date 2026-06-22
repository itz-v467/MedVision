export function MetricTile({ label, value, tone = "default", hint }) {
  return (
    <div className={`cv-metric-tile is-${tone}`} role="listitem">
      <span className="cv-metric-tile-value">{value}</span>
      <span className="cv-metric-tile-label">{label}</span>
      {hint && <span className="cv-metric-tile-hint">{hint}</span>}
    </div>
  );
}
