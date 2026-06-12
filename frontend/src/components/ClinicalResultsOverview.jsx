/**
 * Plain-language health report overview for doctors and patients.
 */
import { plainDocType, UI_LABELS } from "../utils/plainLanguage";

export function ClinicalResultsOverview({ detail }) {
  const overview = detail?.results_overview;
  const pipeline = detail?.pipeline;
  const nameValidation = detail?.name_validation;

  if (!overview && !pipeline) return null;

  return (
    <section className="results-overview-panel">
      <div className="results-overview-header">
        <h3>{UI_LABELS.analysisOverview}</h3>
        {overview?.headline && <p className="results-headline">{overview.headline}</p>}
      </div>

      {overview && (
        <div className="results-metrics-grid">
          <MetricCard label="Document type" value={plainDocType(overview.document_type)} />
          <MetricCard
            label="Tests found"
            value={overview.lab_tests_parsed ?? "—"}
          />
          <MetricCard
            label="Needs attention"
            value={overview.lab_abnormal_count ?? 0}
            tone={overview.lab_abnormal_count > 0 ? "warn" : "neutral"}
          />
          <MetricCard
            label="Looks healthy"
            value={overview.lab_normal_count ?? 0}
            tone="good"
          />
          <MetricCard
            label="Report completeness"
            value={overview.panel_coverage_pct != null ? `${overview.panel_coverage_pct}%` : "—"}
          />
          <MetricCard
            label="Reminders"
            value={overview.alert_count ?? 0}
            tone={overview.alert_count > 0 ? "warn" : "neutral"}
          />
        </div>
      )}

      {nameValidation && (
        <div
          className={`identity-verification ${
            nameValidation.matched ? "verified" : nameValidation.warning_only ? "warn" : "mismatch"
          }`}
        >
          <strong>Patient name check</strong>
          <div className="identity-row">
            <span>You entered: {nameValidation.entered_name || "—"}</span>
            <span>On the report: {nameValidation.extracted_name || "Could not read"}</span>
            <span className={`identity-badge ${nameValidation.matched ? "ok" : "bad"}`}>
              {nameValidation.matched
                ? "✓ Matches"
                : nameValidation.skipped
                  ? "? Please verify"
                  : "⚠ Does not match"}
            </span>
          </div>
          {nameValidation.message && <p>{nameValidation.message}</p>}
        </div>
      )}

      {pipeline?.steps?.length > 0 && (
        <div className="pipeline-trace">
          <h4>{UI_LABELS.pipelineTrace}</h4>
          <ul className="pipeline-trace-list">
            {pipeline.steps.map((step) => (
              <li key={step.id}>
                <span className={`trace-status trace-${step.status}`}>
                  {step.status === "completed" ? "done" : step.status}
                </span>
                <span className="trace-label">{step.label}</span>
                <span className="trace-summary">{step.summary}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

function MetricCard({ label, value, tone = "neutral" }) {
  return (
    <div className={`results-metric results-metric-${tone}`}>
      <div className="results-metric-value">{value}</div>
      <div className="results-metric-label">{label}</div>
    </div>
  );
}
