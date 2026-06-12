import { Link } from "react-router-dom";
import { AppRoutes } from "../../enums/routes";
import { plainStatus } from "../../utils/plainLanguage";

export function ClinicalWorkspace({
  loading,
  encounters = [],
  alerts = [],
  pendingReviews = 0,
  onAcknowledge,
  acknowledgingId,
  canUpload,
}) {
  const activeAlerts = alerts.filter((a) => !a.is_acknowledged);
  const criticalAlerts = activeAlerts.filter((a) => a.priority === "CRITICAL" || a.priority === "HIGH");
  const reviewQueue = encounters.filter(
    (e) => e.status === "PENDING_REVIEW" || e.status === "PROCESSING"
  );
  const recentCases = encounters.slice(0, 8);
  const pendingCount = reviewQueue.length || pendingReviews;

  return (
    <div className="cv-workspace">
      <header className="mv-welcome-header">
        <h1>Workspace</h1>
        <p>Pending reviews, alerts, and recent patient reports.</p>
      </header>

      <div className="cv-metrics" role="list">
        <div className="cv-metric" role="listitem">
          <span className="cv-metric-value">{loading ? "—" : pendingCount}</span>
          <span className="cv-metric-label">Pending review</span>
        </div>
        <div className={`cv-metric${criticalAlerts.length ? " is-alert" : ""}`} role="listitem">
          <span className="cv-metric-value">{loading ? "—" : criticalAlerts.length}</span>
          <span className="cv-metric-label">Urgent alerts</span>
        </div>
        <div className="cv-metric" role="listitem">
          <span className="cv-metric-value">{loading ? "—" : recentCases.length}</span>
          <span className="cv-metric-label">Recent reports</span>
        </div>
      </div>

      <div className="cv-workspace-grid">
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--cv-space-3)" }}>
          <section className="cv-panel cv-panel-pad" aria-labelledby="review-queue-heading">
            <div className="cv-panel-head">
              <h2 id="review-queue-heading">Reports to review</h2>
              <span className="cv-stat-inline">
                {loading ? "Loading…" : `${pendingCount} in queue`}
              </span>
            </div>
            {loading ? (
              <div className="cv-skeleton" style={{ height: 200 }} />
            ) : reviewQueue.length > 0 ? (
              <ul className="cv-case-list">
                {reviewQueue.map((enc) => (
                  <CaseRow key={enc.id} encounter={enc} />
                ))}
              </ul>
            ) : recentCases.length > 0 ? (
              <>
                <p className="mv-empty-hint">No pending reviews. Latest uploads:</p>
                <ul className="cv-case-list">
                  {recentCases.slice(0, 5).map((enc) => (
                    <CaseRow key={enc.id} encounter={enc} />
                  ))}
                </ul>
              </>
            ) : (
              <EmptyState
                message="No reports yet. Upload a lab result or scan to get started."
                action={canUpload ? { label: "Add first case", to: AppRoutes.UPLOAD } : null}
              />
            )}
          </section>

          <section className="cv-panel cv-panel-pad" aria-labelledby="recent-heading">
            <div className="cv-panel-head">
              <h2 id="recent-heading">Recent patients</h2>
              <Link to={AppRoutes.ENCOUNTERS} className="cv-btn cv-btn-ghost cv-btn-sm">
                View all
              </Link>
            </div>
            {loading ? (
              <div className="cv-skeleton" style={{ height: 160 }} />
            ) : recentCases.length > 0 ? (
              <ul className="cv-case-list">
                {recentCases.map((enc) => (
                  <CaseRow key={`recent-${enc.id}`} encounter={enc} compact />
                ))}
              </ul>
            ) : (
              <EmptyState message="Patients will appear here after you upload reports." />
            )}
          </section>
        </div>

        <aside style={{ display: "flex", flexDirection: "column", gap: "var(--cv-space-3)" }}>
          <section className="cv-panel cv-panel-pad" aria-labelledby="alerts-heading">
            <div className="cv-panel-head">
              <h2 id="alerts-heading">Needs attention</h2>
              <span className="cv-stat-inline">{loading ? "—" : criticalAlerts.length}</span>
            </div>
            {loading ? (
              <div className="cv-skeleton" style={{ height: 120 }} />
            ) : criticalAlerts.length > 0 ? (
              criticalAlerts.slice(0, 5).map((alert) => (
                <div
                  key={alert.id}
                  className={`cv-alert-item${alert.priority === "MODERATE" || alert.priority === "MEDIUM" ? " cv-alert-item-moderate" : ""}`}
                >
                  <p className="cv-alert-title">{alert.title}</p>
                  <p className="cv-alert-msg">{alert.message}</p>
                  {onAcknowledge && !alert.is_acknowledged && (
                    <button
                      type="button"
                      className="cv-btn cv-btn-sm cv-btn-secondary"
                      style={{ marginTop: 8 }}
                      onClick={() => onAcknowledge(alert.id)}
                      disabled={acknowledgingId === alert.id}
                    >
                      {acknowledgingId === alert.id ? "Saving…" : "Mark as done"}
                    </button>
                  )}
                </div>
              ))
            ) : (
              <p className="mv-empty-hint">No urgent alerts.</p>
            )}
          </section>

          {canUpload && (
            <section className="cv-panel cv-panel-pad">
              <h2 style={{ margin: "0 0 8px", fontSize: "0.9375rem", fontWeight: 600 }}>New report</h2>
              <p className="mv-empty-hint" style={{ marginBottom: 16 }}>
                Upload a lab report, clinical note, or imaging study for analysis.
              </p>
              <Link to={AppRoutes.UPLOAD} className="cv-btn cv-btn-primary cv-btn-block">
                Upload
              </Link>
            </section>
          )}
        </aside>
      </div>
    </div>
  );
}

function CaseRow({ encounter, compact = false }) {
  const date = new Date(encounter.created_at).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <li className="cv-case-item">
      <div>
        <div className="cv-case-name">{encounter.patient_name || "Unknown patient"}</div>
        <div className="cv-case-meta">
          <span className="mv-case-id">{encounter.patient_external_id || "—"}</span>
          {!compact && ` · ${plainStatus(encounter.status)}`}
          {" · "}{date}
        </div>
      </div>
      <Link to={`${AppRoutes.REVIEW}/${encounter.id}`} className="cv-btn cv-btn-sm cv-btn-secondary">
        Open
      </Link>
    </li>
  );
}

function EmptyState({ message, action }) {
  return (
    <div className="mv-empty-state">
      <p>{message}</p>
      {action && (
        <Link to={action.to} className="cv-btn cv-btn-primary cv-btn-sm">
          {action.label}
        </Link>
      )}
    </div>
  );
}
