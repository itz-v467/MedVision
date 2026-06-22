import { Link } from "react-router-dom";
import { AppRoutes } from "../../enums/routes";
import { plainStatus } from "../../utils/plainLanguage";

function formatRelativeTime(iso) {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  const diffMs = Date.now() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString("en-IN", { day: "2-digit", month: "short" });
}

export function PendingReviewCard({ encounter }) {
  const isProcessing = encounter.status === "PROCESSING";
  const statusLabel = plainStatus(encounter.status);

  return (
    <Link
      to={`${AppRoutes.REVIEW}/${encounter.id}`}
      className={`cv-pending-card${isProcessing ? " is-processing" : ""}`}
    >
      <div className="cv-pending-card-head">
        <span className={`cv-pending-card-status${isProcessing ? " is-processing" : ""}`}>
          {statusLabel}
        </span>
        <span className="cv-pending-card-time">{formatRelativeTime(encounter.created_at)}</span>
      </div>
      <h3 className="cv-pending-card-name">{encounter.patient_name || "Unknown patient"}</h3>
      <p className="cv-pending-card-id">{encounter.patient_external_id || "—"}</p>
      <span className="cv-pending-card-cta">Open review →</span>
    </Link>
  );
}
