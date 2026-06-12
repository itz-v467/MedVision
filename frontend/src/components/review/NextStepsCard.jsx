import { UI_LABELS } from "../../utils/plainLanguage";

export function NextStepsCard({ precautions = [], headline }) {
  return (
    <div className="dash-card dash-card-dark">
      <h3 className="dash-card-title">{UI_LABELS.recommendedActions}</h3>
      {headline && <p className="dash-card-lead">{headline}</p>}
      {precautions.length > 0 ? (
        <ul className="dash-steps-list">
          {precautions.slice(0, 4).map((p) => (
            <li key={p.test}>
              <span className="dash-step-flag">{p.flag}</span>
              <div>
                <strong>{p.test}</strong>
                <p>{p.precaution}</p>
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p className="dash-card-muted">
          No urgent steps right now. Share this report with your doctor at your next visit.
        </p>
      )}
      <p className="dash-disclaimer">
        This is not a diagnosis. Always discuss results with a qualified healthcare provider.
      </p>
    </div>
  );
}
