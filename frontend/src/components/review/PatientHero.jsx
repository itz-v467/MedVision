import { Link } from "react-router-dom";
import { AppRoutes } from "../../enums/routes";
import { plainDocType, UI_LABELS } from "../../utils/plainLanguage";

export function PatientHero({ patient, encounter, riskLabel, docType, onDelete }) {
  const initials = patient?.full_name
    ? patient.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()
    : "?";

  const updated = encounter?.created_at
    ? new Date(encounter.created_at).toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      })
    : "—";

  return (
    <header className="dash-hero">
      <div className="dash-hero-left">
        <div className="dash-avatar">{initials}</div>
        <div>
          <p className="dash-hero-greeting">Patient report</p>
          <h1 className="dash-hero-name">{patient?.full_name || "Unknown patient"}</h1>
          <div className="dash-hero-meta">
            <span>ID {patient?.external_id || "—"}</span>
            {patient?.date_of_birth && <span>Age {patient.date_of_birth}</span>}
            {patient?.gender && <span>{patient.gender}</span>}
            <span className="dash-doc-pill">{plainDocType(docType)}</span>
          </div>
        </div>
      </div>
      <div className="dash-hero-right">
        <div className={`dash-risk-chip dash-risk-${riskLabel.toLowerCase()}`}>
          {riskLabel} priority
        </div>
        <p className="dash-hero-date">Updated {updated}</p>
        <div className="dash-hero-actions">
          <Link to={AppRoutes.ENCOUNTERS} className="dash-btn dash-btn-ghost">
            ← All reports
          </Link>
          <button type="button" className="dash-btn dash-btn-danger" onClick={onDelete}>
            {UI_LABELS.deleteRecord}
          </button>
        </div>
      </div>
    </header>
  );
}
