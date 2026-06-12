import { UI_LABELS } from "../../utils/plainLanguage";

export function PipelineTraceCard({ pipeline }) {
  const steps = pipeline?.steps || [];
  if (!steps.length) return null;

  const done = steps.filter((s) => s.status === "completed").length;

  return (
    <div className="dash-card dash-pipeline-card">
      <div className="dash-card-head">
        <h2>{UI_LABELS.pipelineTrace}</h2>
        <span className="dash-pill dash-pill-good">{done}/{steps.length} done</span>
      </div>
      <ul className="dash-pipeline-list">
        {steps.map((step) => (
          <li key={step.id} className={`dash-pipeline-step dash-pipeline-${step.status}`}>
            <span className="dash-pipeline-dot" />
            <div>
              <strong>{step.label}</strong>
              {step.summary && <p>{step.summary}</p>}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
