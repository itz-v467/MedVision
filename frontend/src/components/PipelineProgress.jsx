/**
 * Pipeline progress from backend (plain language for doctors/patients).
 */
import { PIPELINE_STEPS } from "../utils/plainLanguage";

const STAGE_ORDER = ["ocr", "nlp", "imaging", "correlation", "rag", "summary", "alerts"];

function stepMeta(stepId) {
  return PIPELINE_STEPS[stepId] || { label: stepId, detail: "Processing" };
}

function stepFromBackend(stages, stepId) {
  return stages?.find((s) => s.id === stepId);
}

export function PipelineProgress({
  pipeline,
  loading = false,
  complete = false,
  totalLatencyMs,
}) {
  const backendSteps = pipeline?.steps || [];
  const stages = STAGE_ORDER.filter(
    (id) =>
      backendSteps.some((s) => s.id === id) ||
      (loading && STAGE_ORDER.includes(id))
  );

  const activeIndex = loading ? backendSteps.length : complete ? stages.length : backendSteps.length;

  return (
    <div className="pipeline-container">
      <div className="pipeline-header">
        {complete ? "Your report is ready" : "Processing your document…"}
        {complete && totalLatencyMs != null && (
          <span className="pipeline-total-time">
            Took {(totalLatencyMs / 1000).toFixed(1)} seconds
          </span>
        )}
      </div>

      <div className="pipeline-steps">
        {stages.map((stepId, idx) => {
          const fallback = stepMeta(stepId);
          const backend = stepFromBackend(backendSteps, stepId);
          const label = backend?.label || fallback.label;

          let status = "pending";
          if (backend?.status === "completed" || backend?.status === "skipped") {
            status = backend.status === "skipped" ? "skipped" : "completed";
          } else if (loading && idx === activeIndex) {
            status = "active";
          } else if (complete && backend) {
            status = "completed";
          }

          const summary =
            backend?.summary ||
            (status === "skipped" ? "Not needed for this document" : "");

          return (
            <div key={stepId} className={`pipeline-step ${status}`}>
              <div className="pipeline-indicator">
                {status === "completed" ? "Done" : status === "skipped" ? "—" : idx + 1}
              </div>
              <div className="pipeline-step-body">
                <div className="pipeline-label">{label}</div>
                {status === "active" && loading && (
                  <div className="pipeline-detail">{fallback.detail}</div>
                )}
                {summary && status !== "pending" && (
                  <div className="pipeline-summary">{summary}</div>
                )}
                {status === "active" && loading && !backend && (
                  <div className="pipeline-detail">Please wait…</div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
