import { ConsultDoctorCard } from "./ConsultDoctorCard";

export function CaseMetricsRail({
  confidence,
  docType,
  alerts = [],
  consultRecommendation,
  consultConfig,
  consultRequest,
  onRequestConsult,
  requestingConsult,
  onAcknowledge,
  acknowledgingId,
}) {
  const pct = confidence != null ? Math.round(confidence * 100) : null;
  const caption =
    docType === "xray"
      ? "ChestNet imaging signals"
      : "OCR, NLP, document quality";
  const topAlerts = alerts.filter((a) => !a.is_acknowledged).slice(0, 3);

  return (
    <aside className="cv-case-rail" aria-label="Case metrics">
      {pct != null && (
        <div className="cv-ui-card is-padded cv-confidence-card">
          <p className="cv-confidence-label">Evidence strength</p>
          <div className="cv-confidence-value">{pct}%</div>
          <div className="cv-confidence-bar">
            <div className="cv-confidence-bar-fill" style={{ width: `${pct}%` }} />
          </div>
          <p className="cv-metric-tile-hint">{caption}</p>
        </div>
      )}

      {topAlerts.length > 0 && (
        <div className="cv-ui-card is-padded">
          <h3 className="cv-ui-card-title">Alerts</h3>
          {topAlerts.map((alert) => (
            <div key={alert.id} className="cv-alert-item" style={{ marginBottom: 8 }}>
              <p className="cv-alert-title">[{alert.priority}] {alert.title}</p>
              <p className="cv-alert-msg">{alert.message}</p>
              {onAcknowledge && (
                <button
                  type="button"
                  className="cv-btn cv-btn-sm cv-btn-secondary"
                  onClick={() => onAcknowledge(alert.id)}
                  disabled={acknowledgingId === alert.id}
                >
                  {acknowledgingId === alert.id ? "Saving…" : "Acknowledge"}
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      <ConsultDoctorCard
        consultRecommendation={consultRecommendation}
        consultConfig={consultConfig}
        existingRequest={consultRequest}
        onRequestConsult={onRequestConsult}
        requesting={requestingConsult}
      />
    </aside>
  );
}
