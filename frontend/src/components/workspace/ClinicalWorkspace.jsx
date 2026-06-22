import { Link } from "react-router-dom";
import { AppRoutes } from "../../enums/routes";
import { plainStatus } from "../../utils/plainLanguage";
import { MetricTile } from "../ui/MetricTile";
import { EmptyState } from "../ui/EmptyState";
import { ClinicalCard } from "../ui/ClinicalCard";
import { OperationsAnalytics } from "./OperationsAnalytics";
import { PendingReviewGrid } from "./PendingReviewGrid";

const RECENT_PATIENT_LIMIT = 3;

function isPendingReview(status) {
  return status === "REVIEW_REQUIRED" || status === "PROCESSING";
}

export function ClinicalWorkspace({
  loading,
  encounters = [],
  alerts = [],
  pendingReviews = 0,
  charts,
  chartsLoading,
  onAcknowledge,
  acknowledgingId,
  canUpload,
}) {
  const activeAlerts = alerts.filter((a) => !a.is_acknowledged);
  const criticalAlerts = activeAlerts.filter((a) => a.priority === "CRITICAL" || a.priority === "HIGH");
  const reviewQueue = encounters.filter((e) => isPendingReview(e.status));
  const recentCases = encounters.slice(0, RECENT_PATIENT_LIMIT);
  const pendingCount = reviewQueue.length || pendingReviews;

  return (
    <div className="cv-workspace">
      <div className="cv-metrics-row" role="list">
        <MetricTile label="Pending review" value={loading ? "—" : pendingCount} />
        <MetricTile
          label="Urgent alerts"
          value={loading ? "—" : criticalAlerts.length}
          tone={criticalAlerts.length ? "alert" : "default"}
        />
        <MetricTile label="Recent reports" value={loading ? "—" : Math.min(encounters.length, RECENT_PATIENT_LIMIT)} />
        <MetricTile label="Queue total" value={loading ? "—" : encounters.length} hint="All cases" />
      </div>

      <PendingReviewGrid items={reviewQueue} loading={loading} canUpload={canUpload} />

      <div className="cv-workspace-layout">
        <div className="cv-workspace-main">
          <ClinicalCard
            title="Recent patients"
            action={
              encounters.length > RECENT_PATIENT_LIMIT ? (
                <Link to={AppRoutes.ENCOUNTERS} className="cv-btn cv-btn-ghost cv-btn-sm">
                  View all ({encounters.length})
                </Link>
              ) : (
                <Link to={AppRoutes.ENCOUNTERS} className="cv-btn cv-btn-ghost cv-btn-sm">
                  View all
                </Link>
              )
            }
          >
            {loading ? (
              <div className="cv-skeleton" style={{ height: 120 }} />
            ) : recentCases.length > 0 ? (
              <ul className="cv-case-list">
                {recentCases.map((enc) => (
                  <CaseRow key={`recent-${enc.id}`} encounter={enc} compact />
                ))}
              </ul>
            ) : (
              <EmptyState message="Patients will appear here after you upload reports." />
            )}
          </ClinicalCard>

          <OperationsAnalytics charts={charts} loading={chartsLoading ?? loading} />
        </div>

        <aside className="cv-workspace-aside">
          <ClinicalCard title="Needs attention" action={
            <span className="cv-stat-inline">{loading ? "—" : criticalAlerts.length}</span>
          }>
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
          </ClinicalCard>

          {canUpload && (
            <ClinicalCard title="New report">
              <p className="mv-empty-hint" style={{ marginBottom: 16 }}>
                Upload a lab report, chest X-ray, or describe symptoms with the assistant.
              </p>
              <Link to={AppRoutes.UPLOAD} className="cv-btn cv-btn-primary cv-btn-block">
                Upload
              </Link>
            </ClinicalCard>
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
